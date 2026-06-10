"""
Embedding Service - 文档向量化（ONNX Runtime 版本）

与原 sentence-transformers 版本接口完全一致：
- embed_texts(texts) -> List[List[float]]
- vectorize_chunks(chunks) -> List[ChunkWithEmbedding]]
- store_chunks / search / delete_by_doc_id / get_stats

底层用 onnxruntime + tokenizers，避免引入 torch / transformers / sentence-transformers
（节省 1.5GB+ 镜像体积和 5-30s 冷启动时间）。

模型：`all-MiniLM-L6-v2` 的 ONNX 导出版本（Xenova/all-MiniLM-L6-v2）
  - 输入：input_ids, attention_mask, token_type_ids
  - 输出：last_hidden_state (shape: [batch, seq_len, 384])
  - 池化：mean pooling + L2 normalize（sentence-transformers 默认策略）
"""
import logging
import os
import threading
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import numpy as np
import chromadb
from chromadb.config import Settings

# 延迟导入 onnxruntime / tokenizers，让 collect 错误信息更清晰
onnxruntime = None
Tokenizer = None

from app.rag_engine.document_parser import DocumentChunk, document_parser

logger = logging.getLogger(__name__)

# ============ 配置 ============
CHROMA_PATH = os.getenv("CHROMA_PATH", "./data/chroma")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "knowledge_base")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
# ONNX 模型文件路径；Docker 镜像里放在 /app/models/all-MiniLM-L6-v2/
ONNX_MODEL_DIR = os.getenv(
    "ONNX_MODEL_DIR",
    os.path.join(os.path.dirname(__file__), "..", "..", "models", "all-MiniLM-L6-v2"),
)
# Xenova 仓库目录结构：<root>/onnx/model.onnx、<root>/tokenizer.json
ONNX_MODEL_FILE = os.path.join(ONNX_MODEL_DIR, "onnx", "model.onnx")
ONNX_TOKENIZER_FILE = os.path.join(ONNX_MODEL_DIR, "tokenizer.json")

# 序列长度：与 sentence-transformers/all-MiniLM-L6-v2 默认一致
MAX_SEQ_LENGTH = 256  # MiniLM 实际只用 128/256，256 更稳

# ONNX 线程数：K8s 限制 CPU 时，设置为 1 避免超用
ONNX_THREADS = int(os.getenv("ONNX_THREADS", "1"))


@dataclass
class ChunkWithEmbedding:
    """带向量的文档块"""
    chunk: DocumentChunk
    embedding: List[float]


class EmbeddingService:
    """向量化服务（ONNX Runtime 后端）"""

    def __init__(self):
        self.ort_session = None
        self.tokenizer = None
        self.chroma_client = None
        self.collection = None
        # 推理锁：onnxruntime 的 InferenceSession 默认是 thread-safe 的，
        # 但配 SessionOptions.inter_op_num_threads=1 后可避免多线程抖动
        self._infer_lock = threading.Lock()
        self._initialize()

    def _initialize(self):
        """初始化 ONNX 模型、tokenizer 和 Chroma"""
        global onnxruntime, Tokenizer

        try:
            # ---- 1. 加载 ONNX Runtime ----
            import onnxruntime as _ort  # type: ignore
            onnxruntime = _ort

            if not os.path.isfile(ONNX_MODEL_FILE):
                raise FileNotFoundError(
                    f"ONNX model not found at {ONNX_MODEL_FILE}. "
                    f"Please download it (see scripts/download_onnx_model.sh)."
                )

            sess_options = _ort.SessionOptions()
            sess_options.inter_op_num_threads = ONNX_THREADS
            sess_options.intra_op_num_threads = ONNX_THREADS
            sess_options.graph_optimization_level = _ort.GraphOptimizationLevel.ORT_ENABLE_ALL

            # 优先 CPU provider；如有 GPU 需求可加 "CUDAExecutionProvider"
            providers = ["CPUExecutionProvider"]
            self.ort_session = _ort.InferenceSession(
                ONNX_MODEL_FILE, sess_options=sess_options, providers=providers
            )
            logger.info(
                "ONNX embedding model loaded: %s (providers=%s, threads=%d)",
                ONNX_MODEL_FILE, providers, ONNX_THREADS,
            )

            # ---- 2. 加载 tokenizer ----
            from tokenizers import Tokenizer as _Tok  # type: ignore
            Tokenizer = _Tok

            self.tokenizer = _Tok.from_file(ONNX_TOKENIZER_FILE)
            self.tokenizer.enable_padding(pad_id=0, pad_token="[PAD]", length=MAX_SEQ_LENGTH)
            self.tokenizer.enable_truncation(max_length=MAX_SEQ_LENGTH)
            logger.info("Tokenizer loaded: %s", ONNX_TOKENIZER_FILE)

            # ---- 3. 初始化 Chroma ----
            os.makedirs(CHROMA_PATH, exist_ok=True)
            self.chroma_client = chromadb.PersistentClient(
                path=CHROMA_PATH,
                settings=Settings(anonymized_telemetry=False),
            )
            self.collection = self.chroma_client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"description": "Knowledge base vector store"},
            )
            logger.info("Chroma collection initialized: %s", COLLECTION_NAME)

        except Exception as e:
            logger.error(f"Failed to initialize embedding service: {e}", exc_info=True)
            raise

    # ============ 核心：文本 → 向量 ============

    def _tokenize(self, texts: List[str]):
        """调用 HF tokenizers 把文本切成模型输入"""
        encoded = self.tokenizer.encode_batch(texts)
        input_ids = np.array([e.ids for e in encoded], dtype=np.int64)
        attention_mask = np.array([e.attention_mask for e in encoded], dtype=np.int64)
        token_type_ids = np.array([e.type_ids for e in encoded], dtype=np.int64)
        return input_ids, attention_mask, token_type_ids

    @staticmethod
    def _mean_pool(last_hidden_state: np.ndarray, attention_mask: np.ndarray) -> np.ndarray:
        """
        Mean pooling：把 [batch, seq_len, 384] 压成 [batch, 384]
        对每个 token 的向量按 attention_mask 加权平均
        """
        mask = np.expand_dims(attention_mask, -1).astype(np.float32)
        summed = np.sum(last_hidden_state * mask, axis=1)
        counts = np.clip(mask.sum(axis=1), a_min=1e-9, a_max=None)
        return summed / counts

    @staticmethod
    def _l2_normalize(vectors: np.ndarray) -> np.ndarray:
        """L2 归一化，让余弦相似度 = 点积"""
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.clip(norms, a_min=1e-9, a_max=None)
        return vectors / norms

    def _encode_batch(self, texts: List[str]) -> np.ndarray:
        """批量编码：texts -> [batch, 384] 的归一化向量"""
        with self._infer_lock:
            input_ids, attention_mask, token_type_ids = self._tokenize(texts)
            outputs = self.ort_session.run(
                None,
                {
                    "input_ids": input_ids,
                    "attention_mask": attention_mask,
                    "token_type_ids": token_type_ids,
                },
            )
        last_hidden = outputs[0]  # [batch, seq_len, 384]
        pooled = self._mean_pool(last_hidden, attention_mask)
        return self._l2_normalize(pooled)

    # ============ 公共 API（与原版签名一致）============

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """生成文本向量"""
        if not self.ort_session:
            raise RuntimeError("Embedding model not initialized")
        if not texts:
            return []
        vectors = self._encode_batch(texts)
        return vectors.astype(np.float32).tolist()

    def vectorize_chunks(self, chunks: List[DocumentChunk]) -> List[ChunkWithEmbedding]:
        """向量化文档块（自动按 batch_size 切批，避免 OOM）"""
        if not chunks:
            return []
        BATCH_SIZE = 32
        result: List[ChunkWithEmbedding] = []
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i : i + BATCH_SIZE]
            texts = [c.content for c in batch]
            vectors = self._encode_batch(texts).astype(np.float32).tolist()
            for chunk, vec in zip(batch, vectors):
                result.append(ChunkWithEmbedding(chunk=chunk, embedding=vec))
        return result

    def store_chunks(self, chunks: List[ChunkWithEmbedding]) -> int:
        """存储文档块到向量库"""
        if not chunks:
            return 0
        ids, embeddings, documents, metadatas = [], [], [], []
        for cwe in chunks:
            chunk = cwe.chunk
            ids.append(f"doc_{chunk.doc_id}_chunk_{chunk.chunk_index}")
            embeddings.append(cwe.embedding)
            documents.append(chunk.content)
            metadatas.append({
                "doc_id": chunk.doc_id,
                "title": chunk.title,
                "doc_type": chunk.doc_type,
                "project_name": chunk.project_name,
                "service_name": chunk.service_name,
                "heading_path": chunk.heading_path,
                "chunk_index": chunk.chunk_index,
            })
        self.collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
        logger.info(f"Stored {len(chunks)} chunks to vector store")
        return len(chunks)

    def search(self, query: str, top_k: int = 5,
               project_name: str = None,
               service_name: str = None,
               doc_type: str = None) -> List[Dict[str, Any]]:
        """向量检索"""
        query_vec = self._encode_batch([query])[0].astype(np.float32).tolist()
        where = {}
        if project_name:
            where["project_name"] = project_name
        if service_name:
            where["service_name"] = service_name
        if doc_type:
            where["doc_type"] = doc_type
        kwargs = dict(query_embeddings=[query_vec], n_results=top_k)
        if where:
            kwargs["where"] = where
        results = self.collection.query(**kwargs)

        formatted: List[Dict[str, Any]] = []
        if results and results.get("ids") and len(results["ids"]) > 0:
            for i in range(len(results["ids"][0])):
                dist = results.get("distances", [[1]])[0][i] if results.get("distances") else 0
                formatted.append({
                    "chunk_id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": dist,
                    "similarity": 1 - dist,
                })
        return formatted

    def delete_by_doc_id(self, doc_id: int) -> int:
        """删除指定 doc 的所有 chunks"""
        results = self.collection.get(where={"doc_id": doc_id})
        if not results or not results.get("ids"):
            return 0
        ids = results["ids"]
        self.collection.delete(ids=ids)
        logger.info(f"Deleted {len(ids)} chunks for doc_id={doc_id}")
        return len(ids)

    def get_stats(self) -> Dict[str, Any]:
        """统计信息"""
        return {
            "total_chunks": self.collection.count(),
            "collection_name": COLLECTION_NAME,
            "embedding_model": EMBEDDING_MODEL,
            "embedding_backend": "onnxruntime",
            "onnx_model_path": ONNX_MODEL_FILE,
        }


# 全局服务实例（延迟初始化）
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """获取向量化服务实例"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service

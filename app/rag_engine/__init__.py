"""rag-engine - 独立的 RAG 服务包.

负责：
- 文档解析（md/docx/pdf）
- 向量化（sentence-transformers）
- 向量存储与检索（Chroma，可替换为 Qdrant/PGVector）
- 暴露 gRPC RagService

不在这里做 LLM 生成。检索结果由 agent-orchestrator 取走后自己生成。
"""

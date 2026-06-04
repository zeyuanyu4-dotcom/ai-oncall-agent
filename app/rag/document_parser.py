"""
Document Parser - 多格式文档解析
支持: Markdown, Word (.docx), PDF
"""
import re
import io
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class DocumentChunk:
    """文档块"""
    content: str                    # 块内容
    doc_id: int                      # 文档ID
    title: str                       # 文档标题
    doc_type: str                    # 文档类型
    project_name: str                # 项目名称
    service_name: str                # 服务名称
    heading_path: str                # 章节路径，如 "1.连接问题/1.1连接超时"
    chunk_index: int                 # 块序号


class BaseParser(ABC):
    """文档解析器基类"""

    @abstractmethod
    def parse(self, file_content: bytes, filename: str) -> List[DocumentChunk]:
        """解析文档，返回文档块列表"""
        pass

    @abstractmethod
    def extract_text(self, file_content: bytes) -> str:
        """提取纯文本内容"""
        pass


class MarkdownParser(BaseParser):
    """Markdown 文档解析器"""

    def extract_text(self, file_content: bytes) -> str:
        return file_content.decode('utf-8')

    def parse(self, file_content: bytes, filename: str) -> List[DocumentChunk]:
        """解析 Markdown 文档"""
        content = self.extract_text(file_content)
        chunks = self._split_by_headings(content, filename)
        return chunks

    def _split_by_headings(self, content: str, filename: str) -> List[DocumentChunk]:
        """按标题层级切分"""
        lines = content.split('\n')
        chunks = []
        current_heading = ""
        current_path = ""
        current_content = []
        chunk_index = 0

        # 标题模式：# 开头的行
        heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$')

        for line in lines:
            heading_match = heading_match = heading_pattern.match(line.strip())
            if heading_match:
                # 保存之前的块
                if current_content:
                    text = '\n'.join(current_content).strip()
                    if len(text) >= 50:  # 过滤短内容
                        chunks.append(DocumentChunk(
                            content=text,
                            doc_id=0,  # 稍后填充
                            title=filename.replace('.md', ''),
                            doc_type="markdown",
                            project_name="",
                            service_name="",
                            heading_path=current_path,
                            chunk_index=chunk_index
                        ))
                        chunk_index += 1

                # 开始新块
                level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()

                # 构建路径
                if level == 1:
                    current_path = heading_text
                else:
                    current_path = current_path + "/" + heading_text if current_path else heading_text

                current_content = [line]
            else:
                current_content.append(line)

        # 保存最后一块
        if current_content:
            text = '\n'.join(current_content).strip()
            if len(text) >= 50:
                chunks.append(DocumentChunk(
                    content=text,
                    doc_id=0,
                    title=filename.replace('.md', ''),
                    doc_type="markdown",
                    project_name="",
                    service_name="",
                    heading_path=current_path,
                    chunk_index=chunk_index
                ))

        return chunks


class WordParser(BaseParser):
    """Word (.docx) 文档解析器"""

    def extract_text(self, file_content: bytes) -> str:
        try:
            from docx import Document
            doc = Document(io.BytesIO(file_content))
            paragraphs = []
            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text)
            return '\n'.join(paragraphs)
        except Exception as e:
            raise ValueError(f"Failed to parse Word document: {e}")

    def parse(self, file_content: bytes, filename: str) -> List[DocumentChunk]:
        """解析 Word 文档"""
        try:
            from docx import Document
            doc = Document(io.BytesIO(file_content))

            chunks = []
            current_heading = ""
            current_path = ""
            current_content = []
            chunk_index = 0

            for para in doc.paragraphs:
                text = para.text.strip()
                if not text:
                    continue

                # 检测标题（根据样式）
                if para.style.name.startswith('Heading'):
                    level = int(para.style.name.replace('Heading ', ''))
                    heading_text = text

                    # 保存之前的块
                    if current_content:
                        content_text = '\n'.join(current_content).strip()
                        if len(content_text) >= 50:
                            chunks.append(DocumentChunk(
                                content=content_text,
                                doc_id=0,
                                title=filename.replace('.docx', '').replace('.doc', ''),
                                doc_type="word",
                                project_name="",
                                service_name="",
                                heading_path=current_path,
                                chunk_index=chunk_index
                            ))
                            chunk_index += 1

                    # 更新路径
                    if level == 1:
                        current_path = heading_text
                    else:
                        current_path = current_path + "/" + heading_text if current_path else heading_text

                    current_content = [text]
                else:
                    current_content.append(text)

            # 保存最后一块
            if current_content:
                text = '\n'.join(current_content).strip()
                if len(text) >= 50:
                    chunks.append(DocumentChunk(
                        content=text,
                        doc_id=0,
                        title=filename.replace('.docx', '').replace('.doc', ''),
                        doc_type="word",
                        project_name="",
                        service_name="",
                        heading_path=current_path,
                        chunk_index=chunk_index
                    ))

            return chunks

        except Exception as e:
            raise ValueError(f"Failed to parse Word document: {e}")


class PDFParser(BaseParser):
    """PDF 文档解析器"""

    def extract_text(self, file_content: bytes) -> str:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(file_content))
            text_parts = []

            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            return '\n'.join(text_parts)
        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {e}")

    def parse(self, file_content: bytes, filename: str) -> List[DocumentChunk]:
        """解析 PDF 文档"""
        content = self.extract_text(file_content)

        # PDF 按页面切分（简单策略）
        # 更好的方案是按段落切分
        chunks = []
        chunk_size = 2000  # 字符数
        chunk_overlap = 200  # 重叠字符

        pages = content.split('\n\n')
        current_content = []
        current_size = 0
        chunk_index = 0

        for page in pages:
            if current_size + len(page) > chunk_size and current_content:
                text = '\n'.join(current_content)
                chunks.append(DocumentChunk(
                    content=text,
                    doc_id=0,
                    title=filename.replace('.pdf', ''),
                    doc_type="pdf",
                    project_name="",
                    service_name="",
                    heading_path=f"第{chunk_index + 1}部分",
                    chunk_index=chunk_index
                ))
                chunk_index += 1

                # 保留最后一个用于重叠
                overlap_size = len(current_content[-1]) if current_content else 0
                if overlap_size > 0 and overlap_size < chunk_overlap:
                    current_content = [current_content[-1]]
                    current_size = overlap_size
                else:
                    current_content = []
                    current_size = 0

            current_content.append(page)
            current_size += len(page) + 2

        # 保存最后一块
        if current_content:
            text = '\n'.join(current_content).strip()
            if len(text) >= 50:
                chunks.append(DocumentChunk(
                    content=text,
                    doc_id=0,
                    title=filename.replace('.pdf', ''),
                    doc_type="pdf",
                    project_name="",
                    service_name="",
                    heading_path=f"第{chunk_index}部分",
                    chunk_index=chunk_index
                ))

        return chunks


class DocumentParser:
    """文档解析器（根据格式选择解析器）"""

    def __init__(self):
        self.parsers = {
            'markdown': MarkdownParser(),
            'md': MarkdownParser(),
            'word': WordParser(),
            'docx': WordParser(),
            'doc': WordParser(),
            'pdf': PDFParser(),
        }

    def parse(self, file_content: bytes, filename: str, doc_id: int = 0,
              title: str = "", doc_type: str = "", project_name: str = "",
              service_name: str = "") -> List[DocumentChunk]:
        """
        解析文档

        Args:
            file_content: 文件内容（字节）
            filename: 文件名
            doc_id: 文档ID
            title: 文档标题
            doc_type: 文档类型
            project_name: 项目名称
            service_name: 服务名称

        Returns:
            List[DocumentChunk]: 文档块列表
        """
        # 根据扩展名选择解析器
        ext = filename.lower().split('.')[-1]
        parser = self.parsers.get(ext)

        if not parser:
            raise ValueError(f"Unsupported file format: {ext}")

        # 解析文档
        chunks = parser.parse(file_content, filename)

        # 填充元数据
        for chunk in chunks:
            chunk.doc_id = doc_id
            chunk.title = title or chunk.title
            chunk.doc_type = doc_type or chunk.doc_type
            chunk.project_name = project_name
            chunk.service_name = service_name

        return chunks

    def extract_text(self, file_content: bytes, filename: str) -> str:
        """提取纯文本"""
        ext = filename.lower().split('.')[-1]
        parser = self.parsers.get(ext)

        if not parser:
            raise ValueError(f"Unsupported file format: {ext}")

        return parser.extract_text(file_content)


# 全局解析器实例
document_parser = DocumentParser()

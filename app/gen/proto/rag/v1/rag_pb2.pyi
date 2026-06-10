from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class VectorizeTextRequest(_message.Message):
    __slots__ = ("doc_id", "title", "doc_type", "project_name", "service_name", "heading_path", "content")
    DOC_ID_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    DOC_TYPE_FIELD_NUMBER: _ClassVar[int]
    PROJECT_NAME_FIELD_NUMBER: _ClassVar[int]
    SERVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    HEADING_PATH_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    doc_id: int
    title: str
    doc_type: str
    project_name: str
    service_name: str
    heading_path: str
    content: str
    def __init__(self, doc_id: _Optional[int] = ..., title: _Optional[str] = ..., doc_type: _Optional[str] = ..., project_name: _Optional[str] = ..., service_name: _Optional[str] = ..., heading_path: _Optional[str] = ..., content: _Optional[str] = ...) -> None: ...

class VectorizeTextResponse(_message.Message):
    __slots__ = ("stored_chunks", "deleted_chunks")
    STORED_CHUNKS_FIELD_NUMBER: _ClassVar[int]
    DELETED_CHUNKS_FIELD_NUMBER: _ClassVar[int]
    stored_chunks: int
    deleted_chunks: int
    def __init__(self, stored_chunks: _Optional[int] = ..., deleted_chunks: _Optional[int] = ...) -> None: ...

class VectorizeDocumentRequest(_message.Message):
    __slots__ = ("doc_id", "title", "doc_type", "project_name", "service_name", "filename", "content")
    DOC_ID_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    DOC_TYPE_FIELD_NUMBER: _ClassVar[int]
    PROJECT_NAME_FIELD_NUMBER: _ClassVar[int]
    SERVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    FILENAME_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    doc_id: int
    title: str
    doc_type: str
    project_name: str
    service_name: str
    filename: str
    content: bytes
    def __init__(self, doc_id: _Optional[int] = ..., title: _Optional[str] = ..., doc_type: _Optional[str] = ..., project_name: _Optional[str] = ..., service_name: _Optional[str] = ..., filename: _Optional[str] = ..., content: _Optional[bytes] = ...) -> None: ...

class VectorizeDocumentResponse(_message.Message):
    __slots__ = ("stored_chunks", "deleted_chunks")
    STORED_CHUNKS_FIELD_NUMBER: _ClassVar[int]
    DELETED_CHUNKS_FIELD_NUMBER: _ClassVar[int]
    stored_chunks: int
    deleted_chunks: int
    def __init__(self, stored_chunks: _Optional[int] = ..., deleted_chunks: _Optional[int] = ...) -> None: ...

class DeleteByDocIdRequest(_message.Message):
    __slots__ = ("doc_id",)
    DOC_ID_FIELD_NUMBER: _ClassVar[int]
    doc_id: int
    def __init__(self, doc_id: _Optional[int] = ...) -> None: ...

class DeleteByDocIdResponse(_message.Message):
    __slots__ = ("deleted_chunks",)
    DELETED_CHUNKS_FIELD_NUMBER: _ClassVar[int]
    deleted_chunks: int
    def __init__(self, deleted_chunks: _Optional[int] = ...) -> None: ...

class SearchRequest(_message.Message):
    __slots__ = ("query", "top_k", "project_name", "service_name", "doc_type")
    QUERY_FIELD_NUMBER: _ClassVar[int]
    TOP_K_FIELD_NUMBER: _ClassVar[int]
    PROJECT_NAME_FIELD_NUMBER: _ClassVar[int]
    SERVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    DOC_TYPE_FIELD_NUMBER: _ClassVar[int]
    query: str
    top_k: int
    project_name: str
    service_name: str
    doc_type: str
    def __init__(self, query: _Optional[str] = ..., top_k: _Optional[int] = ..., project_name: _Optional[str] = ..., service_name: _Optional[str] = ..., doc_type: _Optional[str] = ...) -> None: ...

class SearchResponse(_message.Message):
    __slots__ = ("hits",)
    HITS_FIELD_NUMBER: _ClassVar[int]
    hits: _containers.RepeatedCompositeFieldContainer[SearchHit]
    def __init__(self, hits: _Optional[_Iterable[_Union[SearchHit, _Mapping]]] = ...) -> None: ...

class SearchHit(_message.Message):
    __slots__ = ("chunk_id", "content", "metadata", "distance", "similarity")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    CHUNK_ID_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_FIELD_NUMBER: _ClassVar[int]
    SIMILARITY_FIELD_NUMBER: _ClassVar[int]
    chunk_id: str
    content: str
    metadata: _containers.ScalarMap[str, str]
    distance: float
    similarity: float
    def __init__(self, chunk_id: _Optional[str] = ..., content: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ..., distance: _Optional[float] = ..., similarity: _Optional[float] = ...) -> None: ...

class GetStatsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetStatsResponse(_message.Message):
    __slots__ = ("total_chunks", "collection_name", "embedding_model")
    TOTAL_CHUNKS_FIELD_NUMBER: _ClassVar[int]
    COLLECTION_NAME_FIELD_NUMBER: _ClassVar[int]
    EMBEDDING_MODEL_FIELD_NUMBER: _ClassVar[int]
    total_chunks: int
    collection_name: str
    embedding_model: str
    def __init__(self, total_chunks: _Optional[int] = ..., collection_name: _Optional[str] = ..., embedding_model: _Optional[str] = ...) -> None: ...

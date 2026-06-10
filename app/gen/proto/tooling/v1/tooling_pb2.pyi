from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GetServiceRequest(_message.Message):
    __slots__ = ("service_id",)
    SERVICE_ID_FIELD_NUMBER: _ClassVar[int]
    service_id: int
    def __init__(self, service_id: _Optional[int] = ...) -> None: ...

class GetServiceResponse(_message.Message):
    __slots__ = ("service",)
    SERVICE_FIELD_NUMBER: _ClassVar[int]
    service: Service
    def __init__(self, service: _Optional[_Union[Service, _Mapping]] = ...) -> None: ...

class ListServicesByProjectRequest(_message.Message):
    __slots__ = ("project_id",)
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    project_id: int
    def __init__(self, project_id: _Optional[int] = ...) -> None: ...

class ListServicesByProjectResponse(_message.Message):
    __slots__ = ("services",)
    SERVICES_FIELD_NUMBER: _ClassVar[int]
    services: _containers.RepeatedCompositeFieldContainer[Service]
    def __init__(self, services: _Optional[_Iterable[_Union[Service, _Mapping]]] = ...) -> None: ...

class Service(_message.Message):
    __slots__ = ("id", "project_id", "name", "language", "owner", "status")
    ID_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    OWNER_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    id: int
    project_id: int
    name: str
    language: str
    owner: str
    status: str
    def __init__(self, id: _Optional[int] = ..., project_id: _Optional[int] = ..., name: _Optional[str] = ..., language: _Optional[str] = ..., owner: _Optional[str] = ..., status: _Optional[str] = ...) -> None: ...

class SearchHistoryIssuesRequest(_message.Message):
    __slots__ = ("keyword", "project_id", "issue_type", "page", "page_size")
    KEYWORD_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    ISSUE_TYPE_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    keyword: str
    project_id: int
    issue_type: str
    page: int
    page_size: int
    def __init__(self, keyword: _Optional[str] = ..., project_id: _Optional[int] = ..., issue_type: _Optional[str] = ..., page: _Optional[int] = ..., page_size: _Optional[int] = ...) -> None: ...

class SearchHistoryIssuesResponse(_message.Message):
    __slots__ = ("items", "total")
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[Issue]
    total: int
    def __init__(self, items: _Optional[_Iterable[_Union[Issue, _Mapping]]] = ..., total: _Optional[int] = ...) -> None: ...

class Issue(_message.Message):
    __slots__ = ("id", "issue_no", "title", "status", "priority", "issue_type")
    ID_FIELD_NUMBER: _ClassVar[int]
    ISSUE_NO_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    ISSUE_TYPE_FIELD_NUMBER: _ClassVar[int]
    id: int
    issue_no: str
    title: str
    status: str
    priority: str
    issue_type: str
    def __init__(self, id: _Optional[int] = ..., issue_no: _Optional[str] = ..., title: _Optional[str] = ..., status: _Optional[str] = ..., priority: _Optional[str] = ..., issue_type: _Optional[str] = ...) -> None: ...

class SearchKnowledgeDocsRequest(_message.Message):
    __slots__ = ("keyword", "doc_type", "project_id", "page", "page_size")
    KEYWORD_FIELD_NUMBER: _ClassVar[int]
    DOC_TYPE_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    keyword: str
    doc_type: str
    project_id: int
    page: int
    page_size: int
    def __init__(self, keyword: _Optional[str] = ..., doc_type: _Optional[str] = ..., project_id: _Optional[int] = ..., page: _Optional[int] = ..., page_size: _Optional[int] = ...) -> None: ...

class SearchKnowledgeDocsResponse(_message.Message):
    __slots__ = ("items", "total")
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[KnowledgeDoc]
    total: int
    def __init__(self, items: _Optional[_Iterable[_Union[KnowledgeDoc, _Mapping]]] = ..., total: _Optional[int] = ...) -> None: ...

class GetKnowledgeDocRequest(_message.Message):
    __slots__ = ("doc_id",)
    DOC_ID_FIELD_NUMBER: _ClassVar[int]
    doc_id: int
    def __init__(self, doc_id: _Optional[int] = ...) -> None: ...

class GetKnowledgeDocResponse(_message.Message):
    __slots__ = ("doc",)
    DOC_FIELD_NUMBER: _ClassVar[int]
    doc: KnowledgeDoc
    def __init__(self, doc: _Optional[_Union[KnowledgeDoc, _Mapping]] = ...) -> None: ...

class KnowledgeDoc(_message.Message):
    __slots__ = ("id", "title", "doc_type", "content")
    ID_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    DOC_TYPE_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    id: int
    title: str
    doc_type: str
    content: str
    def __init__(self, id: _Optional[int] = ..., title: _Optional[str] = ..., doc_type: _Optional[str] = ..., content: _Optional[str] = ...) -> None: ...

class GetLogsByTraceIDRequest(_message.Message):
    __slots__ = ("trace_id",)
    TRACE_ID_FIELD_NUMBER: _ClassVar[int]
    trace_id: str
    def __init__(self, trace_id: _Optional[str] = ...) -> None: ...

class GetLogsByTraceIDResponse(_message.Message):
    __slots__ = ("entries",)
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    entries: _containers.RepeatedCompositeFieldContainer[LogEntry]
    def __init__(self, entries: _Optional[_Iterable[_Union[LogEntry, _Mapping]]] = ...) -> None: ...

class GetServiceLogsRequest(_message.Message):
    __slots__ = ("service_id", "limit")
    SERVICE_ID_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    service_id: int
    limit: int
    def __init__(self, service_id: _Optional[int] = ..., limit: _Optional[int] = ...) -> None: ...

class GetServiceLogsResponse(_message.Message):
    __slots__ = ("entries",)
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    entries: _containers.RepeatedCompositeFieldContainer[LogEntry]
    def __init__(self, entries: _Optional[_Iterable[_Union[LogEntry, _Mapping]]] = ...) -> None: ...

class SearchLogsRequest(_message.Message):
    __slots__ = ("project_id", "service_id", "log_level", "keyword", "limit")
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    SERVICE_ID_FIELD_NUMBER: _ClassVar[int]
    LOG_LEVEL_FIELD_NUMBER: _ClassVar[int]
    KEYWORD_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    project_id: int
    service_id: int
    log_level: str
    keyword: str
    limit: int
    def __init__(self, project_id: _Optional[int] = ..., service_id: _Optional[int] = ..., log_level: _Optional[str] = ..., keyword: _Optional[str] = ..., limit: _Optional[int] = ...) -> None: ...

class SearchLogsResponse(_message.Message):
    __slots__ = ("entries",)
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    entries: _containers.RepeatedCompositeFieldContainer[LogEntry]
    def __init__(self, entries: _Optional[_Iterable[_Union[LogEntry, _Mapping]]] = ...) -> None: ...

class LogEntry(_message.Message):
    __slots__ = ("timestamp", "level", "message", "service", "trace_id")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    SERVICE_FIELD_NUMBER: _ClassVar[int]
    TRACE_ID_FIELD_NUMBER: _ClassVar[int]
    timestamp: str
    level: str
    message: str
    service: str
    trace_id: str
    def __init__(self, timestamp: _Optional[str] = ..., level: _Optional[str] = ..., message: _Optional[str] = ..., service: _Optional[str] = ..., trace_id: _Optional[str] = ...) -> None: ...

class UpdateIssueRequest(_message.Message):
    __slots__ = ("issue_id", "fields")
    class FieldsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ISSUE_ID_FIELD_NUMBER: _ClassVar[int]
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    issue_id: int
    fields: _containers.ScalarMap[str, str]
    def __init__(self, issue_id: _Optional[int] = ..., fields: _Optional[_Mapping[str, str]] = ...) -> None: ...

class UpdateIssueResponse(_message.Message):
    __slots__ = ("issue",)
    ISSUE_FIELD_NUMBER: _ClassVar[int]
    issue: Issue
    def __init__(self, issue: _Optional[_Union[Issue, _Mapping]] = ...) -> None: ...

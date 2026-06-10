from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RunAgentRequest(_message.Message):
    __slots__ = ("task_id", "issue_id", "issue_no", "title", "description", "error_message", "log_excerpt", "environment", "project_id", "project_name", "service_name", "impact_scope")
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    ISSUE_ID_FIELD_NUMBER: _ClassVar[int]
    ISSUE_NO_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    LOG_EXCERPT_FIELD_NUMBER: _ClassVar[int]
    ENVIRONMENT_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    PROJECT_NAME_FIELD_NUMBER: _ClassVar[int]
    SERVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    IMPACT_SCOPE_FIELD_NUMBER: _ClassVar[int]
    task_id: int
    issue_id: int
    issue_no: str
    title: str
    description: str
    error_message: str
    log_excerpt: str
    environment: str
    project_id: int
    project_name: str
    service_name: str
    impact_scope: str
    def __init__(self, task_id: _Optional[int] = ..., issue_id: _Optional[int] = ..., issue_no: _Optional[str] = ..., title: _Optional[str] = ..., description: _Optional[str] = ..., error_message: _Optional[str] = ..., log_excerpt: _Optional[str] = ..., environment: _Optional[str] = ..., project_id: _Optional[int] = ..., project_name: _Optional[str] = ..., service_name: _Optional[str] = ..., impact_scope: _Optional[str] = ...) -> None: ...

class RunAgentResponse(_message.Message):
    __slots__ = ("progress", "result", "error")
    PROGRESS_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    progress: ProgressUpdate
    result: AgentResult
    error: ErrorInfo
    def __init__(self, progress: _Optional[_Union[ProgressUpdate, _Mapping]] = ..., result: _Optional[_Union[AgentResult, _Mapping]] = ..., error: _Optional[_Union[ErrorInfo, _Mapping]] = ...) -> None: ...

class ProgressUpdate(_message.Message):
    __slots__ = ("step", "step_label", "message")
    STEP_FIELD_NUMBER: _ClassVar[int]
    STEP_LABEL_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    step: int
    step_label: str
    message: str
    def __init__(self, step: _Optional[int] = ..., step_label: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class AgentResult(_message.Message):
    __slots__ = ("summary", "issue_type", "related_services", "suspected_cause", "evidence", "suggestions", "missing_info", "next_steps", "confidence", "tool_calls")
    SUMMARY_FIELD_NUMBER: _ClassVar[int]
    ISSUE_TYPE_FIELD_NUMBER: _ClassVar[int]
    RELATED_SERVICES_FIELD_NUMBER: _ClassVar[int]
    SUSPECTED_CAUSE_FIELD_NUMBER: _ClassVar[int]
    EVIDENCE_FIELD_NUMBER: _ClassVar[int]
    SUGGESTIONS_FIELD_NUMBER: _ClassVar[int]
    MISSING_INFO_FIELD_NUMBER: _ClassVar[int]
    NEXT_STEPS_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    TOOL_CALLS_FIELD_NUMBER: _ClassVar[int]
    summary: str
    issue_type: str
    related_services: _containers.RepeatedScalarFieldContainer[str]
    suspected_cause: str
    evidence: _containers.RepeatedCompositeFieldContainer[EvidenceItem]
    suggestions: _containers.RepeatedScalarFieldContainer[str]
    missing_info: _containers.RepeatedScalarFieldContainer[str]
    next_steps: _containers.RepeatedScalarFieldContainer[str]
    confidence: float
    tool_calls: _containers.RepeatedCompositeFieldContainer[ToolCallRecord]
    def __init__(self, summary: _Optional[str] = ..., issue_type: _Optional[str] = ..., related_services: _Optional[_Iterable[str]] = ..., suspected_cause: _Optional[str] = ..., evidence: _Optional[_Iterable[_Union[EvidenceItem, _Mapping]]] = ..., suggestions: _Optional[_Iterable[str]] = ..., missing_info: _Optional[_Iterable[str]] = ..., next_steps: _Optional[_Iterable[str]] = ..., confidence: _Optional[float] = ..., tool_calls: _Optional[_Iterable[_Union[ToolCallRecord, _Mapping]]] = ...) -> None: ...

class EvidenceItem(_message.Message):
    __slots__ = ("source", "content", "relevance")
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    RELEVANCE_FIELD_NUMBER: _ClassVar[int]
    source: str
    content: str
    relevance: str
    def __init__(self, source: _Optional[str] = ..., content: _Optional[str] = ..., relevance: _Optional[str] = ...) -> None: ...

class ToolCallRecord(_message.Message):
    __slots__ = ("step", "tool_name", "input", "output", "thought", "executed_at", "duration_ms")
    STEP_FIELD_NUMBER: _ClassVar[int]
    TOOL_NAME_FIELD_NUMBER: _ClassVar[int]
    INPUT_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_FIELD_NUMBER: _ClassVar[int]
    THOUGHT_FIELD_NUMBER: _ClassVar[int]
    EXECUTED_AT_FIELD_NUMBER: _ClassVar[int]
    DURATION_MS_FIELD_NUMBER: _ClassVar[int]
    step: int
    tool_name: str
    input: str
    output: str
    thought: str
    executed_at: str
    duration_ms: int
    def __init__(self, step: _Optional[int] = ..., tool_name: _Optional[str] = ..., input: _Optional[str] = ..., output: _Optional[str] = ..., thought: _Optional[str] = ..., executed_at: _Optional[str] = ..., duration_ms: _Optional[int] = ...) -> None: ...

class ErrorInfo(_message.Message):
    __slots__ = ("code", "message")
    CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    code: str
    message: str
    def __init__(self, code: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

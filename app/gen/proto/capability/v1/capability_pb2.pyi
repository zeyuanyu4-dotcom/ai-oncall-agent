from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GenerateTextRequest(_message.Message):
    __slots__ = ("prompt", "model", "max_tokens")
    PROMPT_FIELD_NUMBER: _ClassVar[int]
    MODEL_FIELD_NUMBER: _ClassVar[int]
    MAX_TOKENS_FIELD_NUMBER: _ClassVar[int]
    prompt: str
    model: str
    max_tokens: int
    def __init__(self, prompt: _Optional[str] = ..., model: _Optional[str] = ..., max_tokens: _Optional[int] = ...) -> None: ...

class GenerateTextResponse(_message.Message):
    __slots__ = ("text", "prompt_tokens", "completion_tokens")
    TEXT_FIELD_NUMBER: _ClassVar[int]
    PROMPT_TOKENS_FIELD_NUMBER: _ClassVar[int]
    COMPLETION_TOKENS_FIELD_NUMBER: _ClassVar[int]
    text: str
    prompt_tokens: int
    completion_tokens: int
    def __init__(self, text: _Optional[str] = ..., prompt_tokens: _Optional[int] = ..., completion_tokens: _Optional[int] = ...) -> None: ...

class VectorizeTextRequest(_message.Message):
    __slots__ = ("texts", "collection")
    TEXTS_FIELD_NUMBER: _ClassVar[int]
    COLLECTION_FIELD_NUMBER: _ClassVar[int]
    texts: _containers.RepeatedScalarFieldContainer[str]
    collection: str
    def __init__(self, texts: _Optional[_Iterable[str]] = ..., collection: _Optional[str] = ...) -> None: ...

class VectorizeTextResponse(_message.Message):
    __slots__ = ("vectors", "dim")
    VECTORS_FIELD_NUMBER: _ClassVar[int]
    DIM_FIELD_NUMBER: _ClassVar[int]
    vectors: _containers.RepeatedCompositeFieldContainer[Vector]
    dim: int
    def __init__(self, vectors: _Optional[_Iterable[_Union[Vector, _Mapping]]] = ..., dim: _Optional[int] = ...) -> None: ...

class Vector(_message.Message):
    __slots__ = ("values",)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, values: _Optional[_Iterable[float]] = ...) -> None: ...

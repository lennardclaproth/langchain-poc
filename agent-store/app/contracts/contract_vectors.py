from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field

Metadata = Dict[str, Any]


class VectorCreate(BaseModel):
    id: str
    collection: str
    document: str
    metadata: Metadata = Field(default_factory=dict)


class VectorUpdate(BaseModel):
    id: str
    collection: str
    document: Optional[str] = None
    metadata: Optional[Metadata] = None  # patch semantics (merge in repo)


class VectorRead(BaseModel):
    collection: str
    id: str
    model_config = ConfigDict(from_attributes=True)
    document: Optional[str] = None
    metadata: Metadata = Field(default_factory=dict)


class VectorCollectionRead(BaseModel):
    collection: str
    count: int
    metadata: Metadata = Field(default_factory=dict)


class VectorQueryRequest(BaseModel):
    collection: str
    query: Union[str, List[str]]
    n_results: int = 5
    where: Optional[Metadata] = None
    where_document: Optional[Dict[str, Any]] = None


class VectorQueryHit(VectorRead):
    distance: Optional[float] = None


class VectorQueryResponse(BaseModel):
    hits: List[VectorQueryHit]
    grouped: List[List[VectorQueryHit]] = Field(default_factory=list)

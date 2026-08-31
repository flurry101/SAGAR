# attr: m1
# [common response schemas]
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class Meta(BaseModel):
    # [metadata fields]
    request_id: Optional[str] = Field(default=None, description="unique request identifier")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="utc timestamp of the response",
    )
    version: str = Field(default="v1", description="api version")


class ErrorDetails(BaseModel):
    # [error payload]
    code: str = Field(..., description="machine readable error code")
    message: str = Field(..., description="human readable error description")
    details: Optional[Any] = Field(default=None, description="optional additional error details")


class APIResponse(BaseModel, Generic[T]):
    # [standard response envelope]
    status: str = Field(..., description="response status: success, needs_clarification, error")
    data: Optional[T] = Field(default=None, description="response payload")
    meta: Meta = Field(default_factory=Meta, description="response metadata")


class ErrorResponse(BaseModel):
    # [standard error envelope]
    status: str = Field(default="error", description="status code indicator")
    error: ErrorDetails = Field(..., description="error information")
    meta: Meta = Field(default_factory=Meta, description="response metadata")
# attr: m1


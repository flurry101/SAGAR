# attr: m1
# [provenance metadata schema]
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class Provenance(BaseModel):
    # [data source attribution and fallback tracking]
    source_name: str = Field(default="unknown", description="name of the data provider")
    source_type: str = Field(
        default="authoritative",
        description="source type e.g. authoritative, ml_inference, static_fallback",
    )
    retrieved_at: str = Field(..., description="utc timestamp when data was fetched")
    valid_until: Optional[str] = Field(default=None, description="expiration timestamp")
    fallback_tier: int = Field(default=1, description="fallback tier: 1 live, 2 ml, 3 static")
    confidence: Optional[float] = Field(default=1.0, description="confidence score 0.0 to 1.0")
# attr: m1


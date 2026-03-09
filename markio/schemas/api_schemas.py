from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ParseResponse(BaseModel):
    api_version: str = Field(default="v1", description="API version")
    parsed_content: str = Field(description="Parsed markdown/text output")
    parser: str = Field(description="Parser identifier used for this request")
    source_type: Literal["file", "url"] = Field(
        description="Source type for this parse request"
    )
    request_id: str = Field(description="Request correlation id")
    duration_ms: int = Field(description="Server-side parse duration in milliseconds")

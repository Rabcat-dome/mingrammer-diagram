"""Stable diagnostics never include rejected payload values."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Diagnostic(BaseModel):
    model_config = ConfigDict(extra="forbid")
    severity: Literal["error", "warning"]
    code: str
    field: str
    entity_id: str | None = None
    message: str
    remedy: str


class ValidationResult(BaseModel):
    valid: bool
    mode: Literal["strict", "lenient"]
    draft: bool
    validation_scope: Literal["core_only"] = "core_only"
    schema_version: str = "1.0.0"
    diagnostics: list[Diagnostic] = Field(default_factory=list)
    selected_view: str | None = None
    excluded_ids: list[str] = Field(default_factory=list)
    view_exclusions: dict[str, list[str]] = Field(default_factory=dict)
    pending_checks: list[str] = Field(
        default_factory=lambda: ["catalog", "provider_rules", "render"]
    )

"""SHARP Extension Specs - Healthcare context propagation for MCP.

Implements the SHARP-on-MCP spec (https://sharponmcp.com).
Three HTTP headers propagate healthcare context:
  - X-FHIR-Server-URL
  - X-Patient-ID
  - X-FHIR-Access-Token (NEVER logged or passed to LLM)
"""

import contextvars
from dataclasses import dataclass
from typing import Any, Optional


SHARP_CAPABILITIES: dict[str, Any] = {
    "experimental": {
        "fhir_context_required": {"value": False},
    },
}


@dataclass
class SharpContext:
    """Healthcare context extracted from SHARP headers."""

    fhir_server_url: Optional[str] = None
    patient_id: Optional[str] = None
    fhir_access_token: Optional[str] = None

    @property
    def has_fhir_context(self) -> bool:
        """True if both server URL and patient ID are present."""
        return bool(self.fhir_server_url and self.patient_id)

    def __repr__(self) -> str:
        """Safe repr - NEVER include the access token."""
        token_status = "present" if self.fhir_access_token else "absent"
        return (
            f"SharpContext(fhir_server_url={self.fhir_server_url!r}, "
            f"patient_id={self.patient_id!r}, "
            f"fhir_access_token=<{token_status}>)"
        )


def extract_sharp_context(headers: dict[str, str]) -> SharpContext:
    """Extract SHARP context from HTTP headers."""
    return SharpContext(
        fhir_server_url=headers.get("X-FHIR-Server-URL"),
        patient_id=headers.get("X-Patient-ID"),
        fhir_access_token=headers.get("X-FHIR-Access-Token"),
    )


# ---------------------------------------------------------------------------
# Per-request contextvar for SHARP context (used by HTTP middleware)
# ---------------------------------------------------------------------------

_sharp_context_var: contextvars.ContextVar[SharpContext] = contextvars.ContextVar(
    "sharp_context", default=SharpContext()
)


def get_sharp_context() -> SharpContext:
    """Get the current request's SHARP context (set by middleware)."""
    return _sharp_context_var.get()


def set_sharp_context(ctx: SharpContext) -> None:
    """Set SHARP context for the current request (called by middleware)."""
    _sharp_context_var.set(ctx)

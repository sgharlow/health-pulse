"""Input validation for MCP tool parameters."""

import re
from typing import Optional


def validate_state(state: Optional[str]) -> Optional[str]:
    """Validate and sanitize state parameter. Returns None if invalid."""
    if not state:
        return None
    state = state.strip().upper()
    if re.match(r'^[A-Z]{2}$', state):
        return state
    return None


def validate_facility_id(facility_id: str) -> Optional[str]:
    """Validate a CMS facility ID (CCN). Returns None if invalid."""
    fid = facility_id.strip()
    if re.match(r'^[A-Z0-9]{6}$', fid, re.IGNORECASE):
        return fid
    return None


def validate_facility_ids(facility_ids: list[str]) -> list[str]:
    """Validate a list of facility IDs, returning only valid ones."""
    return [fid for fid in (validate_facility_id(f) for f in facility_ids) if fid]

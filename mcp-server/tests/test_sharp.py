"""Tests for SHARP healthcare context propagation."""

from healthpulse_mcp.sharp import SharpContext, extract_sharp_context, SHARP_CAPABILITIES


def test_extract_from_headers():
    headers = {
        "X-FHIR-Server-URL": "https://fhir.example.com/r4",
        "X-Patient-ID": "patient-123",
        "X-FHIR-Access-Token": "bearer-token-abc",
    }
    ctx = extract_sharp_context(headers)
    assert ctx.fhir_server_url == "https://fhir.example.com/r4"
    assert ctx.patient_id == "patient-123"
    assert ctx.fhir_access_token == "bearer-token-abc"
    assert ctx.has_fhir_context is True


def test_extract_empty_headers():
    ctx = extract_sharp_context({})
    assert ctx.fhir_server_url is None
    assert ctx.patient_id is None
    assert ctx.has_fhir_context is False


def test_partial_headers():
    headers = {"X-Patient-ID": "patient-456"}
    ctx = extract_sharp_context(headers)
    assert ctx.patient_id == "patient-456"
    assert ctx.fhir_server_url is None
    assert ctx.has_fhir_context is False


def test_token_not_in_repr():
    """SHARP tokens must NEVER appear in logs or string representations."""
    headers = {"X-FHIR-Access-Token": "secret-token"}
    ctx = extract_sharp_context(headers)
    text = repr(ctx)
    assert "secret-token" not in text


def test_sharp_capabilities():
    assert SHARP_CAPABILITIES["experimental"]["fhir_context_required"]["value"] is False

"""Integration tests — verify all 5 tools are registered with valid metadata,
plus API key middleware and SHARP middleware behaviour."""

import asyncio
import os
import pytest

from healthpulse_mcp.server import mcp

EXPECTED_TOOLS = {
    "quality_monitor",
    "care_gap_finder",
    "equity_detector",
    "facility_benchmark",
    "executive_briefing",
}


@pytest.mark.asyncio
async def test_all_five_tools_registered():
    """All 5 healthcare analytics tools must be registered on the MCP server."""
    tools = await mcp.list_tools()
    tool_names = {t.name for t in tools}
    assert EXPECTED_TOOLS == tool_names, (
        f"Missing tools: {EXPECTED_TOOLS - tool_names}; "
        f"Extra tools: {tool_names - EXPECTED_TOOLS}"
    )


@pytest.mark.asyncio
async def test_all_tools_have_descriptions():
    """Every tool must have a description longer than 20 characters."""
    tools = await mcp.list_tools()
    for tool in tools:
        assert tool.description is not None, f"Tool {tool.name!r} has no description"
        assert len(tool.description) > 20, (
            f"Tool {tool.name!r} description too short: {tool.description!r}"
        )


@pytest.mark.asyncio
async def test_all_tools_have_input_schemas():
    """Every tool must have a valid inputSchema dict."""
    tools = await mcp.list_tools()
    for tool in tools:
        assert tool.inputSchema is not None, f"Tool {tool.name!r} has no inputSchema"
        schema = tool.inputSchema
        if hasattr(schema, "model_dump"):
            schema = schema.model_dump()
        assert isinstance(schema, dict), f"Tool {tool.name!r} inputSchema is not a dict"
        assert "type" in schema or "properties" in schema, (
            f"Tool {tool.name!r} inputSchema missing type/properties: {schema}"
        )


@pytest.mark.asyncio
async def test_quality_monitor_schema_has_required_params():
    """quality_monitor tool schema includes measure_group and threshold_sigma."""
    tools = await mcp.list_tools()
    tool = next(t for t in tools if t.name == "quality_monitor")
    schema = tool.inputSchema
    if hasattr(schema, "model_dump"):
        schema = schema.model_dump()
    props = schema.get("properties", {})
    assert "measure_group" in props
    assert "threshold_sigma" in props


@pytest.mark.asyncio
async def test_care_gap_finder_schema_has_required_params():
    """care_gap_finder tool schema includes gap_type and min_excess_ratio."""
    tools = await mcp.list_tools()
    tool = next(t for t in tools if t.name == "care_gap_finder")
    schema = tool.inputSchema
    if hasattr(schema, "model_dump"):
        schema = schema.model_dump()
    props = schema.get("properties", {})
    assert "gap_type" in props
    assert "min_excess_ratio" in props


@pytest.mark.asyncio
async def test_equity_detector_schema_has_required_params():
    """equity_detector tool schema includes svi_threshold and outcome_measure."""
    tools = await mcp.list_tools()
    tool = next(t for t in tools if t.name == "equity_detector")
    schema = tool.inputSchema
    if hasattr(schema, "model_dump"):
        schema = schema.model_dump()
    props = schema.get("properties", {})
    assert "svi_threshold" in props
    assert "outcome_measure" in props


@pytest.mark.asyncio
async def test_facility_benchmark_schema_has_required_params():
    """facility_benchmark tool schema includes facility_ids."""
    tools = await mcp.list_tools()
    tool = next(t for t in tools if t.name == "facility_benchmark")
    schema = tool.inputSchema
    if hasattr(schema, "model_dump"):
        schema = schema.model_dump()
    props = schema.get("properties", {})
    assert "facility_ids" in props


@pytest.mark.asyncio
async def test_executive_briefing_schema_has_required_params():
    """executive_briefing tool schema includes scope and include_equity."""
    tools = await mcp.list_tools()
    tool = next(t for t in tools if t.name == "executive_briefing")
    schema = tool.inputSchema
    if hasattr(schema, "model_dump"):
        schema = schema.model_dump()
    props = schema.get("properties", {})
    assert "scope" in props
    assert "include_equity" in props


@pytest.mark.asyncio
async def test_server_name():
    """Server is named HealthPulse AI."""
    assert mcp.name == "HealthPulse AI"


@pytest.mark.asyncio
async def test_server_has_instructions():
    """Server has non-empty instructions."""
    assert mcp.instructions is not None
    assert len(mcp.instructions) > 20


# ---------------------------------------------------------------------------
# API key middleware tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_api_key_middleware_allows_request_when_no_key_configured(monkeypatch):
    """If HP_API_KEY is not set, all requests are allowed through."""
    from starlette.testclient import TestClient
    from starlette.requests import Request
    from starlette.responses import PlainTextResponse
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.middleware import Middleware
    from healthpulse_mcp.server import ApiKeyMiddleware

    monkeypatch.delenv("HP_API_KEY", raising=False)

    async def homepage(request):
        return PlainTextResponse("ok")

    app = Starlette(
        routes=[Route("/", homepage)],
        middleware=[Middleware(ApiKeyMiddleware)],
    )
    client = TestClient(app, raise_server_exceptions=True)
    response = client.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_api_key_middleware_rejects_missing_key(monkeypatch):
    """If HP_API_KEY is set, requests without the header are rejected with 401."""
    from starlette.testclient import TestClient
    from starlette.requests import Request
    from starlette.responses import PlainTextResponse
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.middleware import Middleware
    from healthpulse_mcp.server import ApiKeyMiddleware

    monkeypatch.setenv("HP_API_KEY", "test-secret-key")
    monkeypatch.setenv("HP_API_KEY_HEADER", "X-API-Key")

    async def homepage(request):
        return PlainTextResponse("ok")

    app = Starlette(
        routes=[Route("/", homepage)],
        middleware=[Middleware(ApiKeyMiddleware)],
    )
    client = TestClient(app, raise_server_exceptions=True)
    response = client.get("/")
    assert response.status_code == 401
    assert response.json() == {"error": "Unauthorized"}


@pytest.mark.asyncio
async def test_api_key_middleware_accepts_correct_key(monkeypatch):
    """If HP_API_KEY is set, requests with the correct key are allowed through."""
    from starlette.testclient import TestClient
    from starlette.requests import Request
    from starlette.responses import PlainTextResponse
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.middleware import Middleware
    from healthpulse_mcp.server import ApiKeyMiddleware

    monkeypatch.setenv("HP_API_KEY", "test-secret-key")
    monkeypatch.setenv("HP_API_KEY_HEADER", "X-API-Key")

    async def homepage(request):
        return PlainTextResponse("ok")

    app = Starlette(
        routes=[Route("/", homepage)],
        middleware=[Middleware(ApiKeyMiddleware)],
    )
    client = TestClient(app, raise_server_exceptions=True)
    response = client.get("/", headers={"X-API-Key": "test-secret-key"})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_api_key_middleware_rejects_wrong_key(monkeypatch):
    """Requests with an incorrect API key are rejected with 401."""
    from starlette.testclient import TestClient
    from starlette.requests import Request
    from starlette.responses import PlainTextResponse
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.middleware import Middleware
    from healthpulse_mcp.server import ApiKeyMiddleware

    monkeypatch.setenv("HP_API_KEY", "correct-key")
    monkeypatch.setenv("HP_API_KEY_HEADER", "X-API-Key")

    async def homepage(request):
        return PlainTextResponse("ok")

    app = Starlette(
        routes=[Route("/", homepage)],
        middleware=[Middleware(ApiKeyMiddleware)],
    )
    client = TestClient(app, raise_server_exceptions=True)
    response = client.get("/", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# SHARP middleware tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sharp_middleware_sets_context_from_headers():
    """SharpMiddleware extracts SHARP headers and sets them in the contextvar."""
    from starlette.testclient import TestClient
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.middleware import Middleware
    from healthpulse_mcp.server import SharpMiddleware
    from healthpulse_mcp.sharp import get_sharp_context

    captured = {}

    async def inspect(request):
        ctx = get_sharp_context()
        captured["fhir_server_url"] = ctx.fhir_server_url
        captured["patient_id"] = ctx.patient_id
        captured["has_fhir_context"] = ctx.has_fhir_context
        return JSONResponse({"ok": True})

    app = Starlette(
        routes=[Route("/", inspect)],
        middleware=[Middleware(SharpMiddleware)],
    )
    client = TestClient(app, raise_server_exceptions=True)
    client.get("/", headers={
        "X-FHIR-Server-URL": "https://fhir.example.com/r4",
        "X-Patient-ID": "patient-999",
        "X-FHIR-Access-Token": "tok-abc",
    })
    assert captured["fhir_server_url"] == "https://fhir.example.com/r4"
    assert captured["patient_id"] == "patient-999"
    assert captured["has_fhir_context"] is True


@pytest.mark.asyncio
async def test_sharp_middleware_empty_headers_sets_empty_context():
    """SharpMiddleware with no SHARP headers leaves context fields as empty string."""
    from starlette.testclient import TestClient
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.middleware import Middleware
    from healthpulse_mcp.server import SharpMiddleware
    from healthpulse_mcp.sharp import get_sharp_context

    captured = {}

    async def inspect(request):
        ctx = get_sharp_context()
        captured["fhir_server_url"] = ctx.fhir_server_url
        captured["patient_id"] = ctx.patient_id
        return JSONResponse({"ok": True})

    app = Starlette(
        routes=[Route("/", inspect)],
        middleware=[Middleware(SharpMiddleware)],
    )
    client = TestClient(app, raise_server_exceptions=True)
    client.get("/")
    # extract_sharp_context returns "" for missing headers (not None) via dict.get default ""
    assert captured["fhir_server_url"] == "" or captured["fhir_server_url"] is None
    assert captured["patient_id"] == "" or captured["patient_id"] is None

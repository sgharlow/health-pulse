"""Integration tests — verify all 5 tools are registered with valid metadata."""

import asyncio
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

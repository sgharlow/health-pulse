"""HealthPulse AI MCP server entry point.

Registers 5 healthcare analytics tools via FastMCP and exposes them
over Streamable HTTP transport at /mcp (for Prompt Opinion marketplace).
"""

import contextlib
import os
from typing import Any, AsyncIterator, Optional

from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount
import uvicorn

from healthpulse_mcp.domo_client import DomoClient
from healthpulse_mcp.sharp import SHARP_CAPABILITIES

# ---------------------------------------------------------------------------
# Server initialisation — Streamable HTTP, stateless mode
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="HealthPulse AI",
    instructions=(
        "Healthcare performance intelligence server. "
        "Provides analytics tools for CMS hospital quality, readmissions, "
        "equity, and executive reporting. "
        "SHARP capabilities: "
        + str(SHARP_CAPABILITIES)
    ),
    stateless_http=True,
    streamable_http_path="/mcp",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", "8000")),
)


def _get_domo_client() -> DomoClient:
    """Build DomoClient from environment variables."""
    client_id = os.environ.get("DOMO_CLIENT_ID", "")
    client_secret = os.environ.get("DOMO_CLIENT_SECRET", "")
    return DomoClient(client_id=client_id, client_secret=client_secret)


# ---------------------------------------------------------------------------
# Middleware: API key authentication
# ---------------------------------------------------------------------------

class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        api_key = os.environ.get("HP_API_KEY", "")
        if api_key:  # Only enforce if API key is configured
            header_name = os.environ.get("HP_API_KEY_HEADER", "X-API-Key")
            provided = request.headers.get(header_name, "")
            if provided != api_key:
                return JSONResponse({"error": "Unauthorized"}, status_code=401)
        return await call_next(request)


# ---------------------------------------------------------------------------
# Middleware: SHARP header extraction
# ---------------------------------------------------------------------------

class SharpMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        from healthpulse_mcp.sharp import extract_sharp_context, set_sharp_context
        headers = dict(request.headers)
        # Starlette normalises headers to lowercase
        sharp_headers = {
            "X-FHIR-Server-URL": headers.get("x-fhir-server-url", ""),
            "X-Patient-ID": headers.get("x-patient-id", ""),
            "X-FHIR-Access-Token": headers.get("x-fhir-access-token", ""),
        }
        ctx = extract_sharp_context(sharp_headers)
        set_sharp_context(ctx)
        return await call_next(request)


# ---------------------------------------------------------------------------
# Tool registrations (unchanged call pattern: server decorator → tool module)
# ---------------------------------------------------------------------------

from healthpulse_mcp.tools import (
    care_gap_finder,
    equity_detector,
    executive_briefing,
    facility_benchmark,
    quality_monitor,
)


@mcp.tool(
    name="quality_monitor",
    description=(
        "Detect statistical anomalies in CMS hospital quality measures using Z-score analysis. "
        "Analyzes mortality, readmission, safety, and timeliness measures. "
        "Returns the top 20 anomalous facilities ranked by severity."
    ),
)
async def quality_monitor_tool(
    measure_group: str = "all",
    state: Optional[str] = None,
    threshold_sigma: float = 2.0,
) -> dict[str, Any]:
    """
    Args:
        measure_group: Category of measures to analyze. One of: mortality, readmission, safety, timeliness, all.
        state: Optional two-letter US state code to filter results (e.g. 'CA', 'TX').
        threshold_sigma: Z-score threshold for flagging anomalies. Default 2.0.
    """
    domo = _get_domo_client()
    return await quality_monitor.run(domo, {
        "state": state,
        "measure_group": measure_group,
        "threshold_sigma": threshold_sigma,
    })


@mcp.tool(
    name="care_gap_finder",
    description=(
        "Identify facilities with care gaps: excess readmission ratios above threshold "
        "or quality measures rated worse than the national rate. "
        "Returns up to 30 facilities sorted by excess ratio."
    ),
)
async def care_gap_finder_tool(
    gap_type: str = "all",
    state: Optional[str] = None,
    min_excess_ratio: float = 1.05,
) -> dict[str, Any]:
    """
    Args:
        gap_type: Type of care gap to find. One of: readmission, mortality, safety, all.
        state: Optional two-letter US state code to filter results.
        min_excess_ratio: Minimum excess readmission ratio to flag. Default 1.05.
    """
    domo = _get_domo_client()
    return await care_gap_finder.run(domo, {
        "state": state,
        "gap_type": gap_type,
        "min_excess_ratio": min_excess_ratio,
    })


@mcp.tool(
    name="equity_detector",
    description=(
        "Detect healthcare equity gaps by correlating facility outcomes with "
        "county-level Social Vulnerability Index (SVI) scores. "
        "Flags facilities in high-vulnerability areas and computes star rating disparity."
    ),
)
async def equity_detector_tool(
    outcome_measure: str = "readmission",
    state: Optional[str] = None,
    svi_threshold: float = 0.75,
) -> dict[str, Any]:
    """
    Args:
        outcome_measure: Outcome measure to assess. One of: readmission, mortality, safety.
        state: Optional two-letter US state code to filter results.
        svi_threshold: SVI percentile threshold for high-vulnerability classification. Default 0.75.
    """
    domo = _get_domo_client()
    return await equity_detector.run(domo, {
        "state": state,
        "svi_threshold": svi_threshold,
        "outcome_measure": outcome_measure,
    })


@mcp.tool(
    name="facility_benchmark",
    description=(
        "Benchmark specific hospitals against each other across quality measures "
        "and readmission rates. Provide a list of CMS facility IDs to compare. "
        "Returns per-facility quality measures and readmission data."
    ),
)
async def facility_benchmark_tool(
    facility_ids: list[str],
    measures: Optional[list[str]] = None,
) -> dict[str, Any]:
    """
    Args:
        facility_ids: Required list of CMS facility IDs (e.g. ['100001', '100002']).
        measures: Optional list of specific measure IDs to include (e.g. ['MORT_30_AMI']).
    """
    domo = _get_domo_client()
    return await facility_benchmark.run(domo, {
        "facility_ids": facility_ids,
        "measures": measures or [],
    })


@mcp.tool(
    name="executive_briefing",
    description=(
        "Generate structured data for an executive healthcare system briefing. "
        "Aggregates quality anomalies, readmission gaps, and equity indicators. "
        "Returns structured data with a suggested_prompt for LLM narrative generation. "
        "Does NOT call any LLM itself."
    ),
)
async def executive_briefing_tool(
    scope: str = "network",
    state: Optional[str] = None,
    facility_ids: Optional[list[str]] = None,
    include_equity: bool = True,
) -> dict[str, Any]:
    """
    Args:
        scope: Analysis scope. One of: state, facility, network.
        state: Two-letter US state code (required when scope='state').
        facility_ids: List of facility IDs (used when scope='facility').
        include_equity: Include equity analysis using SVI data. Default True.
    """
    domo = _get_domo_client()
    return await executive_briefing.run(domo, {
        "scope": scope,
        "state": state,
        "facility_ids": facility_ids or [],
        "include_equity": include_equity,
    })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _build_app() -> Starlette:
    """Build the full ASGI app: FastMCP mounted under middleware."""
    # Initialise the inner Starlette app and the session manager (lazy, first call)
    mcp_app = mcp.streamable_http_app()

    # Build a lifespan that delegates to the session manager
    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        async with mcp.session_manager.run():
            yield

    # Wrap with API key auth and SHARP header extraction middleware
    return Starlette(
        routes=[Mount("/", app=mcp_app)],
        middleware=[
            Middleware(ApiKeyMiddleware),
            Middleware(SharpMiddleware),
        ],
        lifespan=lifespan,
    )


def main() -> None:
    """Run the HealthPulse MCP server over Streamable HTTP at /mcp."""
    app = _build_app()
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()

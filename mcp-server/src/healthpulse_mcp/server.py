"""HealthPulse AI MCP server entry point.

Registers 7 healthcare analytics tools and 6 MCP resources via FastMCP and
exposes them over Streamable HTTP transport at /mcp (for Prompt Opinion marketplace).
"""

import contextlib
import json
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
        "equity, executive reporting, and patient-level FHIR drill-down "
        "with Synthea synthetic data. "
        "SHARP capabilities: "
        + str(SHARP_CAPABILITIES)
    ),
    stateless_http=True,
    streamable_http_path="/mcp",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", "8000")),
)


_domo_client: DomoClient | None = None


def _get_domo_client() -> DomoClient:
    """Return the module-level DomoClient singleton, creating it on first call.

    Using a singleton preserves the OAuth token cache across tool calls,
    avoiding redundant token-refresh round-trips to Domo.
    """
    global _domo_client
    if _domo_client is None:
        _domo_client = DomoClient(
            client_id=os.environ.get("DOMO_CLIENT_ID", ""),
            client_secret=os.environ.get("DOMO_CLIENT_SECRET", ""),
        )
    return _domo_client


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
    cost_efficiency,
    cross_cutting_analysis,
    equity_detector,
    executive_briefing,
    facility_benchmark,
    patient_cohort_analysis,
    patient_experience,
    patient_risk_profile,
    quality_monitor,
    state_ranking,
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
    name="cost_efficiency",
    description=(
        "Analyze Medicare Spending Per Beneficiary (MSPB) efficiency across hospitals. "
        "Identifies overspending facilities by comparing hospital spending to national averages, "
        "and correlates cost data with CMS star ratings to flag high-cost low-quality facilities. "
        "Critical for value-based care analysis."
    ),
)
async def cost_efficiency_tool(
    state: Optional[str] = None,
    spending_threshold: float = 1.1,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Args:
        state: Optional two-letter US state code to filter results (e.g. 'CA', 'TX').
        spending_threshold: Ratio of hospital spending to national average above which a facility is flagged as overspending. Default 1.1 (10% above national avg).
        limit: Maximum number of overspending facilities to return. Default 20, max 100.
    """
    domo = _get_domo_client()
    return await cost_efficiency.run(domo, {
        "state": state,
        "spending_threshold": spending_threshold,
        "limit": limit,
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


@mcp.tool(
    name="state_ranking",
    description=(
        "Rank all US states by composite healthcare performance. "
        "Combines average CMS star rating and percentage of facilities worse than the national rate "
        "into a single 0-100 composite score. Returns a ranked list showing the best or worst "
        "performing states for network-level strategic planning."
    ),
)
async def state_ranking_tool(
    limit: int = 10,
    order: str = "worst",
) -> dict[str, Any]:
    """
    Args:
        limit: Number of states to return (default 10, max 50).
        order: Sort order for results. One of: best, worst. Default is 'worst' to surface highest-need states.
    """
    domo = _get_domo_client()
    return await state_ranking.run(domo, {
        "limit": limit,
        "order": order,
    })


@mcp.tool(
    name="cross_cutting_analysis",
    description=(
        "Find facilities with MULTIPLE simultaneous concerns across quality, readmissions, "
        "equity, and CMS star ratings. Identifies systemic failures that siloed analysis misses — "
        "the AI differentiator. A hospital with high readmissions AND low star rating AND serving "
        "a high-poverty community requires fundamentally different intervention than one with a "
        "single issue. Returns facilities sorted by number of compounding concerns."
    ),
)
async def cross_cutting_analysis_tool(
    state: Optional[str] = None,
) -> dict[str, Any]:
    """
    Args:
        state: Optional two-letter US state code to focus the analysis (e.g. 'TX', 'FL').
               When omitted, analyzes all facilities nationwide.
    """
    domo = _get_domo_client()
    return await cross_cutting_analysis.run(domo, {
        "state": state,
    })


@mcp.tool(
    name="patient_risk_profile",
    description=(
        "Get patient-level risk data from synthetic FHIR records. "
        "Given a facility_id, returns a summary of high-risk patients. "
        "Given a facility_id AND patient_id (or via SHARP X-Patient-ID header), "
        "returns that patient's conditions, observations, and risk factors. "
        "Uses Synthea synthetic data — no real PHI."
    ),
)
async def patient_risk_profile_tool(
    facility_id: str,
    patient_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Args:
        facility_id: CMS facility CCN ID (e.g. '050454'). Required.
        patient_id: Optional specific patient UUID for individual drill-down.
    """
    return await patient_risk_profile.run({
        "facility_id": facility_id,
        "patient_id": patient_id,
    })


@mcp.tool(
    name="patient_cohort_analysis",
    description=(
        "Analyze patient cohorts at a facility using synthetic FHIR data. "
        "Given a facility_id and optional condition/risk filters, returns cohort "
        "demographics, comorbidity patterns, and readmission risk indicators. "
        "Connects synthetic patient data to aggregate CMS quality measures. "
        "Uses Synthea synthetic data — no real PHI."
    ),
)
async def patient_cohort_analysis_tool(
    facility_id: str,
    condition: Optional[str] = None,
    risk_level: Optional[str] = None,
) -> dict[str, Any]:
    """
    Args:
        facility_id: CMS facility CCN ID (e.g. '050454'). Required.
        condition: CMS condition group filter. One of: heart-failure, pneumonia, copd, stroke, ami, diabetes, hypertension, ihd.
        risk_level: Filter by patient risk level. One of: high, medium, low.
    """
    return await patient_cohort_analysis.run({
        "facility_id": facility_id,
        "condition": condition,
        "risk_level": risk_level,
    })


@mcp.tool(
    name="patient_experience",
    description=(
        "Analyze HCAHPS patient experience scores across hospitals. "
        "Covers communication with nurses/doctors, staff responsiveness, "
        "hospital environment (cleanliness/quietness), and overall rating. "
        "Returns category averages, worst-performing facilities, and summary statistics. "
        "HCAHPS scores affect CMS Value-Based Purchasing payments."
    ),
)
async def patient_experience_tool(
    measure: str = "all",
    state: Optional[str] = None,
    min_star_rating: Optional[float] = None,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Args:
        measure: HCAHPS measure category to analyze. One of: communication, responsiveness, environment, overall, all.
        state: Optional two-letter US state code to filter results (e.g. 'CA', 'TX').
        min_star_rating: Optional star rating ceiling — returns only facilities BELOW this rating to find worst performers.
        limit: Maximum number of worst-performing facilities to return. Default 20.
    """
    domo = _get_domo_client()
    return await patient_experience.run(domo, {
        "state": state,
        "measure": measure,
        "min_star_rating": min_star_rating,
        "limit": limit,
    })


# ---------------------------------------------------------------------------
# MCP Resource registrations
# ---------------------------------------------------------------------------


@mcp.resource("healthpulse://states")
async def list_states() -> str:
    """List all US states with hospital counts from the facilities dataset."""
    ds_id = os.environ.get("HP_FACILITIES_DATASET_ID", "")
    if not ds_id:
        return json.dumps({"error": "HP_FACILITIES_DATASET_ID not configured"})
    try:
        domo = _get_domo_client()
        rows = domo.query_as_dicts(
            ds_id,
            "SELECT state, COUNT(*) as facility_count FROM table GROUP BY state ORDER BY facility_count DESC",
        )
        return json.dumps({"states": rows, "total_states": len(rows)})
    except Exception as exc:
        return json.dumps({"error": str(exc)})


@mcp.resource("healthpulse://measures")
async def list_measures() -> str:
    """List available CMS quality measures and their clinical descriptions."""
    measures = {
        "MORT_30_AMI": "30-day mortality rate for heart attack (AMI)",
        "MORT_30_HF": "30-day mortality rate for heart failure",
        "MORT_30_COPD": "30-day mortality rate for COPD",
        "MORT_30_PN": "30-day mortality rate for pneumonia",
        "MORT_30_STK": "30-day mortality rate for stroke",
        "MORT_30_CABG": "30-day mortality rate for CABG surgery",
        "PSI_90_SAFETY": "Patient Safety Indicator composite score",
        "OP_18b": "Median time from ED arrival to departure (minutes)",
        "OP_22": "Percentage of patients who left the ED without being seen",
        "SEP_1": "Percentage of patients receiving appropriate sepsis care",
        "IMM_3": "Healthcare workers vaccinated for influenza",
    }
    return json.dumps({"measures": measures, "total_measures": len(measures)})


@mcp.resource("healthpulse://about")
async def about_server() -> str:
    """Describe the HealthPulse AI server, its data sources, and capabilities."""
    about = {
        "name": "HealthPulse AI",
        "description": (
            "Healthcare performance intelligence MCP server. Provides statistical anomaly "
            "detection, care gap identification, equity analysis, facility benchmarking, "
            "and executive briefing generation using CMS hospital quality data."
        ),
        "data_sources": [
            {
                "name": "CMS Hospital General Information",
                "description": "4,800+ US hospitals with star ratings, hospital type, location",
                "update_frequency": "Annual",
                "env_var": "HP_FACILITIES_DATASET_ID",
            },
            {
                "name": "CMS Hospital Quality Measures",
                "description": "Mortality, safety, timeliness, and patient experience measures",
                "update_frequency": "Quarterly",
                "env_var": "HP_QUALITY_DATASET_ID",
            },
            {
                "name": "CMS Hospital Readmissions Reduction Program",
                "description": "Excess readmission ratios by facility and condition",
                "update_frequency": "Annual",
                "env_var": "HP_READMISSIONS_DATASET_ID",
            },
            {
                "name": "CDC/ATSDR Social Vulnerability Index 2022",
                "description": (
                    "County-level SVI scores for 3,144 US counties based on US Census "
                    "Bureau ACS data. Includes poverty, unemployment, uninsured rates, "
                    "education, and minority population metrics."
                ),
                "update_frequency": "Every 2 years",
                "env_var": "HP_COMMUNITY_DATASET_ID",
            },
            {
                "name": "CMS Medicare Spending Per Beneficiary (MSPB)",
                "description": (
                    "Hospital-level Medicare spending per beneficiary including Part A and B "
                    "spending during episodes of care. Compares facility spending to national "
                    "averages for value-based purchasing assessment."
                ),
                "update_frequency": "Annual",
                "env_var": "HP_COST_DATASET_ID",
            },
        ],
        "tools": [
            "quality_monitor — Z-score anomaly detection across CMS quality measures",
            "care_gap_finder — Excess readmission ratios and worse-than-national quality flags",
            "cost_efficiency — Medicare spending per beneficiary analysis with cost-quality correlation",
            "equity_detector — SVI correlation with facility outcomes for equity analysis",
            "facility_benchmark — Side-by-side comparison of specific facilities",
            "executive_briefing — Aggregated network-wide performance data with LLM prompt",
            "state_ranking — Composite performance ranking across all 50 US states",
            "cross_cutting_analysis — Multi-dimensional patterns across quality, equity, and readmissions",
            "patient_risk_profile — Patient-level risk data from synthetic FHIR records",
            "patient_cohort_analysis — Cohort demographics, comorbidities, and readmission indicators",
        ],
        "sharp_support": True,
        "phi_handling": "No PHI — all data is de-identified CMS aggregate and CDC/Synthea synthetic",
    }
    return json.dumps(about, indent=2)


@mcp.resource("healthpulse://facilities")
async def list_facilities() -> str:
    """List hospital facility profiles (bulk listing, limited to 200 rows)."""
    ds_id = os.environ.get("HP_FACILITIES_DATASET_ID", "")
    if not ds_id:
        return json.dumps({"error": "HP_FACILITIES_DATASET_ID not configured"})
    try:
        domo = _get_domo_client()
        sql = (
            "SELECT facility_id, facility_name, state, city_town, zip_code, "
            "hospital_type, hospital_overall_rating, emergency_services "
            "FROM table LIMIT 200"
        )
        rows = domo.query_as_dicts(ds_id, sql)
        return json.dumps({"facilities": rows, "total_returned": len(rows)})
    except Exception as exc:
        return json.dumps({"error": str(exc)})


@mcp.resource("healthpulse://facilities/{facility_id}")
async def get_facility(facility_id: str) -> str:
    """Get a single hospital facility profile by CCN ID (e.g. '050454')."""
    from healthpulse_mcp.validation import validate_facility_id

    ds_id = os.environ.get("HP_FACILITIES_DATASET_ID", "")
    if not ds_id:
        return json.dumps({"error": "HP_FACILITIES_DATASET_ID not configured"})

    clean_id = validate_facility_id(facility_id)
    if not clean_id:
        return json.dumps({"error": f"Invalid facility ID: {facility_id!r}"})

    try:
        domo = _get_domo_client()
        sql = (
            "SELECT facility_id, facility_name, state, city_town, zip_code, "
            "hospital_type, hospital_overall_rating, emergency_services, county_fips "
            f"FROM table WHERE facility_id = '{clean_id}'"
        )
        rows = domo.query_as_dicts(ds_id, sql)
        if not rows:
            return json.dumps({"error": f"Facility not found: {clean_id}"})
        return json.dumps({"facility": rows[0]})
    except Exception as exc:
        return json.dumps({"error": str(exc)})


# Maps measure group name to CMS measure ID prefixes (mirrors quality_monitor.py)
_MEASURE_GROUPS: dict[str, dict[str, str]] = {
    "mortality": {
        "MORT_30_AMI": "30-day mortality rate for heart attack (AMI)",
        "MORT_30_HF": "30-day mortality rate for heart failure",
        "MORT_30_COPD": "30-day mortality rate for COPD",
        "MORT_30_PN": "30-day mortality rate for pneumonia",
        "MORT_30_STK": "30-day mortality rate for stroke",
        "MORT_30_CABG": "30-day mortality rate for CABG surgery",
    },
    "readmission": {
        "READM_30_AMI": "30-day readmission rate for heart attack (AMI)",
        "READM_30_HF": "30-day readmission rate for heart failure",
        "READM_30_COPD": "30-day readmission rate for COPD",
        "READM_30_PN": "30-day readmission rate for pneumonia",
        "READM_30_HIP_KNEE": "30-day readmission rate for hip/knee replacement",
        "READM_30_CABG": "30-day readmission rate for CABG surgery",
    },
    "safety": {
        "PSI_90_SAFETY": "Patient Safety Indicator composite score",
        "HAI_1_SIR": "Central Line-Associated Bloodstream Infection (CLABSI)",
        "HAI_2_SIR": "Catheter-Associated Urinary Tract Infection (CAUTI)",
        "COMP_HIP_KNEE": "Rate of complications for hip/knee replacement",
    },
    "timeliness": {
        "OP_18b": "Median time from ED arrival to departure (minutes)",
        "OP_22": "Percentage of patients who left the ED without being seen",
        "SEP_1": "Percentage of patients receiving appropriate sepsis care",
        "IMM_3": "Healthcare workers vaccinated for influenza",
    },
}


@mcp.resource("healthpulse://measures/{group}")
async def get_measures_by_group(group: str) -> str:
    """Get CMS quality measures filtered by group: mortality, readmission, safety, or timeliness."""
    valid_groups = list(_MEASURE_GROUPS.keys())
    if group not in valid_groups:
        return json.dumps({
            "error": f"Unknown measure group: {group!r}",
            "valid_groups": valid_groups,
        })

    measures = _MEASURE_GROUPS[group]
    return json.dumps({
        "group": group,
        "measures": measures,
        "total_measures": len(measures),
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

"""Executive briefing tool — aggregates network-wide health system performance data."""

import os
from typing import Any

from healthpulse_mcp.analytics import detect_anomalies
from healthpulse_mcp.cache import BRIEFING_TTL, tool_cache
from healthpulse_mcp.domo_client import DomoClient
from healthpulse_mcp.validation import validate_facility_ids, validate_state


async def run(domo: DomoClient, args: dict[str, Any]) -> dict[str, Any]:
    """Generate structured data for an executive health system briefing.

    Does NOT call any LLM. Returns structured data and a suggested_prompt
    that the platform LLM can use to generate a narrative.

    Args:
        domo: Authenticated DomoClient
        args: Tool arguments with keys:
            scope (str): One of state|facility|network
            state (str, optional): Two-letter state code (required when scope=state)
            facility_ids (list[str], optional): Facility IDs (used when scope=facility)
            include_equity (bool): Include equity analysis (default True)

    Returns:
        dict with summary_stats, anomalies, care_gaps, top_performers,
        bottom_performers, equity_flags (optional), equity_summary (optional),
        suggested_prompt, filters, clinical_context
    """
    # --- Cache check (1-hour TTL for executive briefing) ---
    cache_key = tool_cache.make_key("executive_briefing", args)
    cached = tool_cache.get(cache_key)
    if cached is not None:
        return cached

    facilities_id = os.environ.get("HP_FACILITIES_DATASET_ID")
    quality_id = os.environ.get("HP_QUALITY_DATASET_ID")
    readmissions_id = os.environ.get("HP_READMISSIONS_DATASET_ID")

    if not facilities_id:
        return {"error": "HP_FACILITIES_DATASET_ID environment variable not set"}
    if not quality_id:
        return {"error": "HP_QUALITY_DATASET_ID environment variable not set"}
    if not readmissions_id:
        return {"error": "HP_READMISSIONS_DATASET_ID environment variable not set"}

    scope = args.get("scope", "network")
    state = validate_state(args.get("state"))
    facility_ids: list[str] = validate_facility_ids(args.get("facility_ids") or [])
    include_equity = bool(args.get("include_equity", True))

    # Build WHERE conditions based on scope.
    # Note: quality dataset does NOT have 'state' — for state-scoped queries we must
    # first fetch facility_ids from facilities, then filter quality in Python.
    fac_conditions: list[str] = []
    readm_conditions: list[str] = []
    quality_facility_ids: set[str] | None = None  # None means "no facility_id filter"

    if scope == "state" and state:
        fac_conditions.append(f"state = '{state}'")
        readm_conditions.append(f"state = '{state}'")
        # quality filter will be applied in Python after fetching facility_ids
    elif scope == "facility" and facility_ids:
        ids_quoted = ", ".join(f"'{fid}'" for fid in facility_ids)
        fac_conditions.append(f"facility_id IN ({ids_quoted})")
        readm_conditions.append(f"facility_id IN ({ids_quoted})")
        quality_facility_ids = set(facility_ids)

    fac_where = f"WHERE {' AND '.join(fac_conditions)}" if fac_conditions else ""
    readm_where = f"WHERE {' AND '.join(readm_conditions)}" if readm_conditions else ""

    # --- Facilities: count + avg star rating (actual column: hospital_overall_rating) ---
    try:
        fac_sql = (
            f"SELECT facility_id, facility_name, hospital_overall_rating, "
            f"hospital_type, state, county_fips "
            f"FROM table {fac_where}"
        )
        fac_rows = domo.query_as_dicts(facilities_id, fac_sql)
    except Exception as exc:
        return {"error": f"Facilities query failed: {exc}"}

    total_facilities = len(fac_rows)
    ratings = []
    rated_facilities: list[dict[str, Any]] = []
    for row in fac_rows:
        try:
            r = float(row.get("hospital_overall_rating", 0) or 0)
            if r > 0:
                ratings.append(r)
                rated_facilities.append({
                    "facility": row.get("facility_name"),
                    "state": row.get("state"),
                    "star_rating": int(r),
                    "type": row.get("hospital_type"),
                })
        except (ValueError, TypeError):
            pass
    avg_star_rating = round(sum(ratings) / len(ratings), 2) if ratings else None

    # --- Top / bottom performers by star rating ---
    rated_facilities.sort(key=lambda x: x["star_rating"], reverse=True)
    top_performers = rated_facilities[:5]
    bottom_performers = sorted(rated_facilities, key=lambda x: x["star_rating"])[:5]

    # For state scope: derive quality_facility_ids from the facilities we just fetched
    if scope == "state" and state:
        quality_facility_ids = {str(r.get("facility_id")) for r in fac_rows}

    # --- Quality: detect anomalies (quality dataset has no 'state' column) ---
    try:
        quality_sql = (
            "SELECT facility_id, measure_id, score, compared_to_national "
            "FROM table"
        )
        quality_rows = domo.query_as_dicts(quality_id, quality_sql)
    except Exception as exc:
        return {"error": f"Quality query failed: {exc}"}

    # Apply facility_id filter in Python when scoping by state or facility list
    if quality_facility_ids is not None:
        quality_rows = [r for r in quality_rows if str(r.get("facility_id")) in quality_facility_ids]

    # Group by measure and detect anomalies
    measures: dict[str, list[dict[str, Any]]] = {}
    for row in quality_rows:
        mid = str(row.get("measure_id", "UNKNOWN"))
        measures.setdefault(mid, []).append(row)

    all_anomalies: list[dict[str, Any]] = []
    for mid, m_rows in measures.items():
        anomalies = detect_anomalies(m_rows, score_key="score", threshold=2.0)
        all_anomalies.extend(anomalies)

    severity_order = {"critical": 0, "high": 1, "medium": 2}
    all_anomalies.sort(
        key=lambda x: (severity_order.get(x.get("severity", ""), 99), -abs(x.get("z_score", 0)))
    )

    # --- Readmissions: find care gaps (excess ratio > 1.05) ---
    try:
        readm_sql = (
            f"SELECT facility_id, facility_name, state, measure_id, excess_readmission_ratio "
            f"FROM table {readm_where}"
        )
        readm_rows = domo.query_as_dicts(readmissions_id, readm_sql)
    except Exception as exc:
        return {"error": f"Readmissions query failed: {exc}"}

    care_gaps = []
    for row in readm_rows:
        try:
            ratio = float(row.get("excess_readmission_ratio", 0) or 0)
        except (ValueError, TypeError):
            continue
        if ratio > 1.05:
            care_gaps.append({
                "facility_id": row.get("facility_id"),
                "facility_name": row.get("facility_name"),
                "state": row.get("state"),
                "measure_id": row.get("measure_id"),
                "excess_readmission_ratio": round(ratio, 4),
            })

    care_gaps.sort(key=lambda x: x.get("excess_readmission_ratio", 0), reverse=True)

    # --- Summary stats ---
    summary_stats: dict[str, Any] = {
        "total_facilities": total_facilities,
        "anomaly_count": len(all_anomalies),
        "care_gap_count": len(care_gaps),
        "avg_star_rating": avg_star_rating,
        "scope": scope,
        "state": state,
    }

    # --- Optional equity summary + equity_flags ---
    equity_summary: dict[str, Any] | None = None
    equity_flags: list[dict[str, Any]] = []
    if include_equity:
        community_id = os.environ.get("HP_COMMUNITY_DATASET_ID")
        if community_id:
            try:
                svi_sql = "SELECT county_fips, svi_score FROM table"
                svi_rows = domo.query_as_dicts(community_id, svi_sql)

                # Build SVI lookup by county_fips
                svi_by_fips: dict[str, float] = {}
                high_svi_count = 0
                for r in svi_rows:
                    score = _safe_float(r.get("svi_score"))
                    fips = str(r.get("county_fips", "") or "")
                    if score is not None and fips:
                        svi_by_fips[fips] = score
                        if score >= 0.75:
                            high_svi_count += 1

                equity_summary = {
                    "high_vulnerability_counties": high_svi_count,
                    "total_counties_analyzed": len(svi_rows),
                }

                # Build per-facility equity flags by joining fac_rows with SVI
                for fac in fac_rows:
                    fips = str(fac.get("county_fips", "") or "")
                    svi_score = svi_by_fips.get(fips)
                    if svi_score is None:
                        # Try zero-padded FIPS
                        svi_score = svi_by_fips.get(fips.zfill(5))
                    if svi_score is not None and svi_score >= 0.75:
                        # Determine outcome gap from care_gaps
                        fac_id = fac.get("facility_id")
                        fac_care_gaps = [
                            g for g in care_gaps if g.get("facility_id") == fac_id
                        ]
                        if fac_care_gaps:
                            outcome_gap = (
                                f"Excess readmission ratio "
                                f"{fac_care_gaps[0]['excess_readmission_ratio']}"
                            )
                        else:
                            outcome_gap = "No readmission gap detected"
                        equity_flags.append({
                            "facility": fac.get("facility_name"),
                            "svi_score": round(svi_score, 4),
                            "outcome_gap": outcome_gap,
                        })
                # Sort by SVI descending
                equity_flags.sort(
                    key=lambda x: x.get("svi_score", 0), reverse=True
                )
            except Exception:
                equity_summary = {"note": "Equity data unavailable"}
        else:
            equity_summary = {"note": "HP_COMMUNITY_DATASET_ID not configured"}

    # --- Build suggested prompt for LLM narrative ---
    scope_desc = f"the {state} state" if scope == "state" and state else scope
    suggested_prompt = (
        f"You are a healthcare quality analyst. Based on the following data for {scope_desc}, "
        f"write a concise executive briefing (3-5 paragraphs) covering: "
        f"(1) overall performance ({total_facilities} facilities, avg {avg_star_rating} stars), "
        f"(2) top quality concerns ({len(all_anomalies)} anomalies detected), "
        f"(3) readmission care gaps ({len(care_gaps)} facilities above 1.05 ratio), "
        f"(4) equity considerations. "
        f"Use a professional tone suitable for a C-suite audience."
    )

    result: dict[str, Any] = {
        "summary_stats": summary_stats,
        "anomalies": all_anomalies[:10],
        "care_gaps": care_gaps[:10],
        "top_performers": top_performers,
        "bottom_performers": bottom_performers,
        "suggested_prompt": suggested_prompt,
        "filters": {
            "scope": scope,
            "state": state,
            "facility_ids": facility_ids if facility_ids else None,
            "include_equity": include_equity,
        },
        "clinical_context": {
            "anomaly_interpretation": (
                "Quality anomalies are facilities whose measure scores deviate >= 2 standard "
                "deviations from the national mean. Critical anomalies (|Z| >= 3.0) require "
                "immediate review. These do not constitute regulatory findings."
            ),
            "care_gap_interpretation": (
                "Care gaps represent excess readmission ratios > 1.05 — facilities readmitting "
                "patients at rates 5%+ above predicted. CMS penalizes high-ratio hospitals "
                "up to 3% of Medicare payments annually under the HRRP."
            ),
            "equity_interpretation": (
                "High-vulnerability counties (SVI >= 0.75) are in the most socially vulnerable "
                "25% of US counties per CDC/ATSDR criteria. Star rating gaps between high- and "
                "low-SVI communities indicate systemic healthcare equity disparities."
            ),
            "data_currency": (
                "Quality measures: CMS Hospital Compare (most recent release). "
                "Community SVI: CDC/ATSDR Social Vulnerability Index 2022. "
                "Readmissions: FY 2026 Hospital Readmissions Reduction Program."
            ),
        },
    }

    if include_equity and equity_summary is not None:
        result["equity_summary"] = equity_summary
        result["equity_flags"] = equity_flags

    tool_cache.set(cache_key, result, BRIEFING_TTL)
    return result


def _safe_float(value: Any) -> float | None:
    """Convert value to float, return None on failure."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

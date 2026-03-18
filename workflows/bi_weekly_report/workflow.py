"""
BI Weekly Report workflow: 9 steps to produce an executive brief for the property portfolio.

Execution is BPMN-only; see currentVersion/bpmn-bindings.yaml and the BPMN engine.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Any, Optional

from pydantic import BaseModel, Field

from . import api_client


class BiWeeklyReportState(BaseModel):
    """State for the BI Weekly Report workflow."""

    start_date: str = Field(description="Report period start YYYY-MM-DD")
    end_date: str = Field(description="Report period end YYYY-MM-DD")

    active_property_ids: list[int] = Field(default_factory=list)
    active_properties: list[dict] = Field(default_factory=list)

    portfolio_metrics: list[dict] = Field(default_factory=list)
    portfolio_totals: dict = Field(default_factory=dict)

    top_performers: list[dict] = Field(default_factory=list)
    properties_needing_attention: list[dict] = Field(default_factory=list)
    funnel: dict = Field(default_factory=dict)
    week_over_week_trend: dict = Field(default_factory=dict)
    auction_readiness: list[dict] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    executive_brief_markdown: str = Field(default="")

    workflow_steps: list[str] = Field(default_factory=list)


class BiWeeklyReportWorkflow:
    """BI Weekly Report (9 steps). Execution order from BPMN diagram or legacy step order."""

    def __init__(self, run_id: str | None = None):
        self.run_id = run_id

    async def get_active_properties(self, state: BiWeeklyReportState) -> Optional[str]:
        state.workflow_steps.append("get_active_properties")
        data = await asyncio.to_thread(api_client.list_properties, page_size=100, page=1)
        items = (data.get("data") or {}).get("data") or []
        state.active_properties = items
        state.active_property_ids = [int(p["id"]) for p in items if p.get("id") is not None]
        return "collect_portfolio_metrics"

    async def collect_portfolio_metrics(self, state: BiWeeklyReportState) -> str:
        state.workflow_steps.append("collect_portfolio_metrics")
        totals: dict[str, int] = {
            "views": 0,
            "unique_sessions": 0,
            "brochure_downloads": 0,
            "ifb_downloads": 0,
            "bidder_registrations": 0,
            "subscriber_registrations": 0,
            "photo_clicks": 0,
        }
        state.portfolio_metrics = []
        for pid in state.active_property_ids:
            try:
                j = await asyncio.to_thread(
                    api_client.property_summary,
                    pid,
                    state.start_date,
                    state.end_date,
                )
                state.portfolio_metrics.append(j)
                t = j.get("totals") or {}
                for k in totals:
                    totals[k] += int(t.get(k) or 0)
            except Exception:
                continue
        state.portfolio_totals = totals
        return "identify_top_performers"

    async def identify_top_performers(self, state: BiWeeklyReportState) -> str:
        state.workflow_steps.append("identify_top_performers")
        data = await asyncio.to_thread(
            api_client.top_properties,
            state.start_date,
            state.end_date,
            metric="views",
            limit=10,
        )
        state.top_performers = data.get("items") or []
        return "identify_properties_needing_attention"

    async def identify_properties_needing_attention(self, state: BiWeeklyReportState) -> str:
        state.workflow_steps.append("identify_properties_needing_attention")
        data = await asyncio.to_thread(
            api_client.underperforming,
            state.start_date,
            state.end_date,
            min_views=50,
            max_bidder_registrations=2,
            limit=50,
        )
        state.properties_needing_attention = data.get("items") or []
        return "conversion_funnel_analysis"

    async def conversion_funnel_analysis(self, state: BiWeeklyReportState) -> str:
        state.workflow_steps.append("conversion_funnel_analysis")
        t = state.portfolio_totals
        views = t.get("views") or 0
        brochure = t.get("brochure_downloads") or 0
        ifb = t.get("ifb_downloads") or 0
        bidders = t.get("bidder_registrations") or 0
        state.funnel = {
            "views": views,
            "brochure_downloads": brochure,
            "ifb_downloads": ifb,
            "bidder_registrations": bidders,
            "conversion_brochure_pct": round(100 * brochure / views, 2) if views else 0,
            "conversion_ifb_pct": round(100 * ifb / brochure, 2) if brochure else 0,
            "conversion_bidder_pct": round(100 * bidders / ifb, 2) if ifb else 0,
        }
        return "week_over_week_trend"

    async def week_over_week_trend(self, state: BiWeeklyReportState) -> str:
        state.workflow_steps.append("week_over_week_trend")
        try:
            start = datetime.strptime(state.start_date, "%Y-%m-%d").date()
            end = datetime.strptime(state.end_date, "%Y-%m-%d").date()
            delta_days = (end - start).days + 1
            prior_end = start - timedelta(days=1)
            prior_start = prior_end - timedelta(days=delta_days - 1)
            prior_start_str = prior_start.isoformat()
            prior_end_str = prior_end.isoformat()
        except Exception:
            state.week_over_week_trend = {"error": "Invalid date range"}
            return "auction_readiness_snapshot"

        this_totals: dict[str, int] = {
            "views": 0,
            "brochure_downloads": 0,
            "ifb_downloads": 0,
            "bidder_registrations": 0,
        }
        for pid in state.active_property_ids[:20]:
            try:
                j = await asyncio.to_thread(
                    api_client.property_summary,
                    pid,
                    state.start_date,
                    state.end_date,
                )
                t = j.get("totals") or {}
                for k in this_totals:
                    this_totals[k] += int(t.get(k) or 0)
            except Exception:
                continue

        prior_totals: dict[str, int] = {k: 0 for k in this_totals}
        for pid in state.active_property_ids[:20]:
            try:
                j = await asyncio.to_thread(
                    api_client.property_summary,
                    pid,
                    prior_start_str,
                    prior_end_str,
                )
                t = j.get("totals") or {}
                for k in prior_totals:
                    prior_totals[k] += int(t.get(k) or 0)
            except Exception:
                continue

        pct = {}
        for k in this_totals:
            prev = prior_totals.get(k) or 0
            cur = this_totals.get(k) or 0
            pct[f"{k}_pct_change"] = round(100 * (cur - prev) / prev, 2) if prev else (100 if cur else 0)
        state.week_over_week_trend = {
            "this_period": this_totals,
            "prior_period": prior_totals,
            "pct_change": pct,
        }
        return "auction_readiness_snapshot"

    async def auction_readiness_snapshot(self, state: BiWeeklyReportState) -> str:
        state.workflow_steps.append("auction_readiness_snapshot")
        state.auction_readiness = []
        for p in state.active_properties[:15]:
            pid = p.get("id")
            if not pid:
                continue
            try:
                detail = await asyncio.to_thread(api_client.property_detail, int(pid))
                bidding_end = detail.get("bidding_end") or detail.get("bidding_end_date") or ""
                if not bidding_end:
                    continue
                summary = await asyncio.to_thread(
                    api_client.property_summary,
                    int(pid),
                    state.start_date,
                    state.end_date,
                )
                totals = summary.get("totals") or {}
                views = int(totals.get("views") or 0)
                bidders = int(totals.get("bidder_registrations") or 0)
                readiness = "on_track" if (views >= 20 and bidders >= 1) else "needs_attention"
                state.auction_readiness.append({
                    "property_id": pid,
                    "bidding_end": bidding_end,
                    "views": views,
                    "bidder_registrations": bidders,
                    "readiness": readiness,
                })
            except Exception:
                continue
        return "generate_recommended_actions"

    async def generate_recommended_actions(self, state: BiWeeklyReportState) -> str:
        state.workflow_steps.append("generate_recommended_actions")
        actions = []
        if state.properties_needing_attention:
            pids = [x.get("property_id") for x in state.properties_needing_attention[:5] if x.get("property_id")]
            actions.append(f"Follow up on underperformers (high interest, low bidders): property IDs {pids}")
        if state.top_performers:
            pids = [x.get("property_id") for x in state.top_performers[:3] if x.get("property_id")]
            actions.append(f"Highlight top performers in team update: property IDs {pids}")
        need = [x for x in state.auction_readiness if x.get("readiness") == "needs_attention"]
        if need:
            pids = [x.get("property_id") for x in need[:5]]
            actions.append(f"Outreach for low-readiness auctions: property IDs {pids}")
        if not actions:
            actions.append("No specific actions; monitor portfolio metrics.")
        state.recommended_actions = actions
        return "produce_executive_brief"

    async def produce_executive_brief(self, state: BiWeeklyReportState) -> str:
        state.workflow_steps.append("produce_executive_brief")
        t = state.portfolio_totals
        f = state.funnel
        w = state.week_over_week_trend
        lines = [
            f"# BI Weekly Report — {state.start_date} to {state.end_date}",
            "",
            f"**Active properties:** {len(state.active_property_ids)}",
            "",
            "## Portfolio totals",
            f"- Views: {t.get('views', 0)}",
            f"- Unique sessions: {t.get('unique_sessions', 0)}",
            f"- Brochure downloads: {t.get('brochure_downloads', 0)}",
            f"- IFB downloads: {t.get('ifb_downloads', 0)}",
            f"- Bidder registrations: {t.get('bidder_registrations', 0)}",
            "",
            "## Conversion funnel",
            f"- Views → Brochure: {f.get('conversion_brochure_pct', 0)}%",
            f"- Brochure → IFB: {f.get('conversion_ifb_pct', 0)}%",
            f"- IFB → Bidders: {f.get('conversion_bidder_pct', 0)}%",
            "",
        ]
        if w and "pct_change" in w:
            lines.append("## Week-over-week trend")
            for k, v in (w.get("pct_change") or {}).items():
                lines.append(f"- {k}: {v}%")
            lines.append("")

        lines.append("## Top performers (by views)")
        for i, x in enumerate(state.top_performers[:5], 1):
            lines.append(f"{i}. Property {x.get('property_id')}: views={x.get('views', 0)}, bidders={x.get('bidder_registrations', 0)}")
        lines.append("")

        lines.append("## Properties needing attention")
        for x in state.properties_needing_attention[:5]:
            lines.append(f"- Property {x.get('property_id')}: views={x.get('views', 0)}, bidders={x.get('bidder_registrations', 0)}")
        lines.append("")

        lines.append("## Auction readiness")
        for x in state.auction_readiness[:5]:
            lines.append(f"- Property {x.get('property_id')}: {x.get('readiness', '')} (bidders={x.get('bidder_registrations', 0)})")
        lines.append("")

        lines.append("## Recommended actions")
        for a in state.recommended_actions:
            lines.append(f"- {a}")
        state.executive_brief_markdown = "\n".join(lines)
        return None

# Changelog

All notable changes to the **bi_weekly_report** workflow.

## Version 1 – Initial release

**Date:** 2026-03-03

- Initial implementation of BI Weekly Report (9 steps).
- Input: `start_date`, `end_date` (YYYY-MM-DD, required).
- Steps: Get active properties → Collect portfolio metrics → Identify top performers → Identify properties needing attention → Conversion funnel analysis → Week-over-week trend → Auction readiness snapshot → Generate recommended actions → Produce executive brief.
- Output: `executive_brief_markdown`, `portfolio_totals`, `top_performers`, `properties_needing_attention`, `funnel`, `week_over_week_trend`, `auction_readiness`, `recommended_actions`.
- API client for metrics and property API (sync HTTP via asyncio.to_thread).
- Diagram: vertical flow (Start → 9 steps → End).
- Documentation: README, USER_STORY, documentation.md, CHANGELOG.

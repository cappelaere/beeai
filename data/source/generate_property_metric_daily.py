#!/usr/bin/env python3
"""
Generate a CSV seed file for property_metric_daily (~2000 rows) to exercise the BI agent.
No Django dependency; run from repo root: python3 data/source/generate_property_metric_daily.py

Output: data/source/property_metric_daily_seed.csv (or --output path).
Each row is a unique (property_id, date); counts are non-negative and plausible.
"""
import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description="Generate property_metric_daily seed CSV")
    ap.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    ap.add_argument("--rows", type=int, default=2000, help="Number of rows to generate")
    ap.add_argument("--output", type=str, default=None, help="Output CSV path (default: same dir as script)")
    ap.add_argument("--days", type=int, default=60, help="Spread dates over this many days back (UTC)")
    args = ap.parse_args()

    random.seed(args.seed)
    script_dir = Path(__file__).resolve().parent
    out_path = Path(args.output) if args.output else script_dir / "property_metric_daily_seed.csv"

    # Build unique (property_id, date) pairs: 50 properties × 40 days = 2000
    num_properties = 50
    start_date = date.today() - timedelta(days=args.days)
    pairs = []
    for day_offset in range(args.days):
        d = start_date + timedelta(days=day_offset)
        for property_id in range(1, num_properties + 1):
            pairs.append((property_id, d))
    random.shuffle(pairs)
    pairs = pairs[: args.rows]

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "property_id", "date",
            "views", "unique_sessions", "brochure_downloads", "ifb_downloads",
            "bidder_registrations", "subscriber_registrations", "photo_clicks",
        ])
        for property_id, d in pairs:
            views = random.randint(5, 400)
            unique_sessions = random.randint(1, min(views, 200))
            brochure_downloads = random.randint(0, min(views // 3, 80))
            ifb_downloads = random.randint(0, min(brochure_downloads, 40))
            bidder_registrations = random.randint(0, min(ifb_downloads + 2, 15))
            subscriber_registrations = random.randint(0, min(views // 5, 25))
            photo_clicks = random.randint(0, min(views // 2, 120))
            writer.writerow([
                property_id,
                d.isoformat(),
                views,
                unique_sessions,
                brochure_downloads,
                ifb_downloads,
                bidder_registrations,
                subscriber_registrations,
                photo_clicks,
            ])

    print(f"Wrote {len(pairs)} rows to {out_path}")


if __name__ == "__main__":
    main()

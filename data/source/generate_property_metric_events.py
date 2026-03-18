#!/usr/bin/env python3
"""
Generate a CSV seed file for property_metric_event (~2000 rows) to exercise the BI agent.
No Django dependency; run from repo root: python3 data/source/generate_property_metric_events.py

Output: data/source/property_metric_event_seed.csv (or --output path).
"""
import argparse
import csv
import random
from datetime import datetime, timezone, timedelta
from pathlib import Path

EVENT_TYPES = [
    ("view", 60),
    ("download_brochure", 15),
    ("download_ifb", 10),
    ("click_view_photos", 8),
    ("register_subscriber", 4),
    ("register_bidder", 3),
]
REFERRER_DOMAINS = ["", "", "", "", "", "", "", "", "google.com", "direct"]


def main():
    ap = argparse.ArgumentParser(description="Generate property_metric_event seed CSV")
    ap.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    ap.add_argument("--rows", type=int, default=2000, help="Number of rows to generate")
    ap.add_argument("--output", type=str, default=None, help="Output CSV path (default: same dir as script)")
    ap.add_argument("--days", type=int, default=30, help="Spread received_at over this many days back (UTC)")
    args = ap.parse_args()

    random.seed(args.seed)
    script_dir = Path(__file__).resolve().parent
    out_path = Path(args.output) if args.output else script_dir / "property_metric_event_seed.csv"

    # Weighted event type list for random.choice
    event_type_pool = []
    for name, weight in EVENT_TYPES:
        event_type_pool.extend([name] * weight)

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=args.days)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["property_id", "event_type", "session_id", "page_path", "referrer_domain", "received_at"])

        for i in range(args.rows):
            property_id = random.randint(1, 50)
            event_type = random.choice(event_type_pool)
            session_id = "sess_" + "".join(random.choices("0123456789abcdef", k=12))
            page_path = f"/property/{property_id}"
            referrer_domain = random.choice(REFERRER_DOMAINS)
            # Random timestamp in [start, now]
            delta_sec = random.randint(0, args.days * 86400)
            received_at = start + timedelta(seconds=delta_sec)
            received_at_str = received_at.strftime("%Y-%m-%d %H:%M:%S+00")
            writer.writerow([property_id, event_type, session_id, page_path, referrer_domain, received_at_str])

    print(f"Wrote {args.rows} rows to {out_path}")


if __name__ == "__main__":
    main()

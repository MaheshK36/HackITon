"""
Software Platform Login/Logout Audit & Anomaly Detection System — Main CLI Entrypoint
Usage:
    python main.py              # Run 1 audit cycle (demo)
    python main.py --cycles 3   # Run N audit cycles
    python main.py --loop       # Run continuous monitoring loop
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import structlog

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.dev.ConsoleRenderer(colors=True),
    ]
)

from agents.pipeline import AccessAuditPipeline


def print_banner():
    print("=" * 70)
    print("  SOFTWARE PLATFORM LOGIN/LOGOUT AUDIT & ANOMALY DETECTION")
    print("  Immutable Blockchain Audit Trail + Multi-Confirm Anomaly Detection")
    print("=" * 70)


def print_finding(incident: dict):
    inc_id = incident.get("id", "INC-0000")
    user_id = incident.get("user_id", "unknown")
    state = incident.get("state", "Alert")
    atype = incident.get("anomaly_type", "access_anomaly")
    conf = int(incident.get("peak_confidence", 0.8) * 100)

    print(f"\n🚨 [ACCESS ANOMALY ALERT] {inc_id}")
    print(f"   User ID:     {user_id}")
    print(f"   State:       {state}")
    print(f"   Type:        {atype}")
    print(f"   Confidence:  {conf}%")
    print("-" * 50)


async def run_pipeline(args):
    print_banner()
    print(f"Mode: {'Continuous loop' if args.loop else f'{args.cycles} cycle(s)'}\n")

    async def on_incident_callback(inc: dict):
        print_finding(inc)

    pipeline = AccessAuditPipeline(
        on_incident=on_incident_callback,
        poll_interval=15,
        events_per_cycle=10,
    )

    if args.loop:
        await pipeline.run_continuous()
    else:
        for i in range(args.cycles):
            print(f"\n[+] Running audit cycle {i+1}/{args.cycles}...")
            await pipeline.run_cycle()
            if i < args.cycles - 1:
                await asyncio.sleep(2)

        stats = pipeline.get_stats()
        print(f"\n{'='*60}")
        print(f"  AUDIT PIPELINE COMPLETE")
        print(f"  Cycles: {stats['cycles_run']} | Events Processed: {stats['events_processed']} | Anomalies: {stats['anomalies_detected']}")
        print(f"  Audit Trail: data/audit_events.jsonl")
        print(f"  Dashboard: data/dashboard.json")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Software Platform Login/Logout Audit & Anomaly Detection System")
    parser.add_argument("--loop", action="store_true", help="Run continuous monitoring loop")
    parser.add_argument("--cycles", type=int, default=1, help="Number of audit cycles to run (default: 1)")

    args = parser.parse_args()
    asyncio.run(run_pipeline(args))


if __name__ == "__main__":
    main()

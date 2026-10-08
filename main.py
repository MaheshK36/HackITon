"""
main.py - Single Root Entrypoint & CLI for SIH-MAX Predictive Cyber-Defence Platform

Usage:
  python main.py serve [--host HOST] [--port PORT]
  python main.py train
  python main.py test
  python main.py replay [--scenario SCENARIO] [--events EVENTS]
  python main.py status
"""

import argparse
import sys
import unittest
from pathlib import Path

# Add root and sub-modules to sys.path
ROOT_DIR = Path(__file__).resolve().parent
UNIFIED_DIR = ROOT_DIR / "cyber_dashboard-main" / "unified_cybersecurity_system"

if str(UNIFIED_DIR) not in sys.path:
    sys.path.insert(0, str(UNIFIED_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(1, str(ROOT_DIR))


def cmd_serve(args):
    import uvicorn
    print("=" * 70)
    print("  SIH-MAX: PREDICTIVE CYBER-DEFENCE PLATFORM")
    print("=" * 70)
    print(f"  Command Center URL : http://localhost:{args.port}")
    print(f"  REST API Swagger   : http://localhost:{args.port}/docs")
    print(f"  Health Check       : http://localhost:{args.port}/api/health")
    print(f"  Digital Twin State : http://localhost:{args.port}/api/v1/twin/state")
    print(f"  Model Metadata     : http://localhost:{args.port}/api/v1/model/info")
    print(f"  Audit Logs         : http://localhost:{args.port}/api/audit-logs")
    print("=" * 70)
    print("  Press Ctrl+C to stop server.")
    print("=" * 70)
    uvicorn.run("backend.server:app", host=args.host, port=args.port, reload=False)


def cmd_train(args):
    from scripts.train_baseline import run_training
    run_training()


def cmd_test(args):
    print("=" * 70)
    print("  RUNNING FULL PLATFORM VERIFICATION TEST SUITE")
    print("=" * 70)
    test_dir = UNIFIED_DIR / "tests"
    suite = unittest.defaultTestLoader.discover(str(test_dir), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)


def cmd_replay(args):
    from backend.services.replay_service import replay_service
    from backend.services.platform import platform
    print("=" * 70)
    print(f"  STREAMING REPLAY SCENARIO: {args.scenario} ({args.events} events)")
    print("=" * 70)
    try:
        results = replay_service.replay_scenario(args.scenario, max_events=args.events)
        print(f" Successfully replayed {len(results)} events into the Digital Twin.")
        snapshot = platform.snapshot()
        print(f" Digital Twin Active Hosts : {len(snapshot['nodes'])}")
        print(f" Active Flow Edges         : {len(snapshot['edges'])}")
        print(f" Critical Assets Identified: {len(snapshot['critical_assets'])}")
        print("\n Recent Detected Stages:")
        for r in results[-5:]:
            ev = r["event"]
            dec = r["decision"]
            print(f"   [{dec['inference_mode']}] {ev['source_ip']} -> {ev['destination_ip']}:{ev['destination_port']} "
                  f"| State: {dec['current_state']} -> Next: {dec['predicted_next_state']} (Conf: {dec['confidence']})")
        print("=" * 70)
    except Exception as e:
        print(f" Replay Error: {e}")
        sys.exit(1)


def cmd_status(args):
    from backend.services.platform import platform
    from backend.services.replay_service import replay_service
    print("=" * 70)
    print("  SIH-MAX PLATFORM STATUS")
    print("=" * 70)
    snapshot = platform.snapshot()
    print(f" Operating Mode  : {snapshot['mode']}")
    print(f" ML Model Status : {snapshot['model_status']['attack_state']}")
    if snapshot['model_status']['is_model_trained']:
        metrics = snapshot['model_status']['evaluation_metrics']
        print(f"   - Model Version : {snapshot['model_status']['model_version']}")
        print(f"   - Accuracy      : {metrics.get('accuracy', 0) * 100:.1f}%")
        print(f"   - Macro F1      : {metrics.get('macro_f1', 0) * 100:.1f}%")
    print(f" Digital Twin    : {len(snapshot['nodes'])} nodes, {len(snapshot['edges'])} edges")
    print(" Available Scenarios for Replay:")
    for sc in replay_service.list_available_scenarios():
        print(f"   - {sc['scenario_id']}: {'Available' if sc['available'] else 'Not Found'} ({sc['filename']})")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="SIH-MAX Predictive Cyber-Defence Platform CLI")
    subparsers = parser.add_subparsers(dest="command", help="Platform command to execute")

    # serve
    serve_p = subparsers.add_parser("serve", help="Start the FastAPI backend server & dashboard")
    serve_p.add_argument("--host", default="0.0.0.0", help="Binding host address")
    serve_p.add_argument("--port", type=int, default=8000, help="Port number")

    # train
    subparsers.add_parser("train", help="Train baseline ML threat models and evaluate metrics")

    # test
    subparsers.add_parser("test", help="Run full platform verification test suite")

    # replay
    replay_p = subparsers.add_parser("replay", help="Replay attack or benign scenario telemetry")
    replay_p.add_argument("--scenario", default="scenario_a", help="Scenario id (scenario_a, scenario_b, scenario_c)")
    replay_p.add_argument("--events", type=int, default=25, help="Number of events to replay")

    # status
    subparsers.add_parser("status", help="Show current platform status and model info")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    commands = {
        "serve": cmd_serve,
        "train": cmd_train,
        "test": cmd_test,
        "replay": cmd_replay,
        "status": cmd_status
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()

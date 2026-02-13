#!/usr/bin/env python
"""
AMI-ENGINE CLI

Usage:
    ami-engine dashboard          # Start Streamlit dashboard
    ami-engine realtime [--duration SEC] [--profile PROFILE]  # Run live test
    ami-engine tests             # Run test suite
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def cmd_dashboard(args):
    """Start Streamlit dashboard."""
    dashboard_path = ROOT / "visualization" / "dashboard.py"
    if not dashboard_path.exists():
        print(f"Error: Dashboard not found at {dashboard_path}")
        sys.exit(1)
    cmd = ["streamlit", "run", str(dashboard_path)]
    if args.port:
        cmd.extend(["--server.port", str(args.port)])
    print(f"Starting dashboard at http://localhost:{args.port or 8501}")
    subprocess.run(cmd)


def cmd_realtime(args):
    """Run live test."""
    script_path = ROOT / "tools" / "realtime_10min.py"
    if not script_path.exists():
        print(f"Error: Realtime script not found at {script_path}")
        sys.exit(1)
    cmd = [sys.executable, str(script_path), "--duration", str(args.duration)]
    if args.profile:
        cmd.extend(["--profile", args.profile])
    print(f"Running live test: {args.duration}s, profile={args.profile or 'scenario_test'}")
    subprocess.run(cmd)


def cmd_tests(args):
    """Run test suite."""
    test_script = ROOT / "run_all_tests.py"
    if not test_script.exists():
        print(f"Error: Test script not found at {test_script}")
        sys.exit(1)
    cmd = [sys.executable, str(test_script)]
    if args.verbose:
        cmd.append("-v")
    subprocess.run(cmd)


def cmd_demo(args):
    """Run proof-of-concept demo."""
    import time
    import sys
    from pathlib import Path
    
    # Import from repo root
    _root = Path(__file__).resolve().parent.parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    
    from ami_engine import decide
    from core.trace_collector import TraceCollector, build_decision_trace
    
    print("=" * 60)
    print("AMI-ENGINE Proof-of-Concept Demo")
    print("=" * 60)
    
    collector = TraceCollector(jsonl_path="demo_traces.jsonl")
    
    # Generate sample decisions
    print(f"\nGenerating {args.steps} decisions...")
    for i in range(args.steps):
        raw_state = {
            "risk": 0.5 + (i * 0.05) % 0.5,
            "severity": 0.6 + (i * 0.03) % 0.4,
            "physical": 0.5,
            "social": 0.5,
            "context": 0.4,
            "compassion": 0.5,
            "justice": 0.9,
            "harm_sens": 0.5,
            "responsibility": 0.7,
            "empathy": 0.6,
        }
        
        t_before = time.perf_counter()
        result = decide(raw_state, profile=args.profile or "scenario_test")
        t_after = time.perf_counter()
        latency_ms = (t_after - t_before) * 1000
        
        trace = build_decision_trace(result, t=i, latency_ms=latency_ms)
        collector.push(trace)
        
        if (i + 1) % 10 == 0:
            print(f"  [{i+1:03d}] L{trace['level']} cus={trace.get('cus', 0):.3f} "
                  f"human={trace.get('human_escalation', False)}")
    
        # TraceCollector doesn't have close(), it auto-flushes
    
    print(f"\n[OK] Generated {args.steps} traces")
    print(f"   Saved to: {collector.jsonl_path}")
    print(f"\nNext steps:")
    print(f"   1. View traces: ami-engine dashboard")
    print(f"   2. Load file: {collector.jsonl_path}")
    print(f"   3. Check CSV export from dashboard")


def main():
    parser = argparse.ArgumentParser(
        description="AMI-ENGINE CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__ + "\n\nUsage Policy: See USAGE_POLICY.md for guidelines and prohibited uses.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Dashboard command
    dash_parser = subparsers.add_parser("dashboard", help="Start Streamlit dashboard")
    dash_parser.add_argument("--port", type=int, help="Port number (default: 8501)")
    dash_parser.set_defaults(func=cmd_dashboard)

    # Realtime command
    realtime_parser = subparsers.add_parser("realtime", help="Run live test")
    realtime_parser.add_argument(
        "--duration", type=int, default=600, help="Test duration in seconds (default: 600)"
    )
    realtime_parser.add_argument(
        "--profile",
        type=str,
        help="Config profile (default: scenario_test)",
    )
    realtime_parser.set_defaults(func=cmd_realtime)

    # Tests command
    tests_parser = subparsers.add_parser("tests", help="Run test suite")
    tests_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    tests_parser.set_defaults(func=cmd_tests)

    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Run proof-of-concept demo")
    demo_parser.add_argument(
        "--steps", type=int, default=30, help="Number of decisions to generate (default: 30)"
    )
    demo_parser.add_argument(
        "--profile",
        type=str,
        help="Config profile (default: scenario_test)",
    )
    demo_parser.set_defaults(func=cmd_demo)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()

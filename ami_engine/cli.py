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


def main():
    parser = argparse.ArgumentParser(
        description="AMI-ENGINE CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
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

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()

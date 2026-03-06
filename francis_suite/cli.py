"""
francis_suite/cli.py

Francis Suite CLI — command line interface.
Allows running workflows from the terminal.

Usage:
    francis-suite run workflow.xml
    francis-suite run workflow.xml --var nombre=Francis --var url=https://ejemplo.com
    francis-suite --version
    francis-suite --help
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="francis-suite",
        description="Francis Suite — Low-code web scraping framework",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="Francis Suite 0.1.0",
    )

    subparsers = parser.add_subparsers(dest="command")

    # francis-suite run workflow.xml
    run_parser = subparsers.add_parser(
        "run",
        help="Run a workflow XML file",
    )
    run_parser.add_argument(
        "workflow",
        help="Path to the workflow XML file",
    )
    run_parser.add_argument(
        "--var",
        action="append",
        metavar="KEY=VALUE",
        help="Pass variables to the workflow (can be used multiple times)",
        default=[],
    )

    args = parser.parse_args()

    if args.command == "run":
        _run(args)
    else:
        parser.print_help()


def _run(args) -> None:
    from francis_suite.core.parser import FParser
    from francis_suite.core.runtime import FRuntime
    from francis_suite.core.variables import FNodeVariable
    from francis_suite.core.session import SessionStatus

    path = Path(args.workflow)

    if not path.exists():
        print(f"[ERROR] Workflow file not found: '{path}'")
        sys.exit(1)

    # Parse --var KEY=VALUE pairs
    variables: dict[str, str] = {}
    for var in args.var:
        if "=" not in var:
            print(f"[ERROR] Invalid --var format: '{var}'. Use KEY=VALUE")
            sys.exit(1)
        key, value = var.split("=", 1)
        variables[key.strip()] = value.strip()

    # Run workflow
    parser = FParser()
    runtime = FRuntime()

    root = parser.parse_file(path)
    session = runtime.run(
        root,
        workflow_name=path.stem,
    )

    if session.status == SessionStatus.COMPLETED:
        print(f"\n[OK] Workflow '{path.stem}' completed successfully.")
    else:
        print(f"\n[FAILED] Workflow '{path.stem}' failed.")
        if session.error:
            print(f"[ERROR] {session.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
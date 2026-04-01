"""
francis_suite/cli.py

Francis Suite CLI — command line interface.
Allows running workflows from the terminal.

Usage:
    francis-suite run workflow.xml
    francis-suite run workflow.xml --param ciudad=santiago --param paginas=10
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
        description="Francis Suite — Universal data extraction framework",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="Francis Suite 0.1.0",
    )

    subparsers = parser.add_subparsers(dest="command")

    # francis-suite schema [--out DIR]
    schema_parser = subparsers.add_parser(
        "schema",
        help="Write XSD and JSON manifest for registered workflow hands",
    )
    schema_parser.add_argument(
        "--out",
        type=Path,
        default=Path("schema"),
        help="Output directory (default: ./schema)",
    )
    schema_parser.add_argument(
        "--version",
        dest="schema_version",
        default=None,
        help="Version string in the JSON manifest (default: package version)",
    )

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
        "--param",
        action="append",
        metavar="KEY=VALUE",
        help="Inject a variable into the workflow context (can be used multiple times)",
        default=[],
    )

    args = parser.parse_args()

    if args.command == "run":
        _run(args)
    elif args.command == "schema":
        _schema(args)
    else:
        parser.print_help()


def _schema_version_default() -> str:
    try:
        from importlib.metadata import version as pkg_version

        return pkg_version("francis-suite")
    except Exception:
        return "0.1.0"


def _schema(args) -> None:
    from francis_suite.schema_gen import write_schemas

    ver = args.schema_version if args.schema_version is not None else _schema_version_default()
    xsd_path, json_path = write_schemas(args.out, version=ver)
    print(f"[OK] Wrote {xsd_path.as_posix()}")
    print(f"[OK] Wrote {json_path.as_posix()}")


def _run(args) -> None:
    from francis_suite.core.parser import FParser
    from francis_suite.core.runtime import FRuntime
    from francis_suite.core.session import FrancisSession, SessionStatus
    from francis_suite.core.variables import FNodeVariable

    path = Path(args.workflow)

    if not path.exists():
        print(f"[ERROR] Workflow file not found: '{path}'")
        sys.exit(1)

    # Parse --param KEY=VALUE pairs
    params: dict[str, str] = {}
    for param in args.param:
        if "=" not in param:
            print(f"[ERROR] Invalid --param format: '{param}'. Use KEY=VALUE")
            sys.exit(1)
        key, value = param.split("=", 1)
        key   = key.strip()
        value = value.strip()
        if not key:
            print(f"[ERROR] Invalid --param format: key cannot be empty. Use KEY=VALUE")
            sys.exit(1)
        params[key] = value

    # Parse workflow
    root = FParser().parse_file(path)

    # Build session and inject --param variables before running
    session = FrancisSession(workflow_name=path.stem)

    if params:
        try:
            for key, value in params.items():
                session.context.set_shared_box(key, FNodeVariable(value))
            print("[PARAMS] Context variables loaded.")
        except Exception as e:
            print(f"[ERROR] Failed to load context variables: {e}")
            sys.exit(1)

    # Run workflow using the pre-built session
    runtime = FRuntime()
    session = runtime.run_session(root, session)

    if session.status == SessionStatus.COMPLETED:
        print(f"\n[OK] Workflow '{path.stem}' completed successfully.")
        if session.duration:
            print(f"[OK] Duration: {session.duration:.2f}s")
    else:
        print(f"\n[FAILED] Workflow '{path.stem}' failed.")
        if session.error:
            print(f"[ERROR] {session.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()

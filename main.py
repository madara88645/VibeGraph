"""VibeGraph CLI entry point.

Usage:
    python main.py analyze <path>   Analyze a Python project and export graph data.
    python main.py export           Re-export the last analysis to graph_data.json.
    python main.py start            Start the FastAPI web server (default: http://localhost:8000).
"""

import sys
import argparse

from analyst.analyzer import CodeAnalyzer
from analyst.exporter import export_graph


def cmd_analyze(args: argparse.Namespace) -> None:
    analyzer = CodeAnalyzer(args.path)
    analyzer.analyze()
    export_graph(analyzer.graph, output_path="explorer/public/graph_data.json")
    print(f"[VibeGraph] Analysis complete. Graph written to explorer/public/graph_data.json")


def cmd_export(_args: argparse.Namespace) -> None:
    export_graph(output_path="explorer/public/graph_data.json")
    print("[VibeGraph] Export complete.")


def cmd_start(args: argparse.Namespace) -> None:
    import uvicorn
    uvicorn.run(
        "serve:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vibegraph",
        description="VibeGraph — AI-powered code visualization & learning system",
    )
    sub = parser.add_subparsers(dest="command")

    # analyze
    p_analyze = sub.add_parser("analyze", help="Analyze a Python codebase")
    p_analyze.add_argument("path", help="Path to the Python project root")
    p_analyze.set_defaults(func=cmd_analyze)

    # export
    p_export = sub.add_parser("export", help="Re-export last analysis to graph_data.json")
    p_export.set_defaults(func=cmd_export)

    # start
    p_start = sub.add_parser("start", help="Start the VibeGraph web server")
    p_start.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    p_start.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    p_start.add_argument("--reload", action="store_true", help="Enable auto-reload")
    p_start.set_defaults(func=cmd_start)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()

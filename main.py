import argparse
from analyst.analyzer import CodeAnalyzer
from teacher.basic_reporter import BasicTeacher
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()


def main():
    parser = argparse.ArgumentParser(description="Vibe Learning System - Code Analyzer")
    parser.add_argument(
        "command", choices=["analyze", "export", "start"], help="Command to run"
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target file or directory to analyze (default: current directory)",
    )
    parser.add_argument(
        "--out",
        help="Output path for export (default: explorer/public/graph_data.json)",
        default="explorer/public/graph_data.json",
    )

    args = parser.parse_args()

    if args.command == "analyze":
        console.print(Panel(f"[bold green]Analyzing {args.target}...[/bold green]"))

        # 1. Analyze
        analyzer = CodeAnalyzer()
        result = analyzer.analyze_file(args.target)

        if "error" in result:
            console.print(f"[bold red]Error:[/bold red] {result['error']}")
            return

        graph = result["graph"]

        # 2. Teach
        teacher = BasicTeacher()
        lesson_content = teacher.generate_lesson(graph, args.target)

        # 3. Display
        console.print(
            Panel(Markdown(lesson_content), title="Vibe Lesson", border_style="blue")
        )

    elif args.command == "export":
        console.print(
            Panel(f"[bold green]Exporting analysis of {args.target}...[/bold green]")
        )

        from analyst.exporter import GraphExporter
        import os

        # 1. Analyze
        analyzer = CodeAnalyzer()
        result = analyzer.analyze_file(args.target)

        if "error" in result:
            console.print(f"[bold red]Error:[/bold red] {result['error']}")
            return

        graph = result["graph"]

        # 2. Export
        exporter = GraphExporter()

        output_path = args.out
        exporter.export_to_react_flow(graph, output_path)

        console.print(f"[bold blue]Graph exported to:[/bold blue] {output_path}")

    elif args.command == "start":
        from analyst.exporter import GraphExporter
        import os
        import subprocess
        import webbrowser
        import uvicorn
        from serve import app
        import shutil

        target = args.target if args.target else "."

        # 1. Analyze & Export
        analyzer = CodeAnalyzer()
        result = analyzer.analyze_file(target)
        if "error" in result:
            console.print(f"[bold red]Analysis Error:[/bold red] {result['error']}")
            return

        graph = result["graph"]
        exporter = GraphExporter()

        # Output to public (for dev) and dist (for prod)
        output_dir = "explorer/public"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        public_graph_path = os.path.join(output_dir, "graph_data.json")
        exporter.export_to_react_flow(graph, public_graph_path)

        # 2. Check Frontend Build
        dist_dir = os.path.join("explorer", "dist")
        dist_graph_path = os.path.join(dist_dir, "graph_data.json")

        # Build if dist is missing or empty
        if not os.path.exists(dist_dir) or not os.listdir(dist_dir):
            try:
                npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
                # Install deps if needed
                if not os.path.exists(os.path.join("explorer", "node_modules")):
                    subprocess.run([npm_cmd, "install"], cwd="explorer", check=True)

                subprocess.run([npm_cmd, "run", "build"], cwd="explorer", check=True)
            except subprocess.CalledProcessError:
                return
        else:
            if os.path.exists(dist_dir):
                shutil.copy(public_graph_path, dist_graph_path)

        # 3. Start Server
        url = "http://localhost:8000"

        webbrowser.open(url)
        uvicorn.run(app, host="127.0.0.1", port=8000)  # nosec B104


if __name__ == "__main__":
    main()

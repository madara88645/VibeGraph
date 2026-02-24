import argparse
from analyst.analyzer import CodeAnalyzer
from teacher.basic_reporter import BasicTeacher
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

def main():
    parser = argparse.ArgumentParser(description="Vibe Learning System - Code Analyzer")
    parser.add_argument("command", choices=["analyze", "export", "start"], help="Command to run")
    parser.add_argument("target", nargs='?', default=".", help="Target file or directory to analyze (default: current directory)")
    parser.add_argument("--out", help="Output path for export (default: explorer/public/graph_data.json)", default="explorer/public/graph_data.json")
    
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
        console.print(Panel(Markdown(lesson_content), title="Vibe Lesson", border_style="blue"))

    elif args.command == "export":
        console.print(Panel(f"[bold green]Exporting analysis of {args.target}...[/bold green]"))
        
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
        exporter.export_to_json(graph, output_path)
        
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
        # console.print(Panel(f"[bold green]Starting Vibe Learning System on {target}...[/bold green]"))

        # 1. Analyze & Export
        # console.print("[dim]Step 1: Analyzing code...[/dim]")
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
        # console.print(f"   [green]✔[/green] Graph analyzed and exported.")

        # 2. Check Frontend Build
        dist_dir = os.path.join("explorer", "dist")
        dist_graph_path = os.path.join(dist_dir, "graph_data.json")
        
        # Build if dist is missing or empty
        if not os.path.exists(dist_dir) or not os.listdir(dist_dir):
            # console.print("[dim]Step 2: Building Frontend...[/dim]")
            try:
                # Install deps if needed
                if not os.path.exists(os.path.join("explorer", "node_modules")):
                     # console.print("   Installing dependencies...")
                     subprocess.run("npm install", cwd="explorer", shell=True, check=True)
                
                # console.print("   Building React app...")
                subprocess.run("npm run build", cwd="explorer", shell=True, check=True)
                # console.print("   [green]✔[/green] Build complete.")
            except subprocess.CalledProcessError:
                # console.print("[bold red]Frontend build failed.[/bold red]")
                return
        else:
            # console.print("[dim]Step 2: Frontend build found. Syncing graph data...[/dim]")
            if os.path.exists(dist_dir):
                shutil.copy(public_graph_path, dist_graph_path)
                # console.print(f"   [green]✔[/green] Synced graph data.")

        # 3. Start Server
        # console.print("[dim]Step 3: Launching Interface...[/dim]")
        url = "http://localhost:8000"
        # console.print(f"[bold cyan]Click to open: {url}[/bold cyan]")
        
        webbrowser.open(url)
        uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()

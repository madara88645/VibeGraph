# Vibe Learning System

A system to turn "vibe coding" sessions into interactive learning experiences.
It analyzes code changes, generates call graphs, and uses LLMs to explain *what* changed and *why*, helping users learn from the AI's speed.

## Architecture

- **Observer (VS Code Ext)**: Collects session data (diffs, logs).
- **Analyst (Python)**: Parses code, builds call graphs (`networkx`), identifies logical changes.
- **Teacher (LLM Agent)**: Generates lessons, cheat sheets, and quizzes based on analysis.
- **Explorer (React)**: Interactive web UI to explore the code evolution.

## Setup (Phase 1 - Local Python)

1.  It is recommended to use a virtual environment.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the analyzer on a target file/folder:
    ```bash
    python main.py analyze <path_to_python_file_or_dir>
    ```

"""
AiAgentsTaskSolvingBenchmark
Praca Inżynierska: Badanie Skuteczności Systemów Wieloagentowych (Solo ReAct vs Multi-Agent Swarm)
Autor: Wiktor Kozakowski
"""

import sys
import os

# Ensure UTF-8 output on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.cli import app
from src.runner import BenchmarkRunner

if __name__ == "__main__":
    # If arguments are passed (e.g. 'run', 'ui', 'report', '--help'), use Typer CLI
    if len(sys.argv) > 1:
        app()
    else:
        # Default fallback for PyCharm / direct execution: run the benchmark
        runner = BenchmarkRunner()
        runner.run()

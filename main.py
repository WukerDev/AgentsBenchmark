import sys
import os

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.cli import app
from src.runner import BenchmarkRunner

if __name__ == "__main__":
    if len(sys.argv) > 1:
        app()
    else:
        runner = BenchmarkRunner()
        runner.run()

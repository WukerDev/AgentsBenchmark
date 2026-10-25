from __future__ import annotations
import sys
import subprocess
from pathlib import Path
from typing import Optional, List
import typer
import pandas as pd
from rich.console import Console

from src.runner import BenchmarkRunner
from src.config import config, BASE_DIR
from src.evaluation.statistics import compute_benchmark_statistics
from src.storage.checkpoint import CheckpointManager
from src.storage.excel_exporter import ExcelBenchmarkExporter
from src.storage.latex_exporter import LatexExporter
from src.visualization.plots import BenchmarkVisualizer

app = typer.Typer(
    help="AiAgents Task Solving Benchmark - Narzędzie Badawcze dla Pracy Inżynierskiej",
    add_completion=False
)
console = Console()

@app.command()
def run(
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Dostawca LLM: ollama, groq, openai, openrouter"),
    tasks: Optional[str] = typer.Option(None, "--tasks", "-t", help="Lista ID zadań rozdzielona przecinkami (np. task_01_helium,task_02_monty_hall_100)"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filtruj zadania wg kategorii (np. math_probability, sysadmin_security)"),
    resume: bool = typer.Option(True, "--resume/--no-resume", help="Wznawiaj od ostatniego checkpointu bez powtarzania zrobionych zadań"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Szybki test potoku bez odpytywania LLM (mock)")
):
    """
    Uruchamia benchmark porównawczy Solo ReAct vs Multi-Agent Swarm.
    """
    task_list = [t.strip() for t in tasks.split(",")] if tasks else None
    runner = BenchmarkRunner(
        provider=provider,
        task_filter=task_list,
        category_filter=category,
        resume=resume,
        dry_run=dry_run
    )
    runner.run()

@app.command()
def ui():
    """
    Uruchamia interaktywny interfejs graficzny Web (Streamlit Dashboard).
    """
    app_path = BASE_DIR / "src" / "ui" / "app.py"
    console.print(f"[bold green]Uruchamiam graficzny dashboard badawczy:[/bold green] [underline]http://localhost:8501[/underline]")
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])

@app.command()
def report():
    """
    Generuje raporty Excel oraz tabele LaTeX na podstawie istniejącego pliku checkpointów.
    """
    chk_path = BASE_DIR / config.system.checkpoint_file
    if not chk_path.exists():
        console.print(f"[bold red]Błąd:[/bold red] Plik checkpointu {chk_path} nie istnieje!")
        raise typer.Exit(code=1)

    chk_mgr = CheckpointManager(chk_path)
    records = list(chk_mgr.load_completed_tasks().values())
    if not records:
        console.print("[yellow]Brak zapisanych rekordów w pliku checkpointu.[/yellow]")
        return

    df = pd.DataFrame(records)
    stats = compute_benchmark_statistics(df)

    excel_path = BASE_DIR / config.system.excel_output
    reports_dir = BASE_DIR / "results" / "reports"

    ExcelBenchmarkExporter.export(excel_path, df, stats)
    LatexExporter.export(reports_dir, df, stats)
    console.print(f"[bold green][OK] Zaktualizowano arkusz Excel:[/bold green] {excel_path}")
    console.print(f"[bold green][OK] Zaktualizowano tabele LaTeX w:[/bold green] {reports_dir}")

@app.command()
def plot(show: bool = typer.Option(False, "--show", help="Wyświetl okna wykresów po wygenerowaniu")):
    """
    Generuje wykresy publikacyjne (PNG 300 DPI) na podstawie wyników.
    """
    chk_path = BASE_DIR / config.system.checkpoint_file
    if not chk_path.exists():
        console.print(f"[bold red]Błąd:[/bold red] Plik checkpointu {chk_path} nie istnieje!")
        raise typer.Exit(code=1)

    chk_mgr = CheckpointManager(chk_path)
    records = list(chk_mgr.load_completed_tasks().values())
    if not records:
        console.print("[yellow]Brak rekordów do narysowania wykresów.[/yellow]")
        return

    df = pd.DataFrame(records)
    figures_dir = BASE_DIR / "results" / "figures"
    BenchmarkVisualizer.generate_all_plots(df, figures_dir, show=show)
    console.print(f"[bold green][OK] Wygenerowano wykresy w:[/bold green] {figures_dir}")

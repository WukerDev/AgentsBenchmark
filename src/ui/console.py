from __future__ import annotations
from typing import Optional
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.text import Text
from rich import box

console = Console()

class BenchmarkLiveConsole:
    """
    Rich live terminal dashboard that displays real-time execution status
    without spamming the console with scrolling logs.
    """
    def __init__(self, total_tasks: int):
        self.total_tasks = total_tasks
        self.completed_tasks = 0
        self.current_task_id = "Inicjalizacja..."
        self.current_category = ""
        self.current_step = "Gotowy do startu"
        self.results_table = self._init_table()

    def _init_table(self) -> Table:
        table = Table(
            title="Podsumowanie Przebiegu Badania",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
            expand=True
        )
        table.add_column("ID Zadania", style="dim", width=22)
        table.add_column("Kategoria", width=18)
        table.add_column("Solo", justify="center", width=8)
        table.add_column("Multi (Fin)", justify="center", width=12)
        table.add_column("Zwycięzca", justify="center", width=12)
        table.add_column("Czas Solo", justify="right", width=10)
        table.add_column("Czas Multi", justify="right", width=10)
        table.add_column("Koszt USD", justify="right", width=12)
        return table

    def set_task(self, task_id: str, category: str, index: int):
        self.current_task_id = task_id
        self.current_category = category
        self.current_step = f"Zadanie [{index + 1}/{self.total_tasks}]: Rozpoczynam..."

    def set_step(self, step_text: str):
        self.current_step = step_text

    def add_completed_row(
        self,
        task_id: str,
        category: str,
        score_solo: float,
        score_multi: float,
        solo_time: float,
        multi_time: float,
        cost: float
    ):
        self.completed_tasks += 1

        if score_multi > score_solo:
            winner = "[bold green]Multi[/bold green]"
        elif score_solo > score_multi:
            winner = "[bold yellow]Solo[/bold yellow]"
        else:
            winner = "[dim]Remis[/dim]"

        s_solo_str = f"[bold]{score_solo:.0f}[/bold]" if score_solo >= 75 else f"{score_solo:.0f}"
        s_multi_str = f"[bold green]{score_multi:.0f}[/bold green]" if score_multi >= 75 else f"{score_multi:.0f}"

        self.results_table.add_row(
            task_id,
            category,
            s_solo_str,
            s_multi_str,
            winner,
            f"{solo_time:.1f}s",
            f"{multi_time:.1f}s",
            f"${cost:.4f}"
        )

    def get_renderable(self) -> Panel:
        progress_pct = (self.completed_tasks / max(self.total_tasks, 1)) * 100
        status_text = Text.assemble(
            ("Status: ", "bold white"),
            (f"{self.current_step}\n", "yellow"),
            ("Postęp: ", "bold white"),
            (f"{self.completed_tasks}/{self.total_tasks} ({progress_pct:.0f}%)\n", "green"),
            ("Zadanie: ", "bold white"),
            (f"{self.current_task_id} ", "bold magenta"),
            (f"[{self.current_category}]", "dim")
        )
        return Panel(
            status_text,
            title="[bold blue]AiAgents Task Solving Benchmark[/bold blue]",
            border_style="bright_blue",
            box=box.ROUNDED
        )

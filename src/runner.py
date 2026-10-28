from __future__ import annotations
import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
from rich.live import Live

from src.config import config, BASE_DIR, CONFIG_DIR, RESULTS_DIR
from src.agents.solo_agent import SoloAgentRunner
from src.agents.group_chat import MultiAgentSwarmRunner, load_agents_config
from src.evaluation.ground_truth import GroundTruthVerifier
from src.evaluation.jury import LLMJury
from src.evaluation.statistics import compute_benchmark_statistics
from src.storage.checkpoint import CheckpointManager
from src.storage.excel_exporter import ExcelBenchmarkExporter
from src.storage.latex_exporter import LatexExporter
from src.storage.thesis_chapter_generator import ThesisChapterGenerator
from src.evaluation.failure_taxonomy import FailureTaxonomy
from src.hardware.telemetry import HardwareProfiler
from src.storage.html_reporter import HTMLReporter
from src.visualization.plots import BenchmarkVisualizer
from src.ui.console import BenchmarkLiveConsole, console

class BenchmarkRunner:
    def __init__(
        self,
        provider: Optional[str] = None,
        task_filter: Optional[List[str]] = None,
        category_filter: Optional[str] = None,
        difficulty_filter: Optional[str] = None,
        resume: bool = True,
        dry_run: bool = False,
        no_live: bool = False
    ):
        self.provider = provider or config.system.default_provider
        self.task_filter = task_filter
        self.category_filter = category_filter
        self.difficulty_filter = difficulty_filter
        self.resume = resume
        self.dry_run = dry_run
        self.no_live = no_live

        self.checkpoint_path = BASE_DIR / config.system.checkpoint_file
        self.excel_path = BASE_DIR / config.system.excel_output
        self.reports_dir = RESULTS_DIR / "reports"
        self.figures_dir = RESULTS_DIR / "figures"
        self.logs_dir = RESULTS_DIR / "logs"

        self.checkpoint_mgr = CheckpointManager(self.checkpoint_path)
        self.tasks = self._load_tasks()

    def _load_tasks(self) -> List[Dict[str, Any]]:
        tasks_file = CONFIG_DIR / "tasks.json"
        if not tasks_file.exists():
            tasks_file = BASE_DIR / "tasks.json"

        with open(tasks_file, "r", encoding="utf-8") as f:
            all_tasks = json.load(f)

        if self.category_filter:
            all_tasks = [t for t in all_tasks if t.get("category") == self.category_filter]

        if self.difficulty_filter:
            all_tasks = [t for t in all_tasks if t.get("difficulty") == self.difficulty_filter]

        if self.task_filter:
            all_tasks = [t for t in all_tasks if t["id"] in self.task_filter]

        return all_tasks

    def run(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        completed_records = self.checkpoint_mgr.load_completed_tasks() if self.resume else {}

        remaining_tasks = [t for t in self.tasks if t["id"] not in completed_records]
        total_tasks_count = len(self.tasks)

        console.print(f"[bold cyan]Rozpoczynam badanie:[/bold cyan] {len(remaining_tasks)} zadań do wykonania (ukończono wcześniej: {len(completed_records)})")
        console.print(f"[dim]Dostawca LLM:[/dim] [magenta]{self.provider}[/magenta] | [dim]Tryb wznawiania:[/dim] {self.resume}")

        live_ui = BenchmarkLiveConsole(total_tasks=total_tasks_count)

        for tid, row in completed_records.items():
            live_ui.add_completed_row(
                tid,
                row.get("category", "ogólne"),
                row.get("score_solo", 0),
                row.get("score_multi_final", 0),
                row.get("solo_time", 0),
                row.get("multi_time", 0),
                row.get("multi_cost_usd", 0)
            )

        all_results = list(completed_records.values())

        solo_runner = SoloAgentRunner(provider=self.provider)
        multi_runner = MultiAgentSwarmRunner(provider=self.provider)
        jury = LLMJury(provider=self.provider)

        with Live(live_ui.get_renderable(), refresh_per_second=4, console=console) as live:
            for idx, task in enumerate(self.tasks):
                task_id = task["id"]
                category = task.get("category", "general")
                difficulty = task.get("difficulty", "medium")
                required_tool = task.get("required_tool", "none")

                if task_id in completed_records:
                    continue

                live_ui.set_task(task_id, category, idx)
                live.update(live_ui.get_renderable())
                try:

                    if self.dry_run:
                        time.sleep(0.3)
                        solo_res = {
                            "final_answer": "Dry run mock answer", "generation_time": 0.1, "tool_time": 0.0,
                            "total_time": 0.1, "tokens": 100, "cost": 0.0001, "turns": 1,
                            "tool_counts": {"python": 1}, "tool_error_count": 0, "chat_history": "Mock history"
                        }
                        group_res = {
                            "final_answer": "Dry run mock answer", "snapshot_5": "Mock 5", "snapshot_10": "Mock 10",
                            "generation_time": 0.2, "tool_time": 0.0, "total_time": 0.2, "tokens": 300,
                            "cost": 0.0003, "turns": 3, "agent_path": "analyst -> solver -> secretary",
                            "role_counts": {"analyst": 1, "solver": 1, "secretary": 1},
                            "tool_counts": {"python": 1}, "tool_error_count": 0, "chat_history": "Mock swarm history"
                        }
                        scores = {
                            "score_solo": 80.0, "score_multi_5": 70.0, "score_multi_10": 85.0, "score_multi_final": 95.0,
                            "hallucination_solo": False, "hallucination_multi": False, "jury_reasons": "[Mock Jury]: Poprawne",
                            "judge_total_cost": 0.0001, "jury_std_dev": 2.5
                        }
                    else:
                        live_ui.set_step(f"Zadanie [{idx+1}/{total_tasks_count}]: Uruchamiam Solo ReAct...")
                        live.update(live_ui.get_renderable())
                        solo_res = solo_runner.run(task["query"])

                        live_ui.set_step(f"Zadanie [{idx+1}/{total_tasks_count}]: Uruchamiam Multi-Agent Swarm...")
                        live.update(live_ui.get_renderable())
                        group_res = multi_runner.run(task["query"])

                        live_ui.set_step(f"Zadanie [{idx+1}/{total_tasks_count}]: Ewaluacja Sędziowska...")
                        live.update(live_ui.get_renderable())
                        jury_eval = jury.evaluate(
                            task["query"],
                            task.get("expected_answer", ""),
                            solo_res["final_answer"],
                            group_res["snapshot_5"],
                            group_res["snapshot_10"],
                            group_res["final_answer"]
                        )
                        scores = {
                            "score_solo": jury_eval.score_solo,
                            "score_multi_5": jury_eval.score_multi_5,
                            "score_multi_10": jury_eval.score_multi_10,
                            "score_multi_final": jury_eval.score_multi_final,
                            "hallucination_solo": jury_eval.hallucination_solo,
                            "hallucination_multi": jury_eval.hallucination_multi,
                            "jury_reasons": jury_eval.jury_reasons,
                            "judge_total_cost": jury_eval.judge_total_cost,
                            "jury_std_dev": jury_eval.jury_std_dev
                        }

                    gt_solo_score, gt_solo_ok, gt_solo_expl = GroundTruthVerifier.verify(task_id, solo_res["final_answer"])
                    gt_multi_score, gt_multi_ok, gt_multi_expl = GroundTruthVerifier.verify(task_id, group_res["final_answer"])

                    multi_total_cost = group_res["cost"] + scores.get("judge_total_cost", 0.0)
                    debate_gain = round(scores.get("score_multi_final", 0.0) - scores.get("score_multi_5", 0.0), 1)

                    row_record = {
                        "task_id": task_id,
                        "category": category,
                        "difficulty": difficulty,
                        "required_tool": required_tool,
                        "score_solo": scores.get("score_solo", 0.0),
                        "score_multi_5": scores.get("score_multi_5", 0.0),
                        "score_multi_10": scores.get("score_multi_10", 0.0),
                        "score_multi_final": scores.get("score_multi_final", 0.0),
                        "debate_gain": debate_gain,
                        "gt_solo_score": gt_solo_score,
                        "gt_multi_score": gt_multi_score,
                        "hallucination_solo": scores.get("hallucination_solo", False),
                        "hallucination_multi": scores.get("hallucination_multi", False),
                        "solo_time": solo_res["total_time"],
                        "solo_generation_time": solo_res["generation_time"],
                        "solo_tool_time": solo_res["tool_time"],
                        "multi_time": group_res["total_time"],
                        "multi_generation_time": group_res["generation_time"],
                        "multi_tool_time": group_res["tool_time"],
                        "solo_tokens": solo_res["tokens"],
                        "multi_tokens": group_res["tokens"],
                        "solo_cost_usd": solo_res["cost"],
                        "multi_cost_usd": multi_total_cost,
                        "solo_turns": solo_res["turns"],
                        "multi_turns": group_res["turns"],
                        "solo_tools_used": sum(solo_res.get("tool_counts", {}).values()),
                        "multi_tools_used": sum(group_res.get("tool_counts", {}).values()),
                        "multi_tool_errors": group_res.get("tool_error_count", 0),
                        "jury_std_dev": scores.get("jury_std_dev", 0.0),
                        "agent_path": group_res.get("agent_path", ""),
                        "jury_reason": scores.get("jury_reasons", ""),
                        "failure_taxonomy": FailureTaxonomy.classify_record({"score_multi_final": scores.get("score_multi_final", 0.0), "gt_multi_score": gt_multi_score, "multi_turns": group_res.get("turns", 0), "multi_tool_errors": group_res.get("tool_error_count", 0), "hallucination_multi": scores.get("hallucination_multi", False), "agent_path": group_res.get("agent_path", "")}),
                        "gpu_vram_mb": HardwareProfiler.get_gpu_status().get("used_vram_mb", 0),
                        "gpu_util_pct": HardwareProfiler.get_gpu_status().get("utilization_pct", 0)
                    }

                    self.checkpoint_mgr.save_task_result(row_record)
                    all_results.append(row_record)

                    live_ui.add_completed_row(
                        task_id,
                        category,
                        row_record["score_solo"],
                        row_record["score_multi_final"],
                        row_record["solo_time"],
                        row_record["multi_time"],
                        row_record["multi_cost_usd"]
                    )
                    live.update(live_ui.get_renderable())

                    HTMLReporter.generate_task_log(
                        self.logs_dir / f"log_{timestamp}_{task_id}.html",
                        task_id,
                        task["query"],
                        task.get("expected_answer", ""),
                        solo_res,
                        group_res,
                        scores
                    )
                except Exception as task_err:
                    console.print(f"[bold red][BŁĄD ZADANIA {task_id}]:[/bold red] {task_err}")
                    error_record = {
                        "task_id": task_id,
                        "category": category,
                        "difficulty": difficulty,
                        "required_tool": required_tool,
                        "score_solo": 0.0,
                        "score_multi_5": 0.0,
                        "score_multi_10": 0.0,
                        "score_multi_final": 0.0,
                        "debate_gain": 0.0,
                        "gt_solo_score": 0,
                        "gt_multi_score": 0,
                        "hallucination_solo": False,
                        "hallucination_multi": False,
                        "solo_time": 0.0,
                        "solo_generation_time": 0.0,
                        "solo_tool_time": 0.0,
                        "multi_time": 0.0,
                        "multi_generation_time": 0.0,
                        "multi_tool_time": 0.0,
                        "solo_tokens": 0,
                        "multi_tokens": 0,
                        "solo_cost_usd": 0.0,
                        "multi_cost_usd": 0.0,
                        "solo_turns": 0,
                        "multi_turns": 0,
                        "solo_tools_used": 0,
                        "multi_tools_used": 0,
                        "multi_tool_errors": 1,
                        "jury_std_dev": 0.0,
                        "agent_path": "ERROR",
                        "jury_reason": f"Błąd wykonania: {str(task_err)}",
                        "failure_taxonomy": "Błąd Wykonania Kodu / Narzędzia (Tool Execution Failure)",
                        "gpu_vram_mb": HardwareProfiler.get_gpu_status().get("used_vram_mb", 0),
                        "gpu_util_pct": HardwareProfiler.get_gpu_status().get("utilization_pct", 0)
                    }
                    self.checkpoint_mgr.save_task_result(error_record)
                    all_results.append(error_record)
                    live_ui.add_completed_row(task_id, category, 0.0, 0.0, 0.0, 0.0, 0.0)
                    live.update(live_ui.get_renderable())

        console.print(live_ui.results_table)

        df_final = pd.DataFrame(all_results)
        stats = compute_benchmark_statistics(df_final)

        ExcelBenchmarkExporter.export(self.excel_path, df_final, stats)
        console.print(f"[bold green][OK] Zapisano arkusz Excel:[/bold green] [underline]{self.excel_path}[/underline]")

        LatexExporter.export(self.reports_dir, df_final, stats)
        console.print(f"[bold green][OK] Wygenerowano tabele LaTeX w:[/bold green] [underline]{self.reports_dir}[/underline]")

        ThesisChapterGenerator.generate(self.reports_dir, df_final, stats)
        console.print(f"[bold green][OK] Wygenerowano szkic rozdziału magisterskiego w:[/bold green] [underline]{self.reports_dir}[/underline]")

        BenchmarkVisualizer.generate_all_plots(df_final, self.figures_dir, show=False)
        console.print(f"[bold green][OK] Wygenerowano wykresy badawcze w:[/bold green] [underline]{self.figures_dir}[/underline]")

        console.print(f"[bold green]Badanie zakończone sukcesem![/bold green] Średni wynik Solo: [bold]{stats.get('solo_mean', 0)}[/bold] | Multi: [bold]{stats.get('multi_mean', 0)}[/bold]")

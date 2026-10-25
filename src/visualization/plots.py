from __future__ import annotations
from pathlib import Path
from typing import Optional
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# Set publication style
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "figure.titlesize": 16,
    "figure.titleweight": "bold"
})

class BenchmarkVisualizer:
    @classmethod
    def generate_all_plots(cls, df: pd.DataFrame, output_dir: Path, show: bool = False):
        if df.empty:
            return
        output_dir.mkdir(parents=True, exist_ok=True)

        cls.plot_overview_dashboard(df, output_dir / "dashboard_porownawczy.png")
        cls.plot_category_comparison(df, output_dir / "kategorie_porownanie.png")
        cls.plot_turn_evolution(df, output_dir / "ewolucja_tur.png")
        cls.plot_pareto_cost_score(df, output_dir / "pareto_koszt_wynik.png")

        if show:
            plt.show()

    @classmethod
    def plot_overview_dashboard(cls, df: pd.DataFrame, save_path: Path):
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle("Podsumowanie Badania: Solo Agent (ReAct) vs Multi-Agent Swarm", fontsize=15)

        # 1. Scores Comparison
        solo_mean = df["score_solo"].mean()
        multi_mean = df["score_multi_final"].mean()
        ax = axes[0, 0]
        bars = ax.bar(["Solo (ReAct)", "Multi-Agent Swarm"], [solo_mean, multi_mean], color=["#718096", "#38A169"], width=0.5)
        ax.set_title("Średni Wynik Punktowy (0-100)")
        ax.set_ylim(0, 105)
        for b in bars:
            h = b.get_height()
            ax.text(b.get_x() + b.get_width()/2., h + 2, f"{h:.1f}", ha="center", va="bottom", fontweight="bold")

        # 2. Time Breakdown: LLM Generation vs Tools
        ax2 = axes[0, 1]
        solo_gen = df["solo_generation_time"].mean() if "solo_generation_time" in df else 0
        multi_gen = df["multi_generation_time"].mean() if "multi_generation_time" in df else 0
        solo_tool = df["solo_tool_time"].mean() if "solo_tool_time" in df else 0
        multi_tool = df["multi_tool_time"].mean() if "multi_tool_time" in df else 0

        p1 = ax2.bar(["Solo", "Multi-Agent"], [solo_gen, multi_gen], label="Inference LLM (s)", color="#4A5568", width=0.5)
        p2 = ax2.bar(["Solo", "Multi-Agent"], [solo_tool, multi_tool], bottom=[solo_gen, multi_gen], label="Narzędzia (I/O, Python) (s)", color="#E53E3E", width=0.5)
        ax2.set_title("Średni Czas Odpowiedzi: Inferencja vs Narzędzia")
        ax2.set_ylabel("Sekundy (s)")
        ax2.legend()

        # 3. Cost per Task (USD)
        ax3 = axes[1, 0]
        solo_cost = df["solo_cost_usd"].mean() if "solo_cost_usd" in df else 0
        multi_cost = df["multi_cost_usd"].mean() if "multi_cost_usd" in df else 0
        bars3 = ax3.bar(["Solo", "Multi-Agent"], [solo_cost, multi_cost], color=["#718096", "#D69E2E"], width=0.5)
        ax3.set_title("Średni Koszt Zapytania (USD)")
        ax3.set_ylabel("USD")
        for b in bars3:
            h = b.get_height()
            ax3.text(b.get_x() + b.get_width()/2., h + 0.0001, f"${h:.4f}", ha="center", va="bottom", fontweight="bold")

        # 4. Token Efficiency (Score per 1k tokens)
        ax4 = axes[1, 1]
        solo_tok = df["solo_tokens"].mean()
        multi_tok = df["multi_tokens"].mean()
        eff_solo = (solo_mean / (solo_tok / 1000.0)) if solo_tok > 0 else 0
        eff_multi = (multi_mean / (multi_tok / 1000.0)) if multi_tok > 0 else 0

        bars4 = ax4.bar(["Solo", "Multi-Agent"], [eff_solo, eff_multi], color=["#718096", "#805AD5"], width=0.5)
        ax4.set_title("Efektywność Tokenowa (Punkty / 1k Tokenów)")
        ax4.set_ylabel("Pkt / 1k Tok")
        for b in bars4:
            h = b.get_height()
            ax4.text(b.get_x() + b.get_width()/2., h + 0.5, f"{h:.2f}", ha="center", va="bottom", fontweight="bold")

        plt.tight_layout()
        fig.savefig(save_path, dpi=300)
        plt.close(fig)

    @classmethod
    def plot_turn_evolution(cls, df: pd.DataFrame, save_path: Path):
        if "score_multi_5" not in df or "score_multi_10" not in df:
            return

        fig, ax = plt.subplots(figsize=(8, 5))
        stages = ["Solo ReAct", "Multi Tura 5", "Multi Tura 10", "Multi Finał"]
        vals = [
            df["score_solo"].mean(),
            df["score_multi_5"].mean(),
            df["score_multi_10"].mean(),
            df["score_multi_final"].mean()
        ]

        ax.plot(stages, vals, marker="o", markersize=8, linewidth=2.5, color="#3182CE")
        ax.set_title("Progres Jakości Odpowiedzi w Czasie Dyskusji")
        ax.set_ylabel("Średni Wynik Punktowy (0-100)")
        ax.set_ylim(0, 105)

        for i, v in enumerate(vals):
            ax.annotate(f"{v:.1f}", (stages[i], v + 2.5), ha="center", fontweight="bold")

        plt.tight_layout()
        fig.savefig(save_path, dpi=300)
        plt.close(fig)

    @classmethod
    def plot_category_comparison(cls, df: pd.DataFrame, save_path: Path):
        if "category" not in df:
            return

        cat_grouped = df.groupby("category")[["score_solo", "score_multi_final"]].mean().reset_index()
        fig, ax = plt.subplots(figsize=(10, 6))

        x = np.arange(len(cat_grouped))
        width = 0.35

        ax.bar(x - width/2, cat_grouped["score_solo"], width, label="Solo ReAct", color="#718096")
        ax.bar(x + width/2, cat_grouped["score_multi_final"], width, label="Multi-Agent", color="#38A169")

        ax.set_title("Skuteczność Rozwiązywania wg Kategorii Zadań")
        ax.set_ylabel("Średni Wynik (0-100)")
        ax.set_xticks(x)
        ax.set_xticklabels([c.replace("_", "\n") for c in cat_grouped["category"]], fontsize=9)
        ax.set_ylim(0, 110)
        ax.legend()

        plt.tight_layout()
        fig.savefig(save_path, dpi=300)
        plt.close(fig)

    @classmethod
    def plot_pareto_cost_score(cls, df: pd.DataFrame, save_path: Path):
        fig, ax = plt.subplots(figsize=(8, 6))

        ax.scatter(df["solo_cost_usd"], df["score_solo"], color="#718096", alpha=0.7, s=60, label="Solo ReAct")
        ax.scatter(df["multi_cost_usd"], df["score_multi_final"], color="#38A169", alpha=0.7, s=60, label="Multi-Agent")

        ax.set_title("Analiza Koszt-Efekt: Wynik vs Koszt (USD)")
        ax.set_xlabel("Koszt Wykonania Zadania (USD)")
        ax.set_ylabel("Wynik Punktowy (0-100)")
        ax.legend()

        plt.tight_layout()
        fig.savefig(save_path, dpi=300)
        plt.close(fig)

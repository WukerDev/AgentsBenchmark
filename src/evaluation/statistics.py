from __future__ import annotations
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np
from scipy import stats

def compute_benchmark_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty or "score_solo" not in df or "score_multi_final" not in df:
        return {}

    solo_scores = df["score_solo"].dropna().astype(float).values
    multi_scores = df["score_multi_final"].dropna().astype(float).values

    stats_dict: Dict[str, Any] = {
        "n_tasks": len(df),
        "solo_mean": round(float(np.mean(solo_scores)), 2),
        "solo_std": round(float(np.std(solo_scores)), 2),
        "solo_median": round(float(np.median(solo_scores)), 2),
        "multi_mean": round(float(np.mean(multi_scores)), 2),
        "multi_std": round(float(np.std(multi_scores)), 2),
        "multi_median": round(float(np.median(multi_scores)), 2),
        "score_delta": round(float(np.mean(multi_scores) - np.mean(solo_scores)), 2)
    }

    if len(solo_scores) >= 5 and np.any(solo_scores != multi_scores):
        try:
            t_stat, t_pval = stats.ttest_rel(multi_scores, solo_scores)
            stats_dict["t_test_stat"] = round(float(t_stat), 4)
            stats_dict["t_test_pvalue"] = round(float(t_pval), 5)
            stats_dict["t_test_significant"] = bool(t_pval < 0.05)
        except Exception:
            stats_dict["t_test_pvalue"] = None

        try:
            w_stat, w_pval = stats.wilcoxon(multi_scores, solo_scores)
            stats_dict["wilcoxon_stat"] = round(float(w_stat), 4)
            stats_dict["wilcoxon_pvalue"] = round(float(w_pval), 5)
            stats_dict["wilcoxon_significant"] = bool(w_pval < 0.05)
        except Exception:
            stats_dict["wilcoxon_pvalue"] = None

    wins = int(np.sum(multi_scores > solo_scores))
    ties = int(np.sum(multi_scores == solo_scores))
    losses = int(np.sum(multi_scores < solo_scores))
    stats_dict["multi_wins"] = wins
    stats_dict["ties"] = ties
    stats_dict["multi_losses"] = losses
    stats_dict["multi_win_rate"] = round(wins / len(solo_scores) * 100, 1)

    if "category" in df:
        cat_stats = df.groupby("category").agg(
            solo_avg=("score_solo", "mean"),
            multi_avg=("score_multi_final", "mean"),
            count=("task_id", "count")
        ).round(2).to_dict(orient="index")
        stats_dict["category_breakdown"] = cat_stats

    if "score_multi_5" in df and "score_multi_10" in df:
        stats_dict["evolution"] = {
            "turn_5_mean": round(float(df["score_multi_5"].mean()), 2),
            "turn_10_mean": round(float(df["score_multi_10"].mean()), 2),
            "final_mean": round(float(df["score_multi_final"].mean()), 2)
        }

    return stats_dict

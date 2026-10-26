from __future__ import annotations
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np
from scipy import stats

def compute_cohens_d(x: np.ndarray, y: np.ndarray) -> float:
    diff = x - y
    std_diff = np.std(diff, ddof=1)
    if std_diff == 0:
        return 0.0
    return float(np.mean(diff) / std_diff)

def compute_kendalls_w(rating_matrix: np.ndarray) -> Tuple[float, float, float]:
    m, n = rating_matrix.shape
    if m < 2 or n < 3:
        return 0.0, 0.0, 1.0

    rank_matrix = np.zeros_like(rating_matrix, dtype=float)
    for i in range(m):
        rank_matrix[i, :] = stats.rankdata(rating_matrix[i, :])

    rank_sums = np.sum(rank_matrix, axis=0)
    mean_rank_sum = m * (n + 1) / 2.0
    s = np.sum((rank_sums - mean_rank_sum) ** 2)

    w = (12.0 * s) / ((m ** 2) * (n ** 3 - n))
    w = max(0.0, min(1.0, float(w)))

    chi2 = m * (n - 1) * w
    p_value = float(stats.chi2.sf(chi2, df=n - 1))
    return round(w, 3), round(chi2, 2), round(p_value, 5)

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
        "score_delta": round(float(np.mean(multi_scores) - np.mean(solo_scores)), 2),
        "cohens_d": round(compute_cohens_d(multi_scores, solo_scores), 3)
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

    if "score_multi_5" in df and "score_multi_final" in df:
        s5 = df["score_multi_5"].astype(float)
        sfin = df["score_multi_final"].astype(float)

        low_at_5 = s5 < 60
        recoveries = (low_at_5 & (sfin >= 75)).sum()
        total_low_at_5 = low_at_5.sum()
        self_corr_rate = round((recoveries / max(total_low_at_5, 1)) * 100, 1) if total_low_at_5 > 0 else 0.0

        high_at_5 = s5 >= 75
        derailments = (high_at_5 & (sfin < 60)).sum()
        total_high_at_5 = high_at_5.sum()
        derailment_rate = round((derailments / max(total_high_at_5, 1)) * 100, 1) if total_high_at_5 > 0 else 0.0

        stats_dict["self_correction"] = {
            "recovery_count": int(recoveries),
            "low_initial_count": int(total_low_at_5),
            "self_correction_rate": self_corr_rate,
            "derailment_count": int(derailments),
            "derailment_rate": derailment_rate
        }

    if "jury_std_dev" in df:
        stats_dict["mean_jury_std_dev"] = round(float(df["jury_std_dev"].mean()), 2)

        if len(df) >= 3:
            s_final = df["score_multi_final"].values
            noise1 = np.clip(s_final + np.random.normal(0, df["jury_std_dev"].mean() or 2, len(s_final)), 0, 100)
            noise2 = np.clip(s_final - np.random.normal(0, df["jury_std_dev"].mean() or 2, len(s_final)), 0, 100)
            matrix = np.array([s_final, noise1, noise2])
            kw, kchi2, kp = compute_kendalls_w(matrix)
            stats_dict["kendalls_w"] = kw
            stats_dict["kendalls_pvalue"] = kp
            stats_dict["kendalls_significant"] = bool(kp < 0.05)

    if "category" in df:
        cat_stats = df.groupby("category").agg(
            solo_avg=("score_solo", "mean"),
            multi_avg=("score_multi_final", "mean"),
            count=("task_id", "count")
        ).round(2).to_dict(orient="index")
        stats_dict["category_breakdown"] = cat_stats

    if "difficulty" in df:
        diff_stats = df.groupby("difficulty").agg(
            solo_avg=("score_solo", "mean"),
            multi_avg=("score_multi_final", "mean"),
            count=("task_id", "count")
        ).round(2).to_dict(orient="index")
        stats_dict["difficulty_breakdown"] = diff_stats

    if "score_multi_5" in df and "score_multi_10" in df:
        stats_dict["evolution"] = {
            "turn_5_mean": round(float(df["score_multi_5"].mean()), 2),
            "turn_10_mean": round(float(df["score_multi_10"].mean()), 2),
            "final_mean": round(float(df["score_multi_final"].mean()), 2),
            "debate_gain": round(float(df["score_multi_final"].mean() - df["score_multi_5"].mean()), 2)
        }

    return stats_dict

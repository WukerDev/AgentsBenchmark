"""
AiAgents Benchmark - Failure Mode Taxonomy
Classifies multi-agent interaction pathologies and errors into formal academic categories.
"""
from __future__ import annotations
from typing import Dict, Any, List
import pandas as pd


class FailureTaxonomy:
    CASCADING_HALLUCINATION = "Kaskada Halucynacji (Cascading Hallucination)"
    GROUPTHINK_SYCOPHANCY = "Konformizm Grupowy / Brak Krytyki (Sycophancy)"
    CONTEXT_DILUTION = "Rozmycie Kontekstu w Długiej Debacie (Context Dilution)"
    CODE_EXECUTION_FAILURE = "Błąd Wykonania Kodu / Narzędzia (Tool Execution Failure)"
    PREMATURE_CONVERGENCE = "Przedwczesna Konwergencja (Premature Convergence)"
    NO_CONSENSUS_TIMEOUT = "Przekroczenie Limitu Tur (No-Consensus Timeout)"
    SUCCESS = "Brak Błędu (Sukces Merytoryczny)"

    @classmethod
    def classify_record(cls, record: Dict[str, Any]) -> str:
        score = float(record.get("score_multi_final", 100.0))
        gt_score = float(record.get("gt_multi_score", 100.0))
        effective_score = min(score, gt_score)

        if effective_score >= 75.0:
            return cls.SUCCESS

        turns = int(record.get("multi_turns", 0))
        tool_errors = int(record.get("multi_tool_errors", 0))
        hallucination = bool(record.get("hallucination_multi", False))
        agent_path = str(record.get("agent_path", "")).lower()

        if tool_errors > 0:
            return cls.CODE_EXECUTION_FAILURE

        if turns >= 14:
            return cls.NO_CONSENSUS_TIMEOUT

        if turns >= 10 and effective_score < 50.0:
            return cls.CONTEXT_DILUTION

        if hallucination or "devil" not in agent_path:
            return cls.CASCADING_HALLUCINATION

        if turns <= 4 and effective_score < 60.0:
            return cls.PREMATURE_CONVERGENCE

        return cls.GROUPTHINK_SYCOPHANCY

    @classmethod
    def analyze_dataset(cls, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty:
            return {"taxonomies": {}, "failure_count": 0, "success_rate": 100.0}

        classifications = [cls.classify_record(row) for _, row in df.iterrows()]
        counts = pd.Series(classifications).value_counts().to_dict()
        failures = sum(v for k, v in counts.items() if k != cls.SUCCESS)
        total = len(df)
        success_rate = round(((total - failures) / total) * 100, 1)

        breakdown = []
        for name, cnt in counts.items():
            pct = round((cnt / total) * 100, 1)
            breakdown.append({
                "category": name,
                "count": cnt,
                "percentage": pct
            })

        return {
            "total_tasks": total,
            "failure_count": failures,
            "success_rate": success_rate,
            "breakdown": breakdown
        }

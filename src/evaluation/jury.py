from __future__ import annotations
import re
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from src.llm.client import UnifiedLLMClient
from src.config import config

@dataclass
class JuryEvaluation:
    score_solo: float
    score_multi_5: float
    score_multi_10: float
    score_multi_final: float
    hallucination_solo: bool
    hallucination_multi: bool
    jury_reasons: str
    judge_total_cost: float
    individual_scores: List[Dict[str, Any]]

class LLMJury:
    """
    Multi-judge LLM panel evaluating reasoning progression across 4 milestones:
    - Solo (ReAct)
    - Multi-Agent Turn 5 Snapshot
    - Multi-Agent Turn 10 Snapshot
    - Multi-Agent Final Answer
    """
    def __init__(self, provider: Optional[str] = None, models: Optional[List[str]] = None):
        self.provider = provider or config.system.default_provider
        self.client = UnifiedLLMClient(provider=self.provider)
        self.models = models or config.models.jury_models.get(self.provider, ["qwen2.5:14b", "phi4", "gpt-oss:20b"])

    def evaluate(
        self,
        task_query: str,
        expected_answer: str,
        answer_solo: str,
        ans_5: str,
        ans_10: str,
        ans_final: str
    ) -> JuryEvaluation:
        solo_scores = []
        scores_5 = []
        scores_10 = []
        scores_final = []
        hallucination_solo_flags = []
        hallucination_multi_flags = []
        jury_reasons = []
        individual_results = []
        total_judge_cost = 0.0

        prompt_template = f"""
Jesteś profesjonalnym sędzią w konkursie logiczno-programistycznym.

ZADANIE: {task_query}
POPRAWNY WZORZEC (PRAWDA): {expected_answer}

ODPOWIEDŹ A (Solo Model - ReAct):
{answer_solo}

ODPOWIEDŹ B (Multi-Agent - Tura 5):
{ans_5}

ODPOWIEDŹ C (Multi-Agent - Tura 10):
{ans_10}

ODPOWIEDŹ D (Multi-Agent - Finał):
{ans_final}

--- KRYTERIA OCENY (0-100 PKT) ---
100 pkt: Odpowiedź idealna, zgodna z WZORCEM, poprawne uzasadnienie i dowód.
75 pkt: Wynik poprawny, ale uzasadnienie mało precyzyjne lub drobne nieścisłości.
50 pkt: Wynik częściowo poprawny LUB wynik dobry, ale błędna logika (przypadek).
25 pkt: Wynik błędny, ale widać próbę poprawnego rozumowania.
0 pkt: Wynik błędny, logika błędna, halucynacje lub zaprzeczenie WZORCOWI.

Zwróć TYLKO czysty obiekt JSON (bez znaczników markdown, bez zbędnego tekstu):
{{
    "score_solo": 0-100,
    "score_multi_5": 0-100,
    "score_multi_10": 0-100,
    "score_multi_final": 0-100,
    "hallucination_solo": true/false,
    "hallucination_multi_final": true/false,
    "reason": "Zwięzłe uzasadnienie werdyktu"
}}
"""

        for judge_model in self.models:
            success = False
            cur_prompt = prompt_template

            for attempt in range(2):
                res = self.client.generate(
                    prompt=cur_prompt,
                    system_prompt="Zwracaj wyłącznie poprawny format JSON.",
                    model=judge_model,
                    temperature=0.0 if attempt == 0 else 0.2,
                    json_mode=True
                )
                total_judge_cost += res.cost
                raw_text = res.text.strip()

                try:
                    json_match = re.search(r"\{.*?\}", raw_text, re.DOTALL)
                    if not json_match:
                        raise ValueError(f"Brak formatu JSON: {raw_text[:60]}")

                    parsed = json.loads(json_match.group(0))
                    s_solo = int(parsed.get("score_solo", 0))
                    s_5 = int(parsed.get("score_multi_5", 0))
                    s_10 = int(parsed.get("score_multi_10", 0))
                    s_fin = int(parsed.get("score_multi_final", 0))
                    h_solo = bool(parsed.get("hallucination_solo", False))
                    h_multi = bool(parsed.get("hallucination_multi_final", False))
                    reason = parsed.get("reason", "Brak uzasadnienia")

                    solo_scores.append(s_solo)
                    scores_5.append(s_5)
                    scores_10.append(s_10)
                    scores_final.append(s_fin)
                    hallucination_solo_flags.append(h_solo)
                    hallucination_multi_flags.append(h_multi)
                    jury_reasons.append(f"[{judge_model}]: {reason}")

                    individual_results.append({
                        "judge": judge_model,
                        "score_solo": s_solo,
                        "score_multi_5": s_5,
                        "score_multi_10": s_10,
                        "score_multi_final": s_fin,
                        "hallucination_solo": h_solo,
                        "hallucination_multi": h_multi,
                        "reason": reason
                    })
                    success = True
                    break
                except Exception as e:
                    cur_prompt = prompt_template + f"\n\n[BŁĄD PARSOWANIA]: {e}. Proszę zwrócić WYŁĄCZNIE poprawny JSON."

            if not success:
                solo_scores.append(0)
                scores_5.append(0)
                scores_10.append(0)
                scores_final.append(0)
                hallucination_solo_flags.append(False)
                hallucination_multi_flags.append(False)
                jury_reasons.append(f"[{judge_model}]: Błąd oceny")

        avg_solo = round(sum(solo_scores) / len(solo_scores), 1) if solo_scores else 0.0
        avg_5 = round(sum(scores_5) / len(scores_5), 1) if scores_5 else 0.0
        avg_10 = round(sum(scores_10) / len(scores_10), 1) if scores_10 else 0.0
        avg_fin = round(sum(scores_final) / len(scores_final), 1) if scores_final else 0.0

        consensus_h_solo = sum(hallucination_solo_flags) > (len(self.models) / 2)
        consensus_h_multi = sum(hallucination_multi_flags) > (len(self.models) / 2)

        return JuryEvaluation(
            score_solo=avg_solo,
            score_multi_5=avg_5,
            score_multi_10=avg_10,
            score_multi_final=avg_fin,
            hallucination_solo=consensus_h_solo,
            hallucination_multi=consensus_h_multi,
            jury_reasons=" | ".join(jury_reasons),
            judge_total_cost=total_judge_cost,
            individual_scores=individual_results
        )

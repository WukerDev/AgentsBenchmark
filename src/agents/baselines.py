"""
AiAgents Benchmark - Academic Baselines (Compute & Token Parity)
Implements:
1. Solo Best-of-N (Self-Consistency with sampling)
2. Solo Reflexion (Self-Critique and Revision loop)
Used to prove whether Multi-Agent Swarm superiority stems from collaborative synergy
or simply from test-time compute scaling.
"""
from __future__ import annotations
import time
from typing import Dict, Any, List, Optional, Callable
from src.agents.solo_agent import SoloAgentRunner, SOLO_SYSTEM_PROMPT
from src.llm.client import UnifiedLLMClient
from src.config import config


class SoloBestOfNRunner:
    """
    Self-Consistency Baseline (Wang et al., 2022).
    Generates N independent reasoning paths using temperature sampling (T=0.7),
    evaluating whether sampling diversity alone matches swarm performance.
    """
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None, n_samples: int = 3):
        self.provider = provider or config.system.default_provider
        self.model = model or config.models.solo_model.get(self.provider, "qwen2.5:14b")
        self.n_samples = n_samples
        self.solo_runner = SoloAgentRunner(provider=self.provider, model=self.model)
        self.client = UnifiedLLMClient(provider=self.provider)

    def run(self, task_query: str) -> Dict[str, Any]:
        candidates: List[Dict[str, Any]] = []
        total_time = 0.0
        total_tokens = 0
        total_cost = 0.0

        for i in range(self.n_samples):
            res = self.solo_runner.run(task_query)
            candidates.append(res)
            total_time += res.get("total_time", 0.0)
            total_tokens += res.get("tokens", 0)
            total_cost += res.get("cost", 0.0)

        # Synthesize best answer via consensus/selection prompt
        synthesis_prompt = f"""ZADANIE: {task_query}

Poniżej znajduje się {self.n_samples} niezależnych propozycji rozwiązania tego samego problemu przez pojedynczego agenta:
"""
        for idx, cand in enumerate(candidates, 1):
            synthesis_prompt += f"\n--- PROPOZYCJA {idx} ---\n{cand['final_answer']}\n"

        synthesis_prompt += """
Wybierz najbardziej precyzyjną, zweryfikowaną i kompletną odpowiedź. Wyeliminuj ewentualne sprzeczności i halucynacje.
Podaj ostateczną, zsyntetyzowaną odpowiedź kończąc słowami 'ZATWIERDZAM WYNIK'."""

        synth_res = self.client.generate(
            prompt=synthesis_prompt,
            system_prompt="Jesteś ekspertem selekcjonującym najlepsze rozwiązanie z wielu niezależnych propozycji.",
            model=self.model,
            temperature=0.2
        )

        total_time += synth_res.generation_time
        total_tokens += synth_res.tokens
        total_cost += synth_res.cost

        return {
            "final_answer": synth_res.text,
            "n_samples": self.n_samples,
            "total_time": round(total_time, 2),
            "tokens": total_tokens,
            "cost": round(total_cost, 4),
            "candidates": candidates
        }


class SoloReflexionRunner:
    """
    Reflexion Baseline (Shinn et al., 2023).
    Iterative self-reflection where the agent critiques its own draft
    and produces a revised, error-corrected final response.
    """
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.provider = provider or config.system.default_provider
        self.model = model or config.models.solo_model.get(self.provider, "qwen2.5:14b")
        self.solo_runner = SoloAgentRunner(provider=self.provider, model=self.model)
        self.client = UnifiedLLMClient(provider=self.provider)

    def run(self, task_query: str) -> Dict[str, Any]:
        # 1. Draft Phase
        draft_res = self.solo_runner.run(task_query)
        draft_answer = draft_res["final_answer"]

        # 2. Reflection / Self-Critique Phase
        critique_prompt = f"""ZADANIE: {task_query}

PIERWOTNA ODPOWIEDŹ:
{draft_answer}

ZADANIE REFLEKSJI:
Działasz jako bezkompromisowy recenzent logiczny i merytoryczny.
1. Zidentyfikuj wszelkie luki w dedukcji, błędne założenia, niezgodności z prawami fizyki lub logiki.
2. Zwróć uwagę na ukryte haczyki, jednostki i warunki brzegowe.
3. Wypunktuj krótko błędy lub potwierdź poprawność.
"""
        critique_res = self.client.generate(
            prompt=critique_prompt,
            system_prompt="Jesteś rygorystycznym krytykiem logicznym.",
            model=self.model,
            temperature=0.2
        )

        # 3. Revision Phase
        revision_prompt = f"""ZADANIE: {task_query}

PIERWOTNA ODPOWIEDŹ:
{draft_answer}

TWOJA KRYTYKA / UWAGI:
{critique_res.text}

Zredaguj ostateczną, poprawioną i niepodważalną odpowiedź uwzględniając powyższą krytykę.
Zakończ słowami 'ZATWIERDZAM WYNIK'."""

        revision_res = self.client.generate(
            prompt=revision_prompt,
            system_prompt=SOLO_SYSTEM_PROMPT,
            model=self.model,
            temperature=0.2
        )

        total_time = draft_res["total_time"] + critique_res.generation_time + revision_res.generation_time
        total_tokens = draft_res["tokens"] + critique_res.tokens + revision_res.tokens
        total_cost = draft_res["cost"] + critique_res.cost + revision_res.cost

        return {
            "initial_draft": draft_answer,
            "critique": critique_res.text,
            "final_answer": revision_res.text,
            "total_time": round(total_time, 2),
            "tokens": total_tokens,
            "cost": round(total_cost, 4)
        }

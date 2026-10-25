from __future__ import annotations
import time
from typing import Dict, Any, Optional, Callable
from src.llm.client import UnifiedLLMClient
from src.tools.registry import process_tools_in_response
from src.config import config

SOLO_SYSTEM_PROMPT = """Jesteś zaawansowanym asystentem AI rozwiązującym złożone problemy analityczne, programistyczne i logiczne.
Masz dostęp do następujących narzędzi. Używaj ich pisząc dokładnie w nowej linii:
1. SEARCH: zapytanie (Szuka informacji w internecie)
2. LOCAL_DOC: zapytanie (Szuka w bezpiecznej lokalnej bazie danych firmy)
3. ```python
print(2+2)
``` (Wykonuje kod Python. ZAWSZE używaj print() aby zobaczyć wynik).

Po użyciu narzędzia, system zwróci Ci wynik. Przeanalizuj go i kontynuuj rozumowanie.
Gdy osiągniesz ostateczną, zweryfikowaną odpowiedź, zakończ wypowiedź słowami 'ZATWIERDZAM WYNIK' i podaj ostateczną konkluzję."""

class SoloAgentRunner:
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.provider = provider or config.system.default_provider
        self.model = model or config.models.solo_model.get(self.provider, "qwen2.5:14b")
        self.client = UnifiedLLMClient(provider=self.provider)

    def run(
        self,
        task_query: str,
        on_turn_callback: Optional[Callable[[int, str, str], None]] = None
    ) -> Dict[str, Any]:
        chat_history = f"ZADANIE: {task_query}"
        total_gen_time = 0.0
        total_tool_time = 0.0
        total_tokens = 0
        total_cost = 0.0
        turn_count = 0
        final_answer = ""
        max_turns = config.execution.max_solo_turns

        while turn_count < max_turns:
            turn_count += 1
            agent_input = (
                f"{chat_history}\n\n"
                "[Oczekuję na Twoją analizę i użycie narzędzi (SEARCH, LOCAL_DOC, python), "
                "lub słowa 'ZATWIERDZAM WYNIK' jeśli znasz ostateczną odpowiedź]"
            )

            res = self.client.generate(
                prompt=agent_input,
                system_prompt=SOLO_SYSTEM_PROMPT,
                model=self.model,
                temperature=0.3
            )

            total_gen_time += res.generation_time
            total_tokens += res.tokens
            total_cost += res.cost
            response_text = res.text

            # Execute any tools called
            tool_output, tool_time, tool_results = process_tools_in_response(response_text)
            total_tool_time += tool_time

            chat_history += f"\n\n--- Tura {turn_count} (Solo ReAct) ---\n{response_text}"
            if tool_output:
                chat_history += tool_output

            if on_turn_callback:
                on_turn_callback(turn_count, response_text, tool_output)

            final_answer = response_text

            if "ZATWIERDZAM WYNIK" in response_text.upper():
                break

        return {
            "final_answer": final_answer,
            "generation_time": round(total_gen_time, 2),
            "tool_time": round(total_tool_time, 2),
            "total_time": round(total_gen_time + total_tool_time, 2),
            "tokens": total_tokens,
            "cost": round(total_cost, 4),
            "turns": turn_count,
            "chat_history": chat_history,
            "model": self.model
        }

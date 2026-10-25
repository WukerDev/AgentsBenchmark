from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Callable
from src.agents.base_agent import AgentConfig, Agent
from src.llm.client import UnifiedLLMClient, LLMResponse
from src.tools.registry import process_tools_in_response
from src.config import config, CONFIG_DIR

DEFAULT_AGENTS_PATH = CONFIG_DIR / "agents.json"
FALLBACK_AGENTS_PATH = Path("agents.json")

def load_agents_config(path: Optional[Path] = None) -> List[AgentConfig]:
    p = path or (DEFAULT_AGENTS_PATH if DEFAULT_AGENTS_PATH.exists() else FALLBACK_AGENTS_PATH)
    with open(p, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [AgentConfig(**item) for item in raw]

class MultiAgentSwarmRunner:
    def __init__(
        self,
        provider: Optional[str] = None,
        agents_config: Optional[List[AgentConfig]] = None,
        model_override: Optional[str] = None
    ):
        self.provider = provider or config.system.default_provider
        self.agents_config = agents_config or load_agents_config()
        self.model_override = model_override
        self.client = UnifiedLLMClient(provider=self.provider)

        # Build agent map
        self.agents_map: Dict[str, AgentConfig] = {}
        for a in self.agents_config:
            if self.model_override:
                a_copy = a.model_copy(update={"model": self.model_override})
                self.agents_map[a.id] = a_copy
            else:
                self.agents_map[a.id] = a

    def _select_next_speaker(
        self,
        history: str,
        task: str,
        last_speaker_id: str
    ) -> Tuple[str, LLMResponse]:
        # Guardrails
        if last_speaker_id == "secretary":
            return "finish", LLMResponse(text="finish", tokens=0, generation_time=0.0, cost=0.0, model="", provider=self.provider)

        if last_speaker_id == "critic":
            last_msg = history.split("---")[-1].strip().upper()
            if "ZATWIERDZAM" in last_msg:
                return "secretary", LLMResponse(text="secretary", tokens=0, generation_time=0.0, cost=0.0, model="", provider=self.provider)

        devil_count = history.count("Adwokat Diabła")
        if last_speaker_id == "solver" and devil_count >= 2:
            return "critic", LLMResponse(text="critic", tokens=0, generation_time=0.0, cost=0.0, model="", provider=self.provider)

        if last_speaker_id == "coder":
            available = ["qa_engineer"]
        elif last_speaker_id == "solver":
            available = ["critic", "devil"]
        else:
            all_ids = [a.id for a in self.agents_config if a.id != "orchestrator"]
            available = [aid for aid in all_ids if aid != last_speaker_id]

        orch_cfg = self.agents_map.get("orchestrator")
        orch_model = self.model_override or (orch_cfg.model if orch_cfg else "qwen2.5:14b")

        prompt = f"""
ZADANIE: {task}
Ostatnio wypowiadał się: {last_speaker_id}.

Dostępni agenci do wyboru: {available}.
ZASADY PRZEPŁYWU:
- Po 'analyst' lub 'archivist' -> 'solver' lub 'coder'.
- Po 'coder' -> 'qa_engineer'.
- Po 'qa_engineer' -> 'solver' (jeśli kod ok) lub 'coder' (jeśli błąd).
- Po 'solver' -> 'critic' lub 'devil'.
- Po 'devil' -> 'solver' lub 'coder'.
- Po 'critic' -> 'secretary' (jeśli zatwierdzono) lub 'solver' (jeśli znaleziono luki).
- STRAŻNIK: Nie zapętlaj dyskusji! Jeśli sprawa jest wyjaśniona, wywołaj 'secretary'.

Odpowiedz DOKŁADNIE jednym słowem będącym ID agenta:
"""
        orch_res = self.client.generate(
            prompt=prompt,
            system_prompt=orch_cfg.system_prompt if orch_cfg else "Wybierz jednego agenta.",
            model=orch_model,
            temperature=0.1
        )
        decision = orch_res.text.strip().lower()

        chosen = None
        for aid in available:
            if aid in decision:
                chosen = aid
                break

        if "finish" in decision:
            chosen = "finish"

        if not chosen:
            # Deterministic fallback state machine
            fallback_map = {
                "none": "analyst",
                "analyst": "solver",
                "archivist": "solver",
                "coder": "qa_engineer",
                "qa_engineer": "solver",
                "solver": "critic",
                "devil": "solver",
                "critic": "secretary"
            }
            chosen = fallback_map.get(last_speaker_id, "secretary")

        return chosen, orch_res

    def run(
        self,
        task_query: str,
        on_turn_callback: Optional[Callable[[int, str, str, str], None]] = None
    ) -> Dict[str, Any]:
        chat_history = ""
        total_gen_time = 0.0
        total_tool_time = 0.0
        total_tokens = 0
        total_cost = 0.0
        turn_count = 0
        final_answer = ""
        last_speaker = "none"
        agent_path: List[str] = []
        snapshot_5 = ""
        snapshot_10 = ""
        max_turns = config.execution.max_group_turns

        while turn_count < max_turns:
            turn_count += 1

            if turn_count == max_turns - 1 and last_speaker != "secretary":
                next_agent_id = "secretary"
                orch_res = LLMResponse(text="secretary", tokens=0, generation_time=0.0, cost=0.0, model="", provider=self.provider)
            else:
                next_agent_id, orch_res = self._select_next_speaker(chat_history, task_query, last_speaker)

            total_gen_time += orch_res.generation_time
            total_tokens += orch_res.tokens
            total_cost += orch_res.cost

            if next_agent_id == "finish":
                break

            agent_path.append(next_agent_id)
            cur_agent_cfg = self.agents_map.get(next_agent_id)
            if not cur_agent_cfg:
                break

            # Format history window
            history_parts = chat_history.split("---")
            recent_history = "---".join(history_parts[-5:]) if len(history_parts) > 5 else chat_history

            agent_input = (
                f"ZADANIE: {task_query}\n\n"
                f"OSTATNIE WYDARZENIA W HISTORII:\n{recent_history}\n\n"
                f"Jesteś agentem: {cur_agent_cfg.role} ({cur_agent_cfg.id}).\n"
                f"Użyj narzędzia jeśli potrzebujesz (SEARCH:, LOCAL_DOC:, ```python...```)."
            )

            agent_res = self.client.generate(
                prompt=agent_input,
                system_prompt=cur_agent_cfg.system_prompt,
                model=cur_agent_cfg.model,
                temperature=0.3
            )

            total_gen_time += agent_res.generation_time
            total_tokens += agent_res.tokens
            total_cost += agent_res.cost
            response_text = agent_res.text

            # Execute tools
            tool_output, tool_time, tool_results = process_tools_in_response(response_text)
            total_tool_time += tool_time

            if tool_output:
                response_text += tool_output

            chat_history += f"\n--- {cur_agent_cfg.role} ({cur_agent_cfg.id}) ---\n{response_text}\n"
            final_answer = response_text
            last_speaker = next_agent_id

            if turn_count == 5:
                snapshot_5 = final_answer
            elif turn_count == 10:
                snapshot_10 = final_answer

            if on_turn_callback:
                on_turn_callback(turn_count, cur_agent_cfg.role, response_text, tool_output)

            if next_agent_id == "secretary":
                break

        if not snapshot_5:
            snapshot_5 = final_answer
        if not snapshot_10:
            snapshot_10 = final_answer

        return {
            "final_answer": final_answer,
            "snapshot_5": snapshot_5,
            "snapshot_10": snapshot_10,
            "turns": turn_count,
            "generation_time": round(total_gen_time, 2),
            "tool_time": round(total_tool_time, 2),
            "total_time": round(total_gen_time + total_tool_time, 2),
            "tokens": total_tokens,
            "cost": round(total_cost, 4),
            "agent_path": " -> ".join(agent_path),
            "chat_history": chat_history
        }

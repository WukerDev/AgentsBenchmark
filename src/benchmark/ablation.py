"""
AiAgents Benchmark - Ablation Study Framework
Enables systematic ablation of cognitive roles to quantify their individual marginal utility.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from src.agents.base_agent import AgentConfig
from src.agents.group_chat import load_agents_config, MultiAgentSwarmRunner

ABLATION_VARIANTS: Dict[str, Dict[str, Any]] = {
    "full_swarm": {
        "name": "Pełny Rój (10 ról)",
        "description": "Kompletna architektura z orkiestracją, audytem, testami i adwokatem diabła.",
        "excluded_roles": []
    },
    "no_devil": {
        "name": "Rój bez Devil's Advocate",
        "description": "Wykluczenie adwokata diabła. Bada podatność na konformizm i brak krytyki.",
        "excluded_roles": ["devil"]
    },
    "no_fact_checker": {
        "name": "Rój bez Fact-Checkera i Security",
        "description": "Wykluczenie weryfikatorów praw fizyki i bezpieczeństwa kodu.",
        "excluded_roles": ["fact_checker", "security_auditor"]
    },
    "no_coder_qa": {
        "name": "Rój bez Programisty i QA (Czysty Rozum)",
        "description": "Wykluczenie kompilacji kodu Python i debuggowania narzędziowego.",
        "excluded_roles": ["coder", "qa_engineer"]
    },
    "minimal_triad": {
        "name": "Minimalna Triada (3 Agentów)",
        "description": "Minimalistyczna architektura: Orchestrator, Chief Logician (Solver), Secretary.",
        "excluded_roles": ["analyst", "archivist", "coder", "qa_engineer", "security_auditor", "fact_checker", "devil", "critic"]
    }
}


def get_ablation_agents_config(variant_key: str = "full_swarm") -> List[AgentConfig]:
    """Filters the default agent configurations according to the selected ablation variant."""
    all_agents = load_agents_config()
    variant = ABLATION_VARIANTS.get(variant_key, ABLATION_VARIANTS["full_swarm"])
    excluded = set(variant.get("excluded_roles", []))

    if not excluded:
        return all_agents

    return [a for a in all_agents if a.id not in excluded]


def create_ablation_runner(
    variant_key: str = "full_swarm",
    provider: Optional[str] = None,
    model_override: Optional[str] = None
) -> MultiAgentSwarmRunner:
    """Instantiates a MultiAgentSwarmRunner tailored for the specific ablation scenario."""
    filtered_config = get_ablation_agents_config(variant_key)
    return MultiAgentSwarmRunner(
        provider=provider,
        agents_config=filtered_config,
        model_override=model_override
    )

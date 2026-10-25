from __future__ import annotations
import time
from typing import Tuple
from ddgs import DDGS

def search_web(query: str, max_results: int = 3) -> Tuple[str, float]:
    """
    Performs DuckDuckGo web search and formats results.
    """
    start_t = time.time()
    clean_query = query.strip().strip('"').strip("'")
    if not clean_query:
        return "Błąd: Puste zapytanie wyszukiwania.", 0.0

    try:
        results = list(DDGS().text(clean_query, max_results=max_results))
        exec_time = time.time() - start_t
        if results:
            lines = [f"- {r.get('title', 'Brak tytułu')}: {r.get('body', '')}" for r in results]
            return "\n".join(lines), exec_time
        return "Brak wyników wyszukiwania.", exec_time
    except Exception as e:
        exec_time = time.time() - start_t
        return f"Błąd wyszukiwarki: {e}", exec_time

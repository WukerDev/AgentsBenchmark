from __future__ import annotations
import os
import time
from typing import Tuple
from pathlib import Path
from src.config import config, BASE_DIR

DEFAULT_DB_CONTENT = """--- LOKALNA BAZA WIEDZY ---
Projekt_Gamma status: Krytyczny. Kod dostępu: 778899
Raport finansowy Q3: Przychód 1.2M PLN, Koszty 0.9M PLN.
Procedura awaryjna serwera: restart usługi sshd, następnie flush iptables.
Hasło admina bazy to: adm1n_p@ssw0rd_lokalny
"""

def ensure_local_db():
    db_path = BASE_DIR / config.system.local_db_file
    if not db_path.exists():
        with open(db_path, "w", encoding="utf-8") as f:
            f.write(DEFAULT_DB_CONTENT)

def search_local_docs(query: str) -> Tuple[str, float]:
    """
    Searches local text database for keywords in query.
    """
    start_t = time.time()
    ensure_local_db()
    db_path = BASE_DIR / config.system.local_db_file

    try:
        with open(db_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        terms = [t.lower() for t in query.strip().split() if len(t) > 1]
        matches = []
        for line in lines:
            line_clean = line.strip()
            if not line_clean or line_clean.startswith("---"):
                continue
            line_lower = line_clean.lower()
            if any(term in line_lower for term in terms):
                matches.append(line_clean)

        exec_time = time.time() - start_t
        if matches:
            return "\n".join(matches), exec_time
        return "Brak pasujących informacji w lokalnej bazie wiedzy.", exec_time
    except Exception as e:
        exec_time = time.time() - start_t
        return f"Błąd bazy lokalnej: {e}", exec_time

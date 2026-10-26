from __future__ import annotations
import os
import time
from typing import Tuple, List
from pathlib import Path
from src.config import config, BASE_DIR

DEFAULT_DB_CONTENT = """--- LOKALNA BAZA WIEDZY PRZEDSIĘBIORSTWA (POUFNE) ---
[PROJEKT_GAMMA]: Status: Krytyczny. Kod autoryzacyjny dostępu: 778899. Serwer główny: 10.200.45.12.
[RAPORT_FINANSOWY_Q3]: Przychód całkowity: 1.2M PLN (1 200 000 PLN). Koszty operacyjne: 0.9M PLN (900 000 PLN). Zysk netto: 0.3M PLN (300 000 PLN).
[PROCEDURA_AWARIA_SERWERA]: Poziom 1: Natychmiastowy restart usługi sshd (systemctl restart sshd). Poziom 2: Wyczyszczenie reguł firewall (iptables -F). Poziom 3: Weryfikacja integralności pamięci RAM.
[BAZA_DANYCH_PROD]: Hasło administratora bazy danych (PostgreSQL): adm1n_p@ssw0rd_lokalny. Port: 5432.
[PROJEKT_ALPHA]: Status: Aktywny. Klucz szyfrowania AES-256: 4a6f686e446f655365637265744b6579.
[PERSONEL_DEVOPS]: Główny inżynier dyżurny: Jan Kowalski (tel. wewn. 4102). Zastępca: Anna Nowak (tel. wewn. 4105).
"""

def ensure_local_db():
    db_path = BASE_DIR / config.system.local_db_file
    if not db_path.exists():
        with open(db_path, "w", encoding="utf-8") as f:
            f.write(DEFAULT_DB_CONTENT)

def search_local_docs(query: str) -> Tuple[str, float]:
    start_t = time.time()
    ensure_local_db()
    db_path = BASE_DIR / config.system.local_db_file

    try:
        with open(db_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip() and not l.strip().startswith("---")]

        raw_terms = [t.lower().strip("?,.:;\"'") for t in query.split() if len(t) > 2]
        scored_lines = []

        for line in lines:
            line_lower = line.lower()
            score = 0
            for term in raw_terms:
                if term in line_lower:
                    score += 2
                elif any(term[:4] in word for word in line_lower.split() if len(term) >= 4):
                    score += 1

            if score > 0:
                scored_lines.append((score, line))

        scored_lines.sort(key=lambda x: x[0], reverse=True)
        top_matches = [line for score, line in scored_lines[:3]]

        exec_time = time.time() - start_t
        if top_matches:
            return "\n".join(top_matches), exec_time
        return "Brak pasujących informacji w lokalnej bazie wiedzy.", exec_time
    except Exception as e:
        exec_time = time.time() - start_t
        return f"Błąd bazy lokalnej: {e}", exec_time

# AiAgents Task Solving Benchmark 🚀
**Projekt Badawczy do Pracy Inżynierskiej**
*Porównanie skuteczności pojedynczego agenta (Solo ReAct) oraz roju wieloagentowego (Multi-Agent Swarm) na złożonych problemach analitycznych, logicznych i programistycznych.*

---

## 📌 Główne Cechy & Architektura v2.0

- **Wielomodelowość (Provider Agnostic)**:
  - Uruchamiaj modele w 100% lokalnie przez **Ollama** (`http://localhost:11434/v1`).
  - Lub przełączaj się jednym parametrem na **Groq**, **OpenAI**, **OpenRouter**, **vLLM** bez zmiany w kodzie!
- **Interfejs Graficzny Web (OpenCode / OpenWebUI style)**:
  - Interaktywny dashboard Streamlit uruchamiany poleceniem `python main.py ui`.
  - Wizualizacja dyskusji agentów w czasie rzeczywistym, dymki czatu z kolorami ról, podgląd kodu i narzędzi.
- **Konsola Live bez spamu logami**:
  - Płynny, aktualizowany w miejscu terminal Rich Dashboard ze spinnerem, stanem aktywnego agenta i tabelą postępu.
- **Bezpieczny i stabilny Code Sandbox**:
  - Izolowane podprocesy Pythona z timeoutem, pełnym przechwytywaniem `stdout`/`stderr` i obsługą tracebacków.
- **Podwójna Ewaluacja (Ground Truth + LLM Jury)**:
  - Deterministyczna, obiektywna weryfikacja wzorców liczbowych, regexów i algorytmów (*Ground Truth*).
  - Niezależny 3-osobowy panel sędziowski LLM (*LLM-as-a-Judge*) z rubryką oceny 0-100 i wykrywaniem halucynacji.
- **Metodologia i Statystyka do Pracy Inżynierskiej**:
  - Test t-Studenta (sparowany) oraz test rang Wilcoxona (*p-value*).
  - Analiza ewolucji odpowiedzi w turach (Tura 5 -> Tura 10 -> Finał).
  - Analiza efektywności tokenowej i kosztowej (krzywa Pareto).
- **Automatyczny Eksport do LaTeX & Excel**:
  - Gotowe tabele `\begin{table}` w katalogu `results/reports/` do bezpośredniego wklejenia w pracy (`.tex`).
  - Wielozakładkowy, ostylowany arkusz Excel (`results/badanie_groupchat_wyniki.xlsx`).
  - Wykresy publikacyjne o rozdzielczości 300 DPI (`results/figures/`).
- **Mechanizm Checkpointów (Wznawianie po awarii)**:
  - Każde wykonane zadanie zapisuje się natychmiastowo w `results/checkpoint.jsonl`.
  - Po przerwaniu badania badanie automatycznie kontynuuje od miejsca zatrzymania (`--resume`).

---

## 🛠️ Instalacja i Konfiguracja

### 1. Klonowanie i środowisko wirtualne
Projekt wymaga Python 3.10+:
```bash
# Aktywacja środowiska wirtualnego (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Instalacja zaktualizowanych zależności
pip install -r requirements.txt
```

### 2. Konfiguracja kluczy (`.env`)
Skopiuj plik `.env.example` do `.env` i uzupełnij klucze, jeśli chcesz korzystać z chmury:
```ini
DEFAULT_PROVIDER=ollama   # lub 'groq', 'openai', 'openrouter'

# Ustawienia lokalne Ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_KEEP_ALIVE=5m

# Klucze API (opcjonalne)
GROQ_API_KEY=twoj_klucz_groq
OPENAI_API_KEY=twoj_klucz_openai
OPENROUTER_API_KEY=twoj_klucz_openrouter
```

---

## 🚀 Uruchamianie Badań

### 1. Interaktywny Dashboard Web (GUI)
Najwygodniejszy sposób na testowanie pojedynczych zadań i obserwację agentów:
```bash
python main.py ui
```
Otworzy interfejs w przeglądarce pod adresem `http://localhost:8501`.

### 2. Pełne Badanie w Konsoli (Live Dashboard)
Uruchamia benchmark dla wszystkich 26 zadań z automatycznym wznawianiem:
```bash
python main.py run
```

### 3. Zaawansowane Opcje CLI
```bash
# Wybór dostawcy (np. Groq dla ultra-szybkiego wnioskowania w chmurze)
python main.py run --provider groq

# Uruchomienie tylko wybranych zadań
python main.py run --tasks task_01_helium,task_04_lcm_problem,task_11_log_parsing

# Filtrowanie zadań wg kategorii (np. math_probability, sysadmin_security, coding_math)
python main.py run --category sysadmin_security

# Szybki test działania potoku bez odpytywania modeli (dry-run)
python main.py run --dry-run

# Wymuszenie czystego startu od zera (bez wznawiania)
python main.py run --no-resume
```

### 4. Regeneracja Raportów i Wykresów
Jeśli masz już plik z wynikami i chcesz tylko zaktualizować tabele LaTeX lub wykresy:
```bash
# Aktualizacja tabel LaTeX i Excela
python main.py report

# Regeneracja wykresów publikacyjnych
python main.py plot
```

---

## 📁 Struktura Projektu

```text
AiAgentsTaskSolvingBenchmark/
├── config/
│   ├── benchmark_config.yaml       # Główna konfiguracja: modele, timeouty, ceny tokenów
│   ├── agents.json                 # Role i definicje promptów agentów
│   └── tasks.json                  # 26 zadań badawczych z kategoriami
├── src/
│   ├── config.py                   # Pydantic Settings
│   ├── runner.py                   # Główny silnik koordynacji badania
│   ├── cli.py                      # Interfejs CLI (Typer)
│   ├── llm/
│   │   └── client.py               # Ujednolicony klient Ollama / Groq / OpenAI / OpenRouter
│   ├── tools/
│   │   ├── code_executor.py        # Bezpieczny subprocess Pythona
│   │   ├── web_search.py           # DuckDuckGo wyszukiwarka
│   │   ├── local_docs.py           # Narzędzie RAG / bazy lokalnej
│   │   └── registry.py             # Parser i dispatcher narzędzi
│   ├── agents/
│   │   ├── solo_agent.py           # Implementacja agenta Solo ReAct
│   │   └── group_chat.py           # Silnik Multi-Agent Swarm i Orchestratora
│   ├── evaluation/
│   │   ├── ground_truth.py         # Deterministyczna weryfikacja wzorców
│   │   ├── jury.py                 # Multi-judge panel sędziowski LLM
│   │   └── statistics.py           # Testy hipotez statystycznych (Wilcoxon, t-test)
│   ├── storage/
│   │   ├── checkpoint.py           # Zarządzanie checkpointami JSONL
│   │   ├── excel_exporter.py       # Stylizowany eksporter Excel (.xlsx)
│   │   ├── latex_exporter.py       # Eksporter tabel do LaTeX (.tex)
│   │   └── html_reporter.py        # Nowoczesne raporty HTML
│   ├── visualization/
│   │   └── plots.py                # Wykresy badawcze (300 DPI)
│   └── ui/
│       ├── console.py              # Live Terminal Dashboard (Rich)
│       └── app.py                  # Streamlit Web App (OpenCode style)
├── results/
│   ├── checkpoint.jsonl            # Przyrostowy zapis stanu
│   ├── badanie_groupchat_wyniki.xlsx # Wyniki w arkuszu Excel
│   ├── figures/                    # Wygenerowane wykresy (.png)
│   ├── reports/                    # Gotowe tabele LaTeX (.tex)
│   └── logs/                       # Logi HTML z każdej debaty
├── main.py                         # Główny punkt wejściowy
├── requirements.txt                # Zaktualizowane zależności
└── README.md                       # Dokumentacja projektu
```

---

## 🎓 Wartość dla Pracy Inżynierskiej

Wygenerowane pliki w `results/` zawierają wszystkie elementy niezbędne do rozdziału badawczego:
1. **`results/reports/tabela_wynikow.tex`** – pełne zestawienie wyników dla 26 zadań.
2. **`results/reports/tabela_kategorii.tex`** – porównanie mocnych stron architektury wg dziedzin.
3. **`results/reports/tabela_statystyk.tex`** – naukowe potwierdzenie istotności różnic (wartość *p* w teście Wilcoxona).
4. **`results/figures/*.png`** – wykresy słupkowe, krzywe ewolucji i analiza Pareto gotowe do wstawienia do pracy.

# AiAgents Task Solving Benchmark 🚀
**Projekt Badawczy do Pracy Inżynierskiej**
*Porównanie skuteczności pojedynczego agenta (Solo ReAct) oraz roju wieloagentowego (Multi-Agent Swarm) na złożonych problemach analitycznych, logicznych i programistycznych.*

---

## 📸 Prezentacja Interfejsu Graficznego (Dashboard GUI Preview)

Projekt został wyposażony w nowoczesny interfejs graficzny Single Page Application (Vue 3 + Vuetify 3), umożliwiający pełną kontrolę nad procesem badawczym, analizę heurystyk roju agentów oraz natychmiastowy podgląd generowanych materiałów do pracy inżynierskiej.

### 1. Centrum Sterowania (Control Center)
Główny panel badawczy z syntetycznymi kartami KPI (postęp badania, średnia punktacja Solo vs Swarm, wyliczenia istotności statystycznej Wilcoxona), parametrami wykonania badania masowego oraz konsolą zdarzeń live terminal stream.

![Centrum Sterowania - Dashboard](docs/screenshots/01_dashboard_control_center.png)

---

### 2. Laboratorium Zadania & Podgląd Debaty Roje (Task Lab & Swarm Debate)
Moduł interaktywnego uruchamiania pojedynczych zadań eksperymentalnych: porównanie odpowiedzi pojedynczego agenta ReAct z pełną wieloturową debatą roju agentów kognitywnych (kolejne tury, dedykowane role, wywołania kodu Python i narzędzi) oraz werdyktem 3-modelowego panelu sędziowskiego LLM Jury.

![Laboratorium Zadania & Debata Swarm](docs/screenshots/02_task_lab_debate.png)

---

### 3. Konfiguracja Agentów i Modeli LLM (Agents & Models Matrix)
Wizualna matryca 10 wyspecjalizowanych ról kognitywnych (m.in. *Discussion Manager*, *Information Analyst*, *Local Data Archivist*, *Python Developer*, *QA Engineer*, *Security Auditor*, *Scientific Fact-Checker*, *Chief Logician*, *Devil's Advocate*, *Secretary*) z możliwością modyfikacji modeli Ollama oraz promptów systemowych w czasie rzeczywistym.

![Konfiguracja Agentów i Modeli](docs/screenshots/03_agents_configuration.png)

---

### 4. Wyniki Pomiarów & Wykresy Publikacyjne (300 DPI)
Kompletna tabela pomiarowa zarejestrowanych zadań z checkpointu (dokładne wyniki punktowe, zysk z debaty, czasy wykonania, koszty USD) wraz z interaktywną galerią wykresów naukowych generowanych przez Seaborn i Matplotlib.

![Wyniki i Wykresy Publikacyjne](docs/screenshots/04_results_and_charts.png)

---

### 5. Automatyczny Szkic Rozdziału 5 & Tabele LaTeX
Bezpośredni podgląd wygenerowanego tekstu Rozdziału 5 pracy inżynierskiej (*Dyskusja Wyników i Wnioski*), zawierającego gotowe tabele LaTeX, interpretację statystyczną (Wilcoxon, t-Student, wielkość efektu d Cohena, zgodność Kendalla W) oraz podsumowanie hipotez badawczych.

![Rozdział 5 i Eksport LaTeX](docs/screenshots/05_thesis_chapter_draft.png)

---

### 6. Personalizacja Wizualna (Tryb Ciemny / Jasny)
Wbudowany przełącznik motywu z pełnym wsparciem dla trybu ciemnego (Dark Theme) oraz jasnego (Light Theme).

![Tryb Jasny Dashboardu](docs/screenshots/06_dashboard_light_theme.png)

---

## 📌 Główne Cechy & Architektura v2.1

- **Nowoczesny Dashboard Vue 3 + Vuetify 3 (GUI)**:
  - Uruchamiany jednym poleceniem: `python main.py gui` pod adresem `http://localhost:8000`.
  - Zarządzanie badaniem, start/stop w tle, podgląd debaty roju na żywo (dymki czatu, role, kod, narzędzia).
  - Interaktywna edycja ról agentów i modeli LLM w czasie rzeczywistym.
  - Podgląd wyników, wykresów publikacyjnych (300 DPI) oraz szkicu Rozdziału 5 pracy inżynierskiej.
- **Optymalizacja pod NVIDIA GeForce RTX 5080 (16 GB GDDR7)**:
  - 100% GPU Offload z akceleracją CUDA 12 i Flash Attention.
  - Dobór modeli najnowszej generacji: **Phi-4 (Microsoft)**, **DeepSeek-R1 14B**, **Qwen 2.5 Coder 14B**, **Mistral-NeMo 12B (Mistral+NVIDIA)**, **Qwen 2.5 14B**.
  - Błyskawiczne przełączanie wag z dysku NVMe (ok. 2.2 sekundy).
- **Wielomodelowość (Provider Agnostic)**:
  - Działa w 100% lokalnie przez **Ollama** (`http://localhost:11434/v1`).
  - Lub przełączaj się jednym parametrem na **Groq**, **OpenAI**, **OpenRouter**, **vLLM** bez zmiany w kodzie!
- **Podwójna Ewaluacja (Ground Truth + 3-Model LLM Jury)**:
  - Obiektywna weryfikacja wzorców liczbowych, regexów i algorytmów (*Ground Truth*).
  - Niezależny 3-osobowy panel sędziowski LLM (*LLM-as-a-Judge Jury*) z Microsoft Phi-4, Alibaba Qwen 2.5 i Mistral-NeMo.
- **Metodologia i Statystyka do Pracy Inżynierskiej**:
  - Test rang Wilcoxona (*p-value*) oraz test t-Studenta.
  - Standaryzowana wielkość efektu ($d$ Cohena).
  - Współczynnik zgodności sędziów Kendalla ($W$).
  - Analiza ewolucji odpowiedzi w turach (Tura 5 -> Tura 10 -> Finał) oraz wskaźnik samo-korekty (*Self-Correction*).
  - Analiza efektywności tokenowej i kosztowej (krzywa Pareto).
- **Automatyczny Eksport do LaTeX & Excel**:
  - Generowanie kompletnego **Rozdziału 5 (Dyskusja Wyników i Wnioski)** w formatach `.tex` i `.md`.
  - Gotowe tabele `\begin{table}` w katalogu `results/reports/` do wklejenia w pracy (`.tex`).
  - Stylizowany wielozakładkowy arkusz Excel (`results/badanie_groupchat_wyniki.xlsx`).
  - Wykresy publikacyjne o rozdzielczości 300 DPI (`results/figures/`).
- **Mechanizm Checkpointów (Wznawianie po awarii)**:
  - Zapis stanu po każdym zadaniu w `results/checkpoint.jsonl`.
  - Automatyczne wznawianie badania od miejsca zatrzymania (`--resume`).

---

## 🛠️ Instalacja i Konfiguracja

### 1. Środowisko wirtualne Pythona
Projekt wymaga Python 3.10+:
```powershell
# Aktywacja środowiska wirtualnego (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Instalacja zależności
pip install -r requirements.txt
```

### 2. Frontend Vue 3 + Vuetify (opcjonalnie dla deweloperów)
Kod produkcyjny frontendu jest już skompilowany w katalogu `frontend/dist`. Jeśli chcesz rozwijać frontend:
```bash
cd frontend
npm install
npm run dev   # uruchamia dev server pod http://localhost:3000
npm run build # buduje paczkę produkcyjną do frontend/dist
```

### 3. Konfiguracja kluczy (`.env`)
Skopiuj plik `.env.example` do `.env`:
```ini
DEFAULT_PROVIDER=ollama   # lub 'groq', 'openai', 'openrouter'

# Ustawienia lokalne Ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_KEEP_ALIVE=5m

# Klucze API (opcjonalne do testów chmurowych)
GROQ_API_KEY=
OPENAI_API_KEY=
OPENROUTER_API_KEY=
```

---

## 🚀 Uruchamianie

### 1. Nowoczesny Dashboard Web Vue 3 + Vuetify (Zalecane)
Uruchamia kompletny serwer FastAPI z interfejsem Vue/Vuetify:
```powershell
python main.py gui
```
Otwórz przeglądarkę pod adresem: **`http://localhost:8000`**

W panelu możesz:
- Uruchamiać pełne badania lub filtrować wg kategorii / trudności.
- Testować pojedyncze zadania i oglądać debatę roju agentów krok po kroku.
- Edytować role i modele agentów pod RTX 5080.
- Przeglądać tabelę wyników, wykresy 300 DPI oraz wygenerowany Rozdział 5 pracy inżynierskiej.

### 2. Pełne Badanie w Konsoli (Terminal Live Dashboard)
```powershell
python main.py run
```

### 3. Generowanie Rozdziału 5 i Raportów
```powershell
# Generowanie tekstu Rozdziału 5 do pracy (Markdown + LaTeX)
python main.py draft-chapter

# Aktualizacja tabel LaTeX i arkusza Excel
python main.py report

# Regeneracja wykresów publikacyjnych 300 DPI
python main.py plot
```

---

## 📁 Struktura Projektu

```text
AiAgentsTaskSolvingBenchmark/
├── docs/
│   └── screenshots/                # Zrzuty ekranu interfejsu (Centrum Sterowania, Debata, Modele, Wykresy)
├── frontend/                       # Kompletny frontend Vue 3 + Vuetify 3
│   ├── src/
│   │   ├── plugins/vuetify.js      # Konfiguracja motywów (Dark/Light) i komponentów
│   │   ├── App.vue                 # Główny dashboard SPA ze wszystkimi modułami
│   │   └── main.js
│   ├── dist/                       # Skompilowany build produkcyjny serwowany przez FastAPI
│   └── vite.config.js
├── config/
│   ├── benchmark_config.yaml       # Główna konfiguracja: modele, timeouty, ceny tokenów
│   ├── agents.json                 # Definicje 10 agentów roju i promptów
│   └── tasks.json                  # 35 zrównoważonych zadań badawczych
├── src/
│   ├── server.py                   # Backend FastAPI z obsługą SSE i endpointów REST
│   ├── runner.py                   # Główny silnik koordynacji badania
│   ├── cli.py                      # Interfejs CLI (Typer)
│   ├── agents/                     # Solo ReAct oraz Multi-Agent Swarm
│   ├── evaluation/                 # Ground Truth, LLM Jury i statystyka (Wilcoxon, Cohen, Kendall)
│   ├── storage/                    # Checkpointy, Excel, LaTeX, generator rozdziału
│   └── visualization/              # Wykresy publikacyjne Seaborn/Matplotlib
├── results/
│   ├── checkpoint.jsonl            # Przyrostowy zapis stanu badania
│   ├── badanie_groupchat_wyniki.xlsx # Wyniki w arkuszu Excel
│   ├── figures/                    # Wygenerowane wykresy 300 DPI (.png)
│   ├── reports/                    # Gotowy Rozdział 5 i tabele LaTeX (.tex, .md)
│   └── logs/                       # Szczegółowe logi HTML z każdej debaty
└── main.py                         # Główny punkt wejściowy
```

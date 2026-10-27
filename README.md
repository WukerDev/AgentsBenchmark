# AiAgents Task Solving Benchmark 🚀
**Projekt Badawczy do Pracy Inżynierskiej**
*Porównanie skuteczności pojedynczego agenta (Solo ReAct) oraz roju wieloagentowego (Multi-Agent Swarm) na złożonych problemach analitycznych, logicznych i programistycznych.*

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

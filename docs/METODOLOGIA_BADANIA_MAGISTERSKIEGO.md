# Metodologia Badawcza do Pracy Magisterskiej 🎓
**Tytuł roboczy:** *Empiryczna analiza skuteczności i dynamiki roju wieloagentowego w porównaniu z zaawansowanymi baseline'ami jednoagentowymi przy zrównanym budżecie obliczeniowym na konsumenckim akceleratorze RTX 5080 (16 GB).*

---

## 1. Wprowadzenie i Teoretyczny Model Badawczy

Współczesne badania nad systemami opartymi na wielkich modelach językowych (LLM) koncentrują się na paradygmacie agentowym. W literaturze naukowej kluczowym pytaniem pozostaje:
> **Pytanie badawcze:** Czy wyższa skuteczność roju wieloagentowego (*Multi-Agent Swarm*) wynika z rzeczywistej synergii kognitywnej i podziału ról, czy jest jedynie artefaktem zwiększonego budżetu obliczeniowego w fazie wnioskowania (*Test-Time Compute Scaling*)?

Niniejsza platforma badawcza została zaprojektowana, aby odpowiedzieć na to pytanie z zachowaniem rygoru metodologicznego wymaganego w pracach magisterskich oraz publikacjach naukowych.

### 1.1. Formalizacja Matematyczna Grafu Roju
Rój wieloagentowy modelowany jest jako sterowany graf kognitywny $G = (V, E)$, gdzie:
- $V = \{v_{\text{orch}}, v_{\text{analyst}}, v_{\text{archivist}}, v_{\text{coder}}, v_{\text{qa}}, v_{\text{sec}}, v_{\text{fact}}, v_{\text{solver}}, v_{\text{devil}}, v_{\text{critic}}, v_{\text{secr}}\}$ to zbiór 10 wyspecjalizowanych agentów kognitywnych oraz koordynatora.
- $E \subseteq V \times V$ to dopuszczalne krawędzie przekazywania wątku. W przeciwieństwie do statycznych łańcuchów (Linear Chains), wybór następnika $v_{t+1} \in V$ w turze $t$ jest funkcją dyskusji i bieżącego stanu hipotezy:
  $$v_{t+1} = \operatorname{Orchestrator}(H_t, Q, v_t)$$
  gdzie $H_t$ oznacza historię wypowiedzi, a $Q$ treść zadania.

### 1.2. Model Pojedynczego Agenta ReAct
Architektura jednoagentowa bazuje na kanonicznym paradygmacie ReAct (Yao et al., 2022):
$$\text{Krok } t: \quad \tau_t = (\text{Thought}_t, \text{Action}_t, \text{Observation}_t)$$
Agent ma do dyspozycji interpreter kodu Python, kalkulator symboliczny oraz wyszukiwarkę.

---

## 2. Hipotezy Badawcze

W pracy weryfikowane są cztery główne hipotezy:
- **$H_1$ (Przewaga Merytoryczna):** Rój agentów osiąga statystycznie istotnie wyższy wynik punktowy ($p < 0.05$, test Wilcoxona, $d \ge 0.8$) niż pojedynczy agent ReAct na problemach trudnych (*hard*) wymagających wieloaspektowej weryfikacji.
- **$H_2$ (Synergia Ponad Skalowanie Tokenów):** Skuteczność roju przewyższa zaawansowany baseline **Solo Best-of-N** oraz **Solo Reflexion** przy zrównanym koszcie tokenowym, co dowodzi obecności synergii kognitywnej, a nie tylko efektu próbkowania.
- **$H_3$ (Istotność Roli Adwokata Diabła - Badanie Ablacyjne):** Usunięcie roli *Devil's Advocate* lub *Scientific Fact-Checker* prowadzi do mierzalnego wzrostu wskaźnika kaskadowych halucynacji (*Cascading Hallucinations*) oraz spadku wskaźnika samo-korekty (*Self-Correction Rate*).
- **$H_4$ (Wykonalność na Akceleratorze 16 GB):** Zastosowanie skwantyzowanych modeli 14B (Q4_K_M) na architekturze NVIDIA GeForce RTX 5080 pozwala na stabilną realizację pełnej 15-turowej debaty bez przepełnienia bufora VRAM (Peak VRAM < 15.5 GB).

---

## 3. Zrównanie Kosztu Obliczeniowego (Compute & Token Parity Baselines)

Podstawowy zarzut recenzentów wobec badań wieloagentowych brzmi: *„Swarm wygrał, bo zużył 5-10× więcej tokenów”*. Aby wykluczyć ten zarzut, zaimplementowano dwa zaawansowane baseline'y:

```
[Problem Q]
   │
   ├───> 1. Solo ReAct (Pojedyncza próba, niski koszt: ~800 tokenów)
   │
   ├───> 2. Solo Best-of-N / Self-Consistency (3 niezależne próby + synteza: ~2 500 tokenów)
   │
   ├───> 3. Solo Reflexion (Szkic -> Rygorystyczna samo-krytyka -> Korekta: ~2 800 tokenów)
   │
   └───> 4. Multi-Agent Swarm (Wieloosobowa debata, krzyżowy audyt: ~8 000 - 15 000 tokenów)
```

1. **Solo Best-of-N (`SoloBestOfNRunner`)**:
   - Generuje $N=3$ niezależne trajektorie rozwiązania przy podwyższonej temperaturze ($T=0.7$).
   - Osobny prompt selekcyjny syntetyzuje najlepszą odpowiedź, eliminując przypadkowe błędy pojedynczego przebiegu.
2. **Solo Reflexion (`SoloReflexionRunner`)** (Shinn et al., 2023):
   - Etap 1: Wygenerowanie szkicu rozwiązania.
   - Etap 2: Wymuszenie na modelu roli wewnętrznego krytyka (*Self-Critique*), który punktuje luki logiczne i błędy założeń.
   - Etap 3: Zredagowanie poprawionej wersji finałowej uwzględniającej uwagi.

---

## 4. Metodyka Badań Ablacyjnych (Ablation Study)

Ablacja polega na systematycznym wyłączaniu komponentów systemu w celu zmierzenia ich wkładu krańcowego. Zdefiniowano 5 formalnych wariantów:

| Identyfikator Wariantu | Nazwa | Wykluczone Role | Pytanie Badawcze |
| :--- | :--- | :--- | :--- |
| `full_swarm` | Pełny Rój (10 ról) | *Brak (układ referencyjny)* | Stan wyjściowy. |
| `no_devil` | Rój bez Devil's Advocate | `devil` | Czy brak sceptyka zwiększa podatność na uległość (*sycophancy*) i konformizm? |
| `no_fact_checker` | Rój bez Weryfikatorów | `fact_checker`, `security_auditor` | Jak brak dedykowanych audytorów wpływa na błędy fizykalne i luki bezpieczeństwa? |
| `no_coder_qa` | Czysty Rozum (Bez Kodu) | `coder`, `qa_engineer` | Czy debata czysto werbalna potrafi zastąpić deterministyczną egzekucję kodu? |
| `minimal_triad` | Minimalistyczna Triada | Wszystkie prócz: `orch`, `solver`, `secr` | Czy podział pracy na 10 agentów jest uzasadniony w porównaniu z prostą strukturą 3-agentową? |

---

## 5. Taksonomia Błędów Roju (Failure Mode Taxonomy)

W pracy magisterskiej analiza jakościowa przyczyn porażek jest równie ważna jak statystyka punktowa. Moduł `FailureTaxonomy` kategoryzuje niepowodzenia (wynik < 75%) według 6 formalnych wzorców:

1. **Kaskada Halucynacji (*Cascading Hallucination*)**:
   Jeden z agentów (np. Analyst) wprowadza fałszywą przesłankę, a kolejni agenci przyjmują ją bez weryfikacji jako twardy fakt, budując na niej całe rozwiązanie.
2. **Konformizm Grupowy / Uległość (*Groupthink & Sycophancy*)**:
   Krytyk lub Adwokat Diabła bezkrytycznie akceptują propozycję Codera/Solvera, mimo obecności subtelnego błędu logicznego.
3. **Rozmycie Kontekstu (*Context Dilution*)**:
   W miarę rozrostu historii debaty (powyżej 10 tur / 12 000 tokenów) model traci z pola widzenia kluczowe ograniczenia podane w pierwotnym zapytaniu.
4. **Błąd Wykonania Narzędzia (*Tool Execution Failure*)**:
   Skrypt Python zgłasza nieobsłużony wyjątek lub timeout, którego QA Engineer nie zdołał naprawić w kolejnej turze.
5. **Przedwczesna Konwergencja (*Premature Convergence*)**:
   Orchestrator kieruje wątek do Sekretarza przed zakończeniem pełnego cyklu weryfikacji (np. w 3. turze).
6. **Przekroczenie Limitu Tur (*No-Consensus Timeout*)**:
   Dyskusja osiąga maksymalny limit 15 tur z powodu zapętlenia wymiany zdań między Coderem a QA.

---

## 6. Profilowanie Sprzętowe na NVIDIA GeForce RTX 5080 (16 GB GDDR7)

Projekt bada wykonalność zaawansowanych systemów roju na najnowszej generacji konsumenckich GPU z architekturą NVIDIA Blackwell:
- **Pojemność VRAM:** 16 303 MB GDDR7.
- **Zarządzanie Pamięcią:** Dynamiczne monitorowanie `used_vram_mb`, `free_vram_mb`, `temperature_c` oraz `utilization_pct` w trakcie każdej tury.
- **Bufor KV-Cache:** Analiza narzutu pamięciowego w funkcji długości kontekstu (od 1 000 do 16 000 tokenów).
- **Przepustowość:** Pomiar średniej szybkości generowania w tokenach na sekundę ($Tokens/s$) dla modeli z rodziny 14B Q4_K_M.

---

## 7. Rygor Statystyczny i Metryki Oceny

1. **Test Rang Przykrytych Wilcoxona dla Prób Zależnych:**
   Weryfikacja hipotezy zerowej $H_0: \mu_{\text{multi}} = \mu_{\text{solo}}$ przy poziomie istotności $\alpha = 0.05$.
2. **Standaryzowana Wielkość Efektu $d$ Cohena:**
   $$d = \frac{\bar{X}_{\text{multi}} - \bar{X}_{\text{solo}}}{s_{\text{diff}}}$$
   Interpretacja: $d \ge 0.8$ oznacza duży efekt praktyczny.
3. **Współczynnik Zgodności Sędziów Kendalla ($W$):**
   Ocena spójności 3-modelowego panelu sędziowskiego (Phi-4, Qwen 2.5, Mistral-NeMo).
4. **Przedziały Ufności 95% CI:**
   Wyznaczane z rozkładu $t$-Studenta dla średnich wyników punktowych:
   $$\bar{X} \pm t_{\alpha/2, n-1} \cdot \frac{s}{\sqrt{n}}$$

---

## 8. Wykorzystanie w CLI i REST API

Wszystkie moduły magisterskie są w pełni zintegrowane z backendem i GUI:
- `src/agents/baselines.py`: `SoloBestOfNRunner`, `SoloReflexionRunner`
- `src/benchmark/ablation.py`: `ABLATION_VARIANTS`, `create_ablation_runner`
- `src/evaluation/failure_taxonomy.py`: `FailureTaxonomy.analyze_dataset`
- `src/hardware/telemetry.py`: `HardwareProfiler.get_gpu_status`
- Endpointy REST:
  - `GET /api/ablation/variants`
  - `GET /api/hardware/telemetry`
  - `GET /api/reports/thesis-methodology`

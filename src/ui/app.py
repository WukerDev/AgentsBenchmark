from __future__ import annotations
import os
import json
from pathlib import Path
import streamlit as st
import pandas as pd

from src.config import config, BASE_DIR, CONFIG_DIR
from src.agents.solo_agent import SoloAgentRunner
from src.agents.group_chat import MultiAgentSwarmRunner, load_agents_config
from src.evaluation.ground_truth import GroundTruthVerifier
from src.evaluation.jury import LLMJury
from src.evaluation.statistics import compute_benchmark_statistics
from src.storage.excel_exporter import ExcelBenchmarkExporter
from src.storage.latex_exporter import LatexExporter
from src.visualization.plots import BenchmarkVisualizer

st.set_page_config(
    page_title="AiAgents Benchmark Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.05rem; color: #4B5563; margin-bottom: 1.5rem; }
    .agent-card { padding: 1rem; border-radius: 0.75rem; border: 1px solid #E5E7EB; background: #FFFFFF; margin-bottom: 0.75rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 1rem; }
    .stTabs [data-baseweb="tab"] { font-size: 1.05rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

tasks_path = CONFIG_DIR / "tasks.json"
if not tasks_path.exists():
    tasks_path = BASE_DIR / "tasks.json"

with open(tasks_path, "r", encoding="utf-8") as f:
    ALL_TASKS = json.load(f)

st.sidebar.title("⚙️ Konfiguracja Badania")
provider = st.sidebar.selectbox(
    "Dostawca Modeli (Provider):",
    ["ollama", "groq", "openai", "openrouter"],
    index=["ollama", "groq", "openai", "openrouter"].index(config.system.default_provider)
)

st.sidebar.markdown(f"**Tryb:** `{ 'Lokalny (Ollama)' if provider == 'ollama' else 'API Chmurowe' }`")
if provider != "ollama":
    api_key = config.get_api_key(provider)
    if api_key:
        st.sidebar.success(f"Klucz API dla `{provider}`: Wykryty ✅")
    else:
        st.sidebar.warning(f"Brak klucza `{provider.upper()}_API_KEY` w .env!")

st.sidebar.markdown("---")
categories = sorted(list(set(t.get("category", "ogólne") for t in ALL_TASKS)))
selected_category = st.sidebar.selectbox("Filtruj zadania wg kategorii:", ["Wszystkie"] + categories)

filtered_tasks = ALL_TASKS if selected_category == "Wszystkie" else [t for t in ALL_TASKS if t.get("category") == selected_category]
task_ids = [t["id"] for t in filtered_tasks]
selected_task_id = st.sidebar.selectbox("Wybierz zadanie:", task_ids)
current_task = next(t for t in filtered_tasks if t["id"] == selected_task_id)

st.markdown('<div class="main-header">AiAgents Task Solving Benchmark</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Platforma badawcza: Solo ReAct vs Multi-Agent Swarm (Projekt Inżynierski)</div>', unsafe_allow_html=True)

tab_test, tab_results, tab_latex = st.tabs(["🧪 Interaktywny Test Zadania", "📊 Wyniki Zbiorcze & Statystyki", "📄 Eksport do Pracy (LaTeX & Excel)"])

with tab_test:
    st.subheader(f"Zadanie: `{current_task['id']}`")
    col_q, col_ans = st.columns([2, 1])
    with col_q:
        st.info(f"**Pytanie / Problem:**\n\n{current_task['query']}")
    with col_ans:
        st.success(f"**Wzorzec (Ground Truth):**\n\n{current_task.get('expected_answer', 'Brak')}")

    if st.button("🚀 Uruchom Test Porównawczy dla tego Zadania", type="primary", use_container_width=True):
        col_solo, col_multi = st.columns(2)

        with col_solo:
            st.markdown("### 👤 Solo Agent (ReAct)")
            solo_status = st.empty()
            solo_status.info("Uruchamianie agenta Solo...")
            solo_runner = SoloAgentRunner(provider=provider)
            solo_res = solo_runner.run(current_task["query"])
            solo_status.empty()

            st.write(f"⏱️ Czas: **{solo_res['total_time']}s** (Gen: {solo_res['generation_time']}s, Narzędzia: {solo_res['tool_time']}s)")
            st.write(f"🪙 Koszt: **${solo_res['cost']:.4f}** | Tokeny: **{solo_res['tokens']}** | Tury: **{solo_res['turns']}**")
            with st.expander("Pełna historia myślenia i narzędzi Solo", expanded=False):
                st.text(solo_res["chat_history"])
            st.markdown("**Odpowiedź Solo:**")
            st.text_area("", value=solo_res["final_answer"], height=160, key="solo_ans_box", disabled=True)

        with col_multi:
            st.markdown("### 🐝 Multi-Agent Swarm")
            multi_status = st.empty()
            multi_status.info("Uruchamianie zespołu agentów...")
            multi_runner = MultiAgentSwarmRunner(provider=provider)
            group_res = multi_runner.run(current_task["query"])
            multi_status.empty()

            st.write(f"⏱️ Czas: **{group_res['total_time']}s** (Gen: {group_res['generation_time']}s, Narzędzia: {group_res['tool_time']}s)")
            st.write(f"🪙 Koszt: **${group_res['cost']:.4f}** | Tokeny: **{group_res['tokens']}** | Tury: **{group_res['turns']}**")
            st.markdown(f"**Ścieżka agentów:** `{group_res.get('agent_path', '')}`")

            with st.expander("Przebieg dyskusji w zespole", expanded=False):
                st.text(group_res["chat_history"])
            st.markdown("**Końcowa odpowiedź zespołu (Sekretarz):**")
            st.text_area("", value=group_res["final_answer"], height=160, key="multi_ans_box", disabled=True)

        st.markdown("---")
        st.subheader("⚖️ Werdykt Sędziowski & Weryfikacja")

        gt_score, gt_ok, gt_expl = GroundTruthVerifier.verify(current_task["id"], group_res["final_answer"])
        gt_solo_score, gt_solo_ok, gt_solo_expl = GroundTruthVerifier.verify(current_task["id"], solo_res["final_answer"])

        col_gt1, col_gt2 = st.columns(2)
        with col_gt1:
            st.metric("Solo Ground Truth", f"{gt_solo_score}/100", delta="Poprawny" if gt_solo_ok else "Niepoprawny")
            st.caption(gt_solo_expl)
        with col_gt2:
            st.metric("Multi Ground Truth", f"{gt_score}/100", delta="Poprawny" if gt_ok else "Niepoprawny")
            st.caption(gt_expl)

        jury = LLMJury(provider=provider)
        jury_res = jury.evaluate(
            current_task["query"],
            current_task["expected_answer"],
            solo_res["final_answer"],
            group_res["snapshot_5"],
            group_res["snapshot_10"],
            group_res["final_answer"]
        )

        col_j1, col_j2, col_j3, col_j4 = st.columns(4)
        col_j1.metric("Jury Solo", f"{jury_res.score_solo:.0f}/100")
        col_j2.metric("Jury Multi (Tura 5)", f"{jury_res.score_multi_5:.0f}/100")
        col_j3.metric("Jury Multi (Tura 10)", f"{jury_res.score_multi_10:.0f}/100")
        col_j4.metric("Jury Multi (Finał)", f"{jury_res.score_multi_final:.0f}/100")

        st.info(f"**Uzasadnienie Sędziów:**\n\n{jury_res.jury_reasons}")

with tab_results:
    st.subheader("Baza Danych Wyników Badania")
    chk_file = BASE_DIR / config.system.checkpoint_file
    if chk_file.exists():
        records = []
        with open(chk_file, "r", encoding="utf-8") as f:
            for l in f:
                if l.strip():
                    records.append(json.loads(l))

        if records:
            df = pd.DataFrame(records)
            st.dataframe(df, use_container_width=True)

            stats = compute_benchmark_statistics(df)
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            col_s1.metric("Średni Wynik Solo", f"{stats.get('solo_mean', 0)} pkt")
            col_s2.metric("Średni Wynik Multi", f"{stats.get('multi_mean', 0)} pkt", delta=f"{stats.get('score_delta', 0)} pkt")
            col_s3.metric("Multi Win Rate", f"{stats.get('multi_win_rate', 0)}%")
            col_s4.metric("Wilcoxon p-value", f"{stats.get('wilcoxon_pvalue', 'N/A')}")

            st.markdown("---")
            st.subheader("Wykresy do Pracy Inżynierskiej")
            fig_dir = BASE_DIR / "results" / "figures"
            BenchmarkVisualizer.generate_all_plots(df, fig_dir, show=False)

            if (fig_dir / "dashboard_porownawczy.png").exists():
                st.image(str(fig_dir / "dashboard_porownawczy.png"), caption="Podsumowanie Ogólne", use_container_width=True)
            if (fig_dir / "kategorie_porownanie.png").exists():
                st.image(str(fig_dir / "kategorie_porownanie.png"), caption="Skuteczność wg Kategorii", use_container_width=True)
        else:
            st.warning("Brak zapisanych wyników w pliku checkpoint. Uruchom badanie, aby wygenerować statystyki.")
    else:
        st.warning("Plik wyników jeszcze nie istnieje. Uruchom badanie w konsoli lub interfejsie.")

with tab_latex:
    st.subheader("Gotowe Tabele LaTeX do Wklejenia w Pracy Inżynierskiej")
    reports_dir = BASE_DIR / "results" / "reports"
    tabela_wynikow = reports_dir / "tabela_wynikow.tex"
    tabela_kategorii = reports_dir / "tabela_kategorii.tex"
    tabela_statystyk = reports_dir / "tabela_statystyk.tex"

    if tabela_wynikow.exists():
        with open(tabela_wynikow, "r", encoding="utf-8") as f:
            st.code(f.read(), language="latex")
    else:
        st.info("Tabele LaTeX zostaną wygenerowane automatycznie po zakończeniu badania (`python main.py run` lub `python main.py report`).")

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import pandas as pd

class LatexExporter:
    @classmethod
    def export(cls, output_dir: Path, df: pd.DataFrame, stats: Dict[str, Any]):
        output_dir.mkdir(parents=True, exist_ok=True)

        if df.empty:
            return

        # 1. Main Detailed Results Table
        table_rows = []
        for _, r in df.iterrows():
            tid = str(r.get("task_id", "")).replace("_", "\\_")
            cat = str(r.get("category", "")).replace("_", " ").title()
            diff = str(r.get("difficulty", "medium")).capitalize()
            s_solo = f"{r.get('score_solo', 0):.0f}"
            s_multi = f"{r.get('score_multi_final', 0):.0f}"
            t_solo = f"{r.get('solo_time', 0):.1f}s"
            t_multi = f"{r.get('multi_time', 0):.1f}s"

            if float(r.get("score_multi_final", 0)) > float(r.get("score_solo", 0)):
                s_multi = f"\\textbf{{{s_multi}}}"
            elif float(r.get("score_solo", 0)) > float(r.get("score_multi_final", 0)):
                s_solo = f"\\textbf{{{s_solo}}}"

            table_rows.append(f"{tid} & {diff} & {s_solo} & {s_multi} & {t_solo} & {t_multi} \\\\")

        main_latex = f"""\\begin{{table}}[htbp]
\\centering
\\small
\\caption{{Szczegółowe wyniki porównania Solo ReAct vs Multi-Agent Swarm (N={len(df)})}}
\\label{{tab:benchmark_wyniki_szczegolowe}}
\\begin{{tabular}}{{lccccc}}
\\hline
\\textbf{{Zadanie}} & \\textbf{{Trudność}} & \\textbf{{Solo Score}} & \\textbf{{Multi Score}} & \\textbf{{Czas Solo}} & \\textbf{{Czas Multi}} \\\\
\\hline
""" + "\n".join(table_rows) + f"""
\\hline
\\textbf{{ŚREDNIA}} & - & \\textbf{{{stats.get('solo_mean', 0)}}} & \\textbf{{{stats.get('multi_mean', 0)}}} & - & - \\\\
\\hline
\\end{{tabular}}
\\end{{table}}
"""
        with open(output_dir / "tabela_wynikow.tex", "w", encoding="utf-8") as f:
            f.write(main_latex)

        # 2. Category Breakdown Table
        if "category" in df:
            cat_df = df.groupby("category").agg(
                Liczba=("task_id", "count"),
                Solo=("score_solo", "mean"),
                Multi=("score_multi_final", "mean"),
                SoloTime=("solo_time", "mean"),
                MultiTime=("multi_time", "mean")
            ).round(1).reset_index()
            cat_df["Delta"] = (cat_df["Multi"] - cat_df["Solo"]).round(1)

            cat_rows = []
            for _, cr in cat_df.iterrows():
                cname = str(cr["category"]).replace("_", " ").title()
                delta_str = f"+{cr['Delta']:.1f}" if cr["Delta"] > 0 else f"{cr['Delta']:.1f}"
                cat_rows.append(f"{cname} & {int(cr['Liczba'])} & {cr['Solo']:.1f} & {cr['Multi']:.1f} & \\textbf{{{delta_str}}} & {cr['SoloTime']:.1f}s & {cr['MultiTime']:.1f}s \\\\")

            cat_latex = f"""\\begin{{table}}[htbp]
\\centering
\\caption{{Wyniki badania zagregowane według dziedziny (kategorii)}}
\\label{{tab:kategorie_wyniki}}
\\begin{{tabular}}{{lcccccc}}
\\hline
\\textbf{{Kategoria}} & \\textbf{{N}} & \\textbf{{Solo}} & \\textbf{{Multi}} & \\textbf{{Delta}} & \\textbf{{Czas Solo}} & \\textbf{{Czas Multi}} \\\\
\\hline
""" + "\n".join(cat_rows) + """
\\hline
\\end{{tabular}}
\\end{{table}}
"""
            with open(output_dir / "tabela_kategorii.tex", "w", encoding="utf-8") as f:
                f.write(cat_latex)

        # 3. Difficulty Scaling Table
        if "difficulty" in df:
            diff_df = df.groupby("difficulty").agg(
                Liczba=("task_id", "count"),
                Solo=("score_solo", "mean"),
                Multi=("score_multi_final", "mean"),
                SoloTok=("solo_tokens", "mean"),
                MultiTok=("multi_tokens", "mean")
            ).round(1).reset_index()
            diff_df["Delta"] = (diff_df["Multi"] - diff_df["Solo"]).round(1)

            diff_rows = []
            for _, dr in diff_df.iterrows():
                dname = str(dr["difficulty"]).capitalize()
                delta_str = f"+{dr['Delta']:.1f}" if dr["Delta"] > 0 else f"{dr['Delta']:.1f}"
                diff_rows.append(f"{dname} & {int(dr['Liczba'])} & {dr['Solo']:.1f} & {dr['Multi']:.1f} & \\textbf{{{delta_str}}} & {dr['SoloTok']:.0f} & {dr['MultiTok']:.0f} \\\\")

            diff_latex = f"""\\begin{{table}}[htbp]
\\centering
\\caption{{Skuteczność architektur w zależności od poziomu trudności zadania}}
\\label{{tab:trudnosc_skalowanie}}
\\begin{{tabular}}{{lcccccc}}
\\hline
\\textbf{{Poziom Trudności}} & \\textbf{{N}} & \\textbf{{Solo Score}} & \\textbf{{Multi Score}} & \\textbf{{Delta}} & \\textbf{{Tokeny Solo}} & \\textbf{{Tokeny Multi}} \\\\
\\hline
""" + "\n".join(diff_rows) + """
\\hline
\\end{{tabular}}
\\end{{table}}
"""
            with open(output_dir / "tabela_trudnosci.tex", "w", encoding="utf-8") as f:
                f.write(diff_latex)

        # 4. Turn Evolution & Debate Table
        if "score_multi_5" in df and "score_multi_10" in df:
            g5 = df['score_multi_5'].mean() - df['score_solo'].mean()
            g10 = df['score_multi_10'].mean() - df['score_solo'].mean()
            gfin = float(stats.get('score_delta', 0))
            g5_str = f"+{g5:.1f}" if g5 > 0 else f"{g5:.1f}"
            g10_str = f"+{g10:.1f}" if g10 > 0 else f"{g10:.1f}"
            gfin_str = f"+{gfin:.1f}" if gfin > 0 else f"{gfin:.1f}"

            evo_latex = f"""\\begin{{table}}[htbp]
\\centering
\\caption{{Ewolucja jakości odpowiedzi w trakcie debaty wieloagentowej}}
\\label{{tab:ewolucja_debaty}}
\\begin{{tabular}}{{lcccc}}
\\hline
\\textbf{{Etap Ewaluacji}} & \\textbf{{Średni Wynik}} & \\textbf{{Odchylenie Std.}} & \\textbf{{Zysk vs Solo}} \\\\
\\hline
Solo ReAct & {stats.get('solo_mean', 0)} & {stats.get('solo_std', 0)} & - \\\\
Multi-Agent (Tura 5) & {df['score_multi_5'].mean():.1f} & {df['score_multi_5'].std():.1f} & {g5_str} \\\\
Multi-Agent (Tura 10) & {df['score_multi_10'].mean():.1f} & {df['score_multi_10'].std():.1f} & {g10_str} \\\\
Multi-Agent (Finał) & {stats.get('multi_mean', 0)} & {stats.get('multi_std', 0)} & {gfin_str} \\\\
\\hline
\\end{{tabular}}
\\end{{table}}
"""
            with open(output_dir / "tabela_ewolucji_debaty.tex", "w", encoding="utf-8") as f:
                f.write(evo_latex)

        # 5. Scientific Statistics & Hypothesis Testing Table
        stat_latex = f"""\\begin{{table}}[htbp]
\\centering
\\caption{{Weryfikacja istotności statystycznej i rozmiar efektu (Solo vs Multi-Agent)}}
\\label{{tab:statystyka_istotnosci}}
\\begin{{tabular}}{{lcc}}
\\hline
\\textbf{{Parametr / Test Statystyczny}} & \\textbf{{Wartość Statystyki}} & \\textbf{{Interpretacja}} \\\\
\\hline
Liczebność próby ($N$) & {stats.get('n_tasks', len(df))} & Liczba zbadanych zadań \\\\
Różnica średnich ($\\Delta$) & {stats.get('score_delta', 'N/A')} pkt & Przewaga roju agentów \\\\
Rozmiar efektu (Cohen's $d$) & {stats.get('cohens_d', 'N/A')} & Efekt ustandaryzowany \\\\
Wskaźnik zwycięstw (Win Rate) & {stats.get('multi_win_rate', 'N/A')}\\% & Wygrane zadania Multi \\\\
Test t-Studenta (sparowany, $p$-value) & {stats.get('t_test_pvalue', 'N/A')} & Istotny: {stats.get('t_test_significant', 'N/A')} \\\\
Test rang znakowanych Wilcoxona ($p$-value) & {stats.get('wilcoxon_pvalue', 'N/A')} & Istotny: {stats.get('wilcoxon_significant', 'N/A')} \\\\
Zgodność sędziów (Jury Std Dev) & {stats.get('mean_jury_std_dev', 'N/A')} pkt & Rozrzut ocen panelu \\\\
\\hline
\\multicolumn{{3}}{{l}}{{\\footnotesize * Poziom istotności $\\alpha = 0.05$. Test Wilcoxona odporny na brak normalności rozkładu.}} \\\\
\\hline
\\end{{tabular}}
\\end{{table}}
"""
        with open(output_dir / "tabela_statystyk.tex", "w", encoding="utf-8") as f:
            f.write(stat_latex)

        # 6. Failure Taxonomy Table (Master's level qualitative analysis)
        tax_info = stats.get("failure_taxonomy", {})
        breakdown = tax_info.get("breakdown", [])
        tax_rows = []
        for b in breakdown:
            tax_rows.append(f"{b['category']} & {b['count']} & {b['percentage']}\\% \\\\")

        tax_latex = f"""\\begin{{table}}[htbp]
\\centering
\\caption{{Taksonomia błędów i patologii komunikacji roju wieloagentowego}}
\\label{{tab:taksonomia_bledow}}
\\begin{{tabular}}{{lcc}}
\\hline
\\textbf{{Kategoria Zjawiska / Błędu}} & \\textbf{{Liczba Przypadków}} & \\textbf{{Udział Procentowy}} \\\\
\\hline
""" + "\n".join(tax_rows) + f"""
\\hline
\\textbf{{Łącznie zadań}} & {tax_info.get('total_tasks', len(df))} & 100.0\\% \\\\
\\textbf{{Skuteczność całkowita (brak błędu)}} & - & \\textbf{{{tax_info.get('success_rate', 100.0)}\\%}} \\\\
\\hline
\\end{{tabular}}
\\end{{table}}
"""
        with open(output_dir / "tabela_taksonomii_bledow.tex", "w", encoding="utf-8") as f:
            f.write(tax_latex)

        # 7. Confidence Intervals Table (95% CI)
        solo_ci = stats.get("solo_ci", {})
        multi_ci = stats.get("multi_ci", {})
        ci_latex = f"""\\begin{{table}}[htbp]
\\centering
\\caption{{Przedziały ufności 95\\% CI dla średnich wyników punktowych (Rozkład $t$-Studenta)}}
\\label{{tab:przedzialy_ufnosci}}
\\begin{{tabular}}{{lcccc}}
\\hline
\\textbf{{Architektura}} & \\textbf{{Średnia (Mean)}} & \\textbf{{Odchylenie Std.}} & \\textbf{{Błąd Marginesu ($\\pm h$)}} & \\textbf{{95\\% Przedział Ufności}} \\\\
\\hline
Solo ReAct & {solo_ci.get('mean', 0.0):.2f} & {solo_ci.get('std', 0.0):.2f} & $\\pm {solo_ci.get('margin', 0.0):.2f}$ & [{solo_ci.get('ci_lower', 0.0):.2f}, {solo_ci.get('ci_upper', 0.0):.2f}] \\\\
Multi-Agent Swarm & {multi_ci.get('mean', 0.0):.2f} & {multi_ci.get('std', 0.0):.2f} & $\\pm {multi_ci.get('margin', 0.0):.2f}$ & [{multi_ci.get('ci_lower', 0.0):.2f}, {multi_ci.get('ci_upper', 0.0):.2f}] \\\\
\\hline
\\end{{tabular}}
\\end{{table}}
"""
        with open(output_dir / "tabela_przedzialow_ufnosci.tex", "w", encoding="utf-8") as f:
            f.write(ci_latex)

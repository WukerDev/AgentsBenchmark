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

        table_rows = []
        for _, r in df.iterrows():
            tid = str(r.get("task_id", "")).replace("_", "\\_")
            s_solo = f"{r.get('score_solo', 0):.0f}"
            s_multi = f"{r.get('score_multi_final', 0):.0f}"
            t_solo = f"{r.get('solo_time', 0):.1f}s"
            t_multi = f"{r.get('multi_time', 0):.1f}s"

            if float(r.get("score_multi_final", 0)) > float(r.get("score_solo", 0)):
                s_multi = f"\\textbf{{{s_multi}}}"
            elif float(r.get("score_solo", 0)) > float(r.get("score_multi_final", 0)):
                s_solo = f"\\textbf{{{s_solo}}}"

            table_rows.append(f"{tid} & {s_solo} & {s_multi} & {t_solo} & {t_multi} \\\\")

        main_latex = f"""\\begin{{table}}[htbp]
\\centering
\\caption{{Porównanie skuteczności Solo ReAct vs Multi-Agent Swarm}}
\\label{{tab:benchmark_wyniki}}
\\begin{{tabular}}{{lcccc}}
\\hline
\\textbf{{Zadanie}} & \\textbf{{Solo Score}} & \\textbf{{Multi Score}} & \\textbf{{Solo Czas}} & \\textbf{{Multi Czas}} \\\\
\\hline
""" + "\n".join(table_rows) + f"""
\\hline
\\textbf{{ŚREDNIA}} & \\textbf{{{stats.get('solo_mean', 0)}}} & \\textbf{{{stats.get('multi_mean', 0)}}} & - & - \\\\
\\hline
\\end{{tabular}}
\\end{{table}}
"""
        with open(output_dir / "tabela_wynikow.tex", "w", encoding="utf-8") as f:
            f.write(main_latex)

        if "category" in df:
            cat_df = df.groupby("category").agg(
                Liczba=("task_id", "count"),
                Solo=("score_solo", "mean"),
                Multi=("score_multi_final", "mean"),
                SoloTime=("solo_time", "mean"),
                MultiTime=("multi_time", "mean")
            ).round(1).reset_index()

            cat_rows = []
            for _, cr in cat_df.iterrows():
                cname = str(cr["category"]).replace("_", " ").title()
                cat_rows.append(f"{cname} & {int(cr['Liczba'])} & {cr['Solo']:.1f} & {cr['Multi']:.1f} & {cr['SoloTime']:.1f}s & {cr['MultiTime']:.1f}s \\\\")

            cat_latex = f"""\\begin{{table}}[htbp]
\\centering
\\caption{{Wyniki badania z podziałem na kategorie zadań}}
\\label{{tab:kategorie_wyniki}}
\\begin{{tabular}}{{lccccc}}
\\hline
\\textbf{{Kategoria}} & \\textbf{{Liczba}} & \\textbf{{Solo}} & \\textbf{{Multi-Agent}} & \\textbf{{Czas Solo}} & \\textbf{{Czas Multi}} \\\\
\\hline
""" + "\n".join(cat_rows) + """
\\hline
\\end{{tabular}}
\\end{{table}}
"""
            with open(output_dir / "tabela_kategorii.tex", "w", encoding="utf-8") as f:
                f.write(cat_latex)

        stat_latex = f"""\\begin{{table}}[htbp]
\\centering
\\caption{{Weryfikacja istotności statystycznej (Solo vs Multi-Agent)}}
\\label{{tab:statystyka_istotnosci}}
\\begin{{tabular}}{{lcc}}
\\hline
\\textbf{{Test Statystyczny}} & \\textbf{{Wartość Statystyki}} & \\textbf{{Wartość p (p-value)}} \\\\
\\hline
Test t-Studenta (sparowany) & {stats.get('t_test_stat', 'N/A')} & {stats.get('t_test_pvalue', 'N/A')} \\\\
Test rang znakowanych Wilcoxona & {stats.get('wilcoxon_stat', 'N/A')} & {stats.get('wilcoxon_pvalue', 'N/A')} \\\\
\\hline
\\multicolumn{{3}}{{l}}{{\\footnotesize * Istotność statystyczna na poziomie $\\alpha = 0.05$: {stats.get('wilcoxon_significant', 'N/A')}}} \\\\
\\hline
\\end{{tabular}}
\\end{{table}}
"""
        with open(output_dir / "tabela_statystyk.tex", "w", encoding="utf-8") as f:
            f.write(stat_latex)

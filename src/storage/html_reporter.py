from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import json

class HTMLReporter:
    """
    Generates modern, interactive HTML reports for benchmark tasks and overall research run.
    """

    @classmethod
    def generate_task_log(
        cls,
        output_path: Path,
        task_id: str,
        query: str,
        expected: str,
        solo_res: Dict[str, Any],
        group_res: Dict[str, Any],
        scores: Dict[str, Any]
    ):
        output_path.parent.mkdir(parents=True, exist_ok=True)

        solo_history_html = solo_res.get("chat_history", "").replace("\n", "<br>")
        multi_history = group_res.get("chat_history", "")

        # Format multi-agent history into nice speech cards
        cards_html = ""
        parts = multi_history.split("---")
        for part in parts:
            part_str = part.strip()
            if not part_str:
                continue
            lines = part_str.split("\n", 1)
            role_header = lines[0].strip()
            msg_content = lines[1].strip() if len(lines) > 1 else ""

            # Assign colors
            badge_color = "bg-blue-100 text-blue-800"
            if "Orchestrator" in role_header or "Kierownik" in role_header:
                badge_color = "bg-purple-100 text-purple-800"
            elif "Coder" in role_header or "Programista" in role_header:
                badge_color = "bg-cyan-100 text-cyan-800"
            elif "Adwokat" in role_header or "devil" in role_header:
                badge_color = "bg-red-100 text-red-800"
            elif "Krytyk" in role_header or "critic" in role_header:
                badge_color = "bg-yellow-100 text-yellow-800"
            elif "Sekretarz" in role_header:
                badge_color = "bg-green-100 text-green-800"

            cards_html += f"""
            <div class="mb-4 p-4 rounded-xl border border-gray-200 bg-white shadow-sm">
                <div class="inline-block px-3 py-1 rounded-full text-xs font-semibold {badge_color} mb-2">
                    {role_header}
                </div>
                <div class="text-sm text-gray-800 leading-relaxed font-mono whitespace-pre-wrap">{msg_content}</div>
            </div>
            """

        html_content = f"""<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zadanie {task_id} - Log Badania</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>body {{ font-family: 'Inter', sans-serif; }}</style>
</head>
<body class="bg-gray-50 min-h-screen text-gray-900 p-6 md:p-12">
    <div class="max-w-6xl mx-auto">
        <!-- Header -->
        <div class="mb-8">
            <a href="../index.html" class="text-blue-600 hover:underline text-sm font-medium">&larr; Powrót do pulpitu wyników</a>
            <h1 class="text-3xl font-bold mt-2 text-gray-900">{task_id}</h1>
            <div class="mt-4 p-4 rounded-xl bg-blue-50 border border-blue-200">
                <div class="text-xs font-semibold text-blue-700 uppercase tracking-wider">Treść zadania</div>
                <div class="text-base text-blue-950 font-medium mt-1">{query}</div>
                <div class="mt-3 pt-3 border-t border-blue-200">
                    <span class="text-xs font-semibold text-blue-700 uppercase">Wzorzec (Ground Truth):</span>
                    <span class="text-sm text-blue-900 ml-1">{expected}</span>
                </div>
            </div>
        </div>

        <!-- Scores bar -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div class="p-4 bg-white rounded-xl shadow-sm border border-gray-200">
                <div class="text-xs text-gray-500 font-medium">Solo ReAct Score</div>
                <div class="text-2xl font-bold text-gray-800 mt-1">{scores.get('score_solo', 0)} / 100</div>
                <div class="text-xs text-gray-400 mt-1">Czas: {solo_res.get('total_time', 0)}s | Koszt: ${solo_res.get('cost', 0):.4f}</div>
            </div>
            <div class="p-4 bg-white rounded-xl shadow-sm border border-gray-200">
                <div class="text-xs text-gray-500 font-medium">Multi-Agent Tura 5</div>
                <div class="text-2xl font-bold text-blue-600 mt-1">{scores.get('score_multi_5', 0)} / 100</div>
            </div>
            <div class="p-4 bg-white rounded-xl shadow-sm border border-gray-200">
                <div class="text-xs text-gray-500 font-medium">Multi-Agent Tura 10</div>
                <div class="text-2xl font-bold text-indigo-600 mt-1">{scores.get('score_multi_10', 0)} / 100</div>
            </div>
            <div class="p-4 bg-white rounded-xl shadow-sm border border-gray-200">
                <div class="text-xs text-gray-500 font-medium">Multi-Agent Finał</div>
                <div class="text-2xl font-bold text-green-600 mt-1">{scores.get('score_multi_final', 0)} / 100</div>
                <div class="text-xs text-gray-400 mt-1">Czas: {group_res.get('total_time', 0)}s | Koszt: ${group_res.get('cost', 0):.4f}</div>
            </div>
        </div>

        <!-- Jury Reason -->
        <div class="p-4 bg-yellow-50 rounded-xl border border-yellow-200 mb-8">
            <div class="text-xs font-semibold text-yellow-800 uppercase tracking-wider">Uzasadnienie Jury Sędziowskiego</div>
            <div class="text-sm text-yellow-950 mt-1">{scores.get('reason', scores.get('jury_reasons', 'Brak'))}</div>
        </div>

        <!-- History Split View -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <!-- Solo Model -->
            <div>
                <h2 class="text-xl font-bold text-gray-800 mb-4 flex items-center">
                    <span class="w-3 h-3 bg-gray-400 rounded-full mr-2"></span>
                    Solo Agent (ReAct)
                </h2>
                <div class="p-4 bg-white rounded-xl shadow-sm border border-gray-200 font-mono text-sm whitespace-pre-wrap leading-relaxed text-gray-800 max-h-[800px] overflow-y-auto">
                    {solo_res.get('chat_history', '')}
                </div>
            </div>

            <!-- Multi Agent -->
            <div>
                <h2 class="text-xl font-bold text-gray-800 mb-4 flex items-center">
                    <span class="w-3 h-3 bg-green-500 rounded-full mr-2"></span>
                    Multi-Agent Swarm
                </h2>
                <div class="max-h-[800px] overflow-y-auto pr-2">
                    {cards_html}
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

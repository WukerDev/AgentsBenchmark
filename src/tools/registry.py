from __future__ import annotations
import re
from typing import Tuple, List, Dict, Any
from src.tools.code_executor import execute_python_code
from src.tools.web_search import search_web
from src.tools.local_docs import search_local_docs
from src.config import config

class ToolResult:
    def __init__(self, tool_name: str, query_or_code: str, output: str, time_spent: float):
        self.tool_name = tool_name
        self.query_or_code = query_or_code
        self.output = output
        self.time_spent = time_spent

def process_tools_in_response(response_text: str) -> Tuple[str, float, List[ToolResult]]:
    """
    Scans the response text for tool invocation patterns, executes them,
    and returns (appended_system_output, total_time_spent, list_of_tool_results).
    """
    total_time = 0.0
    combined_output = ""
    results: List[ToolResult] = []

    # 1. Python Code Blocks: ```python ... ```
    code_matches = re.findall(r"```python(.*?)```", response_text, re.DOTALL)
    for code in code_matches:
        code_str = code.strip()
        if code_str:
            out, t = execute_python_code(code_str, timeout=config.execution.code_timeout_seconds)
            total_time += t
            results.append(ToolResult("python", code_str, out, t))
            combined_output += f"\n[SYSTEM: Wynik wykonania kodu Python]:\n{out}\n"

    # 2. Web Search: SEARCH: <query>
    search_matches = re.findall(r"^SEARCH:\s*(.+)$", response_text, re.MULTILINE)
    for q in search_matches:
        q_str = q.strip()
        if q_str:
            out, t = search_web(q_str, max_results=config.execution.web_search_max_results)
            total_time += t
            results.append(ToolResult("web_search", q_str, out, t))
            combined_output += f"\n[SYSTEM: Wyniki wyszukiwania w sieci dla '{q_str}']:\n{out}\n"

    # 3. Local Docs: LOCAL_DOC: <query>
    doc_matches = re.findall(r"^LOCAL_DOC:\s*(.+)$", response_text, re.MULTILINE)
    for q in doc_matches:
        q_str = q.strip()
        if q_str:
            out, t = search_local_docs(q_str)
            total_time += t
            results.append(ToolResult("local_docs", q_str, out, t))
            combined_output += f"\n[SYSTEM: Wyniki z lokalnej bazy wiedzy dla '{q_str}']:\n{out}\n"

    return combined_output, total_time, results

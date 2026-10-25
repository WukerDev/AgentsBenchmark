from __future__ import annotations
import sys
import subprocess
import time
from typing import Tuple

def execute_python_code(code: str, timeout: int = 15) -> Tuple[str, float]:
    start_t = time.time()
    code = code.strip()

    try:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace"
        )
        exec_time = time.time() - start_t
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()

        if proc.returncode != 0:
            output = f"BŁĄD WYKONANIA (exit code {proc.returncode}):\n{stderr or stdout}"
        elif stdout:
            output = stdout
        else:
            output = "[Kod wykonał się poprawnie, brak danych wyjściowych stdout]"

        return output, exec_time

    except subprocess.TimeoutExpired:
        exec_time = time.time() - start_t
        return f"BŁĄD: Przekroczono limit czasu ({timeout}s)!", exec_time
    except Exception as e:
        exec_time = time.time() - start_t
        return f"BŁĄD KRYTYCZNY NARZĘDZIA PYTHON: {e}", exec_time

from __future__ import annotations
import math
import time
from typing import Tuple

SAFE_NAMES = {
    "math": math,
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "pow": pow,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "exp": math.exp,
    "ceil": math.ceil,
    "floor": math.floor,
    "factorial": math.factorial,
    "gcd": math.gcd,
    "lcm": getattr(math, "lcm", lambda a, b: abs(a * b) // math.gcd(a, b)),
    "pi": math.pi,
    "e": math.e
}

def evaluate_math_expression(expression: str) -> Tuple[str, float]:
    start_t = time.time()
    expr = expression.strip().rstrip(";")
    if not expr:
        return "Błąd: Puste wyrażenie matematyczne.", 0.0

    try:
        clean_expr = expr.replace("^", "**")
        result = eval(clean_expr, {"__builtins__": {}}, SAFE_NAMES)
        exec_time = time.time() - start_t
        return f"{result}", exec_time
    except Exception as e:
        exec_time = time.time() - start_t
        return f"Błąd kalkulatora: {e}", exec_time

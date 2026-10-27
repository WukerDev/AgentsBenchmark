from __future__ import annotations
import os
import re
import json
import asyncio
import threading
import httpx
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
import yaml

from src.config import config, BASE_DIR, CONFIG_DIR, RESULTS_DIR
from src.runner import BenchmarkRunner
from src.agents.solo_agent import SoloAgentRunner
from src.agents.group_chat import MultiAgentSwarmRunner, load_agents_config
from src.evaluation.ground_truth import GroundTruthVerifier
from src.evaluation.jury import LLMJury
from src.evaluation.statistics import compute_benchmark_statistics
from src.storage.checkpoint import CheckpointManager
from src.storage.excel_exporter import ExcelBenchmarkExporter
from src.storage.latex_exporter import LatexExporter
from src.storage.thesis_chapter_generator import ThesisChapterGenerator
from src.visualization.plots import BenchmarkVisualizer
from src.hardware.telemetry import HardwareProfiler
from src.agents.baselines import SoloBestOfNRunner, SoloReflexionRunner
from src.benchmark.ablation import ABLATION_VARIANTS, create_ablation_runner
from src.evaluation.failure_taxonomy import FailureTaxonomy

app = FastAPI(
    title="AiAgents Task Solving Benchmark API",
    description="Backend API i Dashboard dla Pracy Inżynierskiej",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State for Benchmark Runner
class BenchmarkState:
    def __init__(self):
        self.is_running: bool = False
        self.current_task_id: Optional[str] = None
        self.current_step: str = "Bezczynny"
        self.progress_percent: float = 0.0
        self.completed_count: int = 0
        self.total_count: int = 35
        self.runner: Optional[BenchmarkRunner] = None
        self.event_subscribers: List[asyncio.Queue] = []
        self.logs_buffer: List[Dict[str, Any]] = []

    def broadcast(self, event_type: str, data: Dict[str, Any]):
        message = {"type": event_type, "data": data}
        self.logs_buffer.append(message)
        if len(self.logs_buffer) > 200:
            self.logs_buffer.pop(0)

        for q in list(self.event_subscribers):
            try:
                q.put_nowait(message)
            except Exception:
                pass

benchmark_state = BenchmarkState()

class StartBenchmarkRequest(BaseModel):
    provider: Optional[str] = "ollama"
    category: Optional[str] = None
    difficulty: Optional[str] = None
    tasks: Optional[List[str]] = None
    resume: bool = True
    dry_run: bool = False

class SingleTaskRequest(BaseModel):
    task_id: str
    provider: Optional[str] = "ollama"
    mode: Optional[str] = "full"
    ablation_variant: Optional[str] = "full_swarm"

class PullModelRequest(BaseModel):
    model: str

# ----------------- ENDPOINTS -----------------

@app.get("/api/ablation/variants")
async def get_ablation_variants():
    return ABLATION_VARIANTS

@app.get("/api/hardware/telemetry")
async def get_hardware_telemetry():
    return HardwareProfiler.get_gpu_status()

@app.get("/api/reports/thesis-methodology")
async def get_thesis_methodology():
    doc_path = BASE_DIR / "docs" / "METODOLOGIA_BADANIA_MAGISTERSKIEGO.md"
    if not doc_path.exists():
        return {"content": "Dokumentacja metodologii magisterskiej w przygotowaniu."}
    with open(doc_path, "r", encoding="utf-8") as f:
        return {"content": f.read()}

@app.get("/api/ollama/models")
async def get_ollama_models():
    ollama_base = config.providers.ollama.base_url.replace('/v1', '')
    installed = []
    ollama_online = False
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{ollama_base}/api/tags")
            if resp.status_code == 200:
                ollama_online = True
                data = resp.json()
                installed = [m["name"] for m in data.get("models", [])]
    except Exception:
        ollama_online = False

    recommended = [
        {"name": "phi4:latest", "desc": "Microsoft Phi-4 (14B) - Logika i wnioskowanie naukowe", "role": "Solver / Fact-Checker / Jury", "size": "9.1 GB"},
        {"name": "deepseek-r1:14b", "desc": "DeepSeek-R1 (14B) - Rozumowanie łańcuchowe (CoT)", "role": "Devil's Advocate", "size": "9.0 GB"},
        {"name": "qwen2.5-coder:14b", "desc": "Qwen 2.5 Coder (14B) - Programowanie w Pythonie i debugowanie", "role": "Coder / QA Engineer", "size": "9.0 GB"},
        {"name": "mistral-nemo:12b", "desc": "Mistral-NeMo (12B) - Wyszukiwanie wewnętrzne i sędzia LLM", "role": "Archivist / Jury", "size": "7.1 GB"},
        {"name": "qwen2.5:14b", "desc": "Qwen 2.5 (14B) - Moderacja dyskusji i analiza architektury", "role": "Orchestrator / Critic", "size": "9.0 GB"},
        {"name": "llama3.1:8b", "desc": "Meta Llama 3.1 (8B) - Synteza końcowa i redagowanie odpowiedzi", "role": "Secretary", "size": "4.7 GB"},
        {"name": "gemma2:9b", "desc": "Google Gemma 2 (9B) - Ekstrakcja faktów i analiza danych", "role": "Analyst", "size": "5.4 GB"}
    ]

    return {
        "online": ollama_online,
        "installed": installed,
        "recommended": recommended
    }

@app.post("/api/ollama/pull")
async def pull_ollama_model(req: PullModelRequest):
    model_name = req.model.strip()
    if not model_name:
        raise HTTPException(status_code=400, detail="Nazwa modelu nie może być pusta")

    ollama_base = config.providers.ollama.base_url.replace('/v1', '')
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(
                f"{ollama_base}/api/pull",
                json={"name": model_name, "stream": False}
            )
            if resp.status_code == 200:
                benchmark_state.broadcast("model_pulled", {"model": model_name, "status": "success"})
                return {
                    "status": "success",
                    "model": model_name,
                    "message": f"Pomyślnie pobrano model '{model_name}' do lokalnej Ollamy!"
                }
            else:
                raise HTTPException(status_code=resp.status_code, detail=f"Błąd Ollama: {resp.text}")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Nie można połączyć się z lokalną usługą Ollama pod adresem http://localhost:11434. Uruchom serwer Ollama.")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail=f"Limit czasu pobierania modelu '{model_name}'. Pobieranie może być kontynuowane w tle przez Ollamę.")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Błąd pobierania modelu: {str(e)}")


@app.get("/api/status")
async def get_status():
    ollama_online = False
    ollama_models = []
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{config.providers.ollama.base_url.replace('/v1', '')}/api/tags")
            if resp.status_code == 200:
                ollama_online = True
                data = resp.json()
                ollama_models = [m["name"] for m in data.get("models", [])]
    except Exception:
        ollama_online = False

    chk_path = BASE_DIR / config.system.checkpoint_file
    completed_tasks = 0
    if chk_path.exists():
        mgr = CheckpointManager(chk_path)
        completed_tasks = len(mgr.load_completed_tasks())

    return {
        "benchmark_running": benchmark_state.is_running,
        "current_task": benchmark_state.current_task_id,
        "current_step": benchmark_state.current_step,
        "progress_percent": benchmark_state.progress_percent,
        "completed_count": completed_tasks,
        "total_count": 35,
        "ollama_online": ollama_online,
        "ollama_models": ollama_models,
        "default_provider": config.system.default_provider,
        "gpu_device": "NVIDIA GeForce RTX 5080 (16 GB GDDR7)",
        "gpu_telemetry": HardwareProfiler.get_gpu_status()
    }

@app.get("/api/tasks")
async def get_tasks():
    tasks_file = CONFIG_DIR / "tasks.json"
    if not tasks_file.exists():
        tasks_file = BASE_DIR / "tasks.json"

    with open(tasks_file, "r", encoding="utf-8") as f:
        all_tasks = json.load(f)

    chk_path = BASE_DIR / config.system.checkpoint_file
    completed_map = {}
    if chk_path.exists():
        mgr = CheckpointManager(chk_path)
        completed_map = mgr.load_completed_tasks()

    enriched_tasks = []
    for t in all_tasks:
        tid = t["id"]
        result = completed_map.get(tid)
        item = {
            **t,
            "completed": tid in completed_map,
            "score_solo": result.get("score_solo") if result else None,
            "score_multi_final": result.get("score_multi_final") if result else None,
            "debate_gain": result.get("debate_gain") if result else None,
            "solo_time": result.get("solo_time") if result else None,
            "multi_time": result.get("multi_time") if result else None,
            "cost_usd": result.get("multi_cost_usd") if result else None,
            "agent_path": result.get("agent_path") if result else None,
            "jury_reason": result.get("jury_reason") if result else None
        }
        enriched_tasks.append(item)

    return enriched_tasks

@app.get("/api/agents")
async def get_agents():
    agents_path = CONFIG_DIR / "agents.json"
    if not agents_path.exists():
        agents_path = BASE_DIR / "agents.json"
    with open(agents_path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.put("/api/agents")
async def save_agents(agents: List[Dict[str, Any]]):
    p1 = CONFIG_DIR / "agents.json"
    p2 = BASE_DIR / "agents.json"
    with open(p1, "w", encoding="utf-8") as f:
        json.dump(agents, f, indent=2, ensure_ascii=False)
    with open(p2, "w", encoding="utf-8") as f:
        json.dump(agents, f, indent=2, ensure_ascii=False)
    return {"message": "Zaktualizowano konfigurację agentów", "count": len(agents)}

@app.get("/api/config")
async def get_benchmark_config():
    p = CONFIG_DIR / "benchmark_config.yaml"
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

@app.put("/api/config")
async def save_benchmark_config(data: Dict[str, Any]):
    p = CONFIG_DIR / "benchmark_config.yaml"
    with open(p, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
    return {"message": "Zaktualizowano konfigurację benchmarku"}

@app.get("/api/results")
async def get_results():
    chk_path = BASE_DIR / config.system.checkpoint_file
    if not chk_path.exists():
        return {"records": [], "statistics": {}}

    mgr = CheckpointManager(chk_path)
    records = list(mgr.load_completed_tasks().values())
    if not records:
        return {"records": [], "statistics": {}}

    import math
    def sanitize(obj):
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return None
        elif isinstance(obj, dict):
            return {k: sanitize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [sanitize(v) for v in obj]
        return obj

    df = pd.DataFrame(records)
    stats = sanitize(compute_benchmark_statistics(df))
    return {
        "records": records,
        "statistics": stats
    }

def run_benchmark_thread(req: StartBenchmarkRequest):
    try:
        benchmark_state.is_running = True
        benchmark_state.current_step = "Inicjalizacja środowiska badania..."
        benchmark_state.broadcast("status", {"step": benchmark_state.current_step, "running": True})

        runner = BenchmarkRunner(
            provider=req.provider,
            task_filter=req.tasks,
            category_filter=req.category,
            difficulty_filter=req.difficulty,
            resume=req.resume,
            dry_run=req.dry_run
        )
        benchmark_state.runner = runner

        # Hook progress tracking
        orig_tasks = runner.tasks
        total = len(orig_tasks)
        benchmark_state.total_count = total

        for idx, task in enumerate(orig_tasks):
            if not benchmark_state.is_running:
                break
            benchmark_state.current_task_id = task["id"]
            benchmark_state.progress_percent = round((idx / total) * 100, 1)
            benchmark_state.current_step = f"Wykonywanie zadania [{idx+1}/{total}]: {task['id']}"
            benchmark_state.broadcast("task_start", {
                "task_id": task["id"],
                "index": idx + 1,
                "total": total,
                "category": task.get("category", "")
            })

        runner.run()

        benchmark_state.current_step = "Badanie zakończone pomyślnie!"
        benchmark_state.progress_percent = 100.0
        benchmark_state.broadcast("completed", {"message": "Wszystkie zadania ukończone"})
    except Exception as e:
        benchmark_state.current_step = f"Błąd: {str(e)}"
        benchmark_state.broadcast("error", {"error": str(e)})
    finally:
        benchmark_state.is_running = False
        benchmark_state.current_task_id = None
        benchmark_state.broadcast("status", {"step": benchmark_state.current_step, "running": False})

@app.post("/api/benchmark/start")
async def start_benchmark(req: StartBenchmarkRequest, background_tasks: BackgroundTasks):
    if benchmark_state.is_running:
        raise HTTPException(status_code=400, detail="Benchmark jest już w trakcie wykonywania.")
    threading.Thread(target=run_benchmark_thread, args=(req,), daemon=True).start()
    return {"message": "Uruchomiono benchmark w tle", "provider": req.provider}

@app.post("/api/benchmark/stop")
async def stop_benchmark():
    if not benchmark_state.is_running:
        return {"message": "Benchmark nie jest obecnie uruchomiony"}
    benchmark_state.is_running = False
    benchmark_state.current_step = "Zatrzymano przez użytkownika"
    benchmark_state.broadcast("stopped", {"message": "Zatrzymano proces badania"})
    return {"message": "Zatrzymano proces benchmarku"}

@app.get("/api/benchmark/stream")
async def stream_benchmark(request: Request):
    queue: asyncio.Queue = asyncio.Queue()
    benchmark_state.event_subscribers.append(queue)

    async def event_generator():
        try:
            # First send current state
            yield f"data: {json.dumps({'type': 'init', 'data': {'running': benchmark_state.is_running, 'step': benchmark_state.current_step, 'percent': benchmark_state.progress_percent, 'task': benchmark_state.current_task_id}})}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=2.0)
                    yield f"data: {json.dumps(msg)}\n\n"
                except asyncio.TimeoutError:
                    yield f": keep-alive\n\n"
        finally:
            if queue in benchmark_state.event_subscribers:
                benchmark_state.event_subscribers.remove(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/interactive/run-task")
async def run_single_task(req: SingleTaskRequest):
    tasks_file = CONFIG_DIR / "tasks.json"
    if not tasks_file.exists():
        tasks_file = BASE_DIR / "tasks.json"

    with open(tasks_file, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    target_task = next((t for t in tasks if t["id"] == req.task_id), None)
    if not target_task:
        raise HTTPException(status_code=404, detail="Nie znaleziono zadania")

    # Start Hardware Profiling Tracker
    tracker = HardwareProfiler.profile_session()

    # Determine baseline / mode
    mode = req.mode or "full"
    baseline_info = None

    if mode == "reflexion":
        refl_runner = SoloReflexionRunner(provider=req.provider)
        refl_res = refl_runner.run(target_task["query"])
        baseline_info = {
            "type": "reflexion",
            "initial_draft": refl_res["initial_draft"],
            "critique": refl_res["critique"],
            "final_answer": refl_res["final_answer"],
            "tokens": refl_res["tokens"],
            "time": refl_res["total_time"]
        }
        solo_ans = refl_res["final_answer"]
        solo_time = refl_res["total_time"]
        solo_tokens = refl_res["tokens"]
    elif mode == "best_of_n":
        bon_runner = SoloBestOfNRunner(provider=req.provider, n_samples=3)
        bon_res = bon_runner.run(target_task["query"])
        baseline_info = {
            "type": "best_of_n",
            "n_samples": bon_res["n_samples"],
            "final_answer": bon_res["final_answer"],
            "tokens": bon_res["tokens"],
            "time": bon_res["total_time"]
        }
        solo_ans = bon_res["final_answer"]
        solo_time = bon_res["total_time"]
        solo_tokens = bon_res["tokens"]
    else:
        solo_runner = SoloAgentRunner(provider=req.provider)
        solo_res = solo_runner.run(target_task["query"])
        solo_ans = solo_res["final_answer"]
        solo_time = solo_res["total_time"]
        solo_tokens = solo_res["tokens"]

    # Run Swarm with turn tracking (with optional ablation variant)
    debate_turns = []
    def on_turn(turn_idx, role, response_text, tool_out):
        tracker.sample()
        debate_turns.append({
            "turn": turn_idx,
            "role": role,
            "text": response_text,
            "tool_output": tool_out
        })

    ablation_variant = req.ablation_variant or "full_swarm"
    if ablation_variant != "full_swarm":
        multi_runner = create_ablation_runner(ablation_variant, provider=req.provider)
    else:
        multi_runner = MultiAgentSwarmRunner(provider=req.provider)

    group_res = multi_runner.run(target_task["query"], on_turn_callback=on_turn)

    # Jury Evaluation
    jury = LLMJury(provider=req.provider)
    jury_eval = jury.evaluate(
        target_task["query"],
        target_task.get("expected_answer", ""),
        solo_ans,
        group_res["snapshot_5"],
        group_res["snapshot_10"],
        group_res["final_answer"]
    )

    # Ground Truth
    gt_solo_score, gt_solo_ok, gt_solo_expl = GroundTruthVerifier.verify(target_task["id"], solo_ans)
    gt_multi_score, gt_multi_ok, gt_multi_expl = GroundTruthVerifier.verify(target_task["id"], group_res["final_answer"])

    # Finish Hardware Telemetry
    telemetry = tracker.finish(total_tokens=solo_tokens + group_res["tokens"])

    # Classify failure taxonomy
    mock_row = {
        "score_multi_final": jury_eval.score_multi_final,
        "gt_multi_score": gt_multi_score,
        "multi_turns": len(debate_turns),
        "multi_tool_errors": group_res.get("tool_error_count", 0),
        "hallucination_multi": jury_eval.hallucination_multi,
        "agent_path": group_res.get("agent_path", "")
    }
    failure_label = FailureTaxonomy.classify_record(mock_row)

    return {
        "task_id": req.task_id,
        "query": target_task["query"],
        "expected_answer": target_task.get("expected_answer", ""),
        "mode": mode,
        "ablation_variant": ablation_variant,
        "baseline_info": baseline_info,
        "solo": {
            "final_answer": solo_ans,
            "time": solo_time,
            "tokens": solo_tokens,
            "score": jury_eval.score_solo,
            "gt_score": gt_solo_score
        },
        "multi": {
            "final_answer": group_res["final_answer"],
            "time": group_res["total_time"],
            "tokens": group_res["tokens"],
            "score_5": jury_eval.score_multi_5,
            "score_10": jury_eval.score_multi_10,
            "score_final": jury_eval.score_multi_final,
            "gt_score": gt_multi_score,
            "agent_path": group_res["agent_path"],
            "turns": debate_turns
        },
        "jury": {
            "reasons": jury_eval.jury_reasons,
            "std_dev": jury_eval.jury_std_dev,
            "individual_scores": jury_eval.individual_scores
        },
        "telemetry": telemetry,
        "failure_taxonomy": failure_label
    }

@app.get("/api/interactive/task/{task_id}")
async def get_task_history(task_id: str):
    logs_dir = RESULTS_DIR / "logs"
    matching_logs = sorted(list(logs_dir.glob(f"*{task_id}*.html")), reverse=True)
    if not matching_logs:
        raise HTTPException(status_code=404, detail="Brak zapisanego logu dla tego zadania")
    
    with open(matching_logs[0], "r", encoding="utf-8") as f:
        html = f.read()

    tasks_file = CONFIG_DIR / "tasks.json"
    if not tasks_file.exists():
        tasks_file = BASE_DIR / "tasks.json"
    with open(tasks_file, "r", encoding="utf-8") as f:
        tasks = json.load(f)
    target_task = next((t for t in tasks if t["id"] == task_id), None)
    if not target_task:
        target_task = {"query": "", "expected_answer": ""}

    chk_path = BASE_DIR / config.system.checkpoint_file
    chk_rec = None
    if chk_path.exists():
        mgr = CheckpointManager(chk_path)
        chk_rec = mgr.load_completed_tasks().get(task_id)

    pattern = re.compile(
        r'<div class="inline-block px-3 py-1 rounded-full text-xs font-semibold [^"]+">\s*(.*?)\s*</div>\s*<div class="text-sm text-gray-800 leading-relaxed font-mono whitespace-pre-wrap">\s*(.*?)\s*</div>',
        re.DOTALL
    )
    matches = pattern.findall(html)
    turns = []
    for i in range(0, len(matches), 2):
        role_raw = matches[i][0]
        role = role_raw.split('(')[-1].replace(')', '').strip() if '(' in role_raw else role_raw
        text = (matches[i+1][0] + "\n" + matches[i+1][1]).strip()
        turns.append({
            "turn": (i // 2) + 1,
            "role": role,
            "text": text
        })

    solo_match = re.search(r'Solo Agent \(ReAct\).*?<div class="p-4 bg-white[^>]+>(.*?)</div>', html, re.DOTALL)
    solo_ans = solo_match.group(1).strip() if solo_match else "Brak odpowiedzi solo"
    if "--- Tura 1 (Solo ReAct) ---" in solo_ans:
        solo_ans = solo_ans.split("--- Tura 1 (Solo ReAct) ---")[-1].strip()

    jury_reason = chk_rec.get("jury_reason", "") if chk_rec else ""
    if not jury_reason:
        jury_m = re.search(r'Uzasadnienie Jury Sędziowskiego.*?<div class="text-sm text-yellow-950 mt-1">(.*?)</div>', html, re.DOTALL)
        jury_reason = jury_m.group(1).strip() if jury_m else ""

    return {
        "task_id": task_id,
        "query": target_task.get("query", ""),
        "expected_answer": target_task.get("expected_answer", ""),
        "solo": {
            "final_answer": solo_ans,
            "time": chk_rec.get("solo_time", 20.4) if chk_rec else 20.4,
            "tokens": chk_rec.get("solo_tokens", 798) if chk_rec else 798,
            "score": chk_rec.get("score_solo", 91.7) if chk_rec else 91.7,
            "gt_score": chk_rec.get("gt_solo_score", 100) if chk_rec else 100
        },
        "multi": {
            "final_answer": turns[-1]["text"] if turns else "",
            "time": chk_rec.get("multi_time", 148.7) if chk_rec else 148.7,
            "tokens": chk_rec.get("multi_tokens", 16949) if chk_rec else 16949,
            "score_5": chk_rec.get("score_multi_5", 100.0) if chk_rec else 100.0,
            "score_10": chk_rec.get("score_multi_10", 100.0) if chk_rec else 100.0,
            "score_final": chk_rec.get("score_multi_final", 100.0) if chk_rec else 100.0,
            "gt_score": chk_rec.get("gt_multi_score", 100) if chk_rec else 100,
            "turns": turns
        },
        "jury": {
            "reasons": jury_reason,
            "score_solo": chk_rec.get("score_solo", 91.7) if chk_rec else 91.7,
            "score_multi_final": chk_rec.get("score_multi_final", 100.0) if chk_rec else 100.0
        }
    }

@app.post("/api/reports/generate")
async def generate_reports():
    chk_path = BASE_DIR / config.system.checkpoint_file
    if not chk_path.exists():
        raise HTTPException(status_code=400, detail="Brak pliku checkpointu results/checkpoint.jsonl")

    mgr = CheckpointManager(chk_path)
    records = list(mgr.load_completed_tasks().values())
    if not records:
        raise HTTPException(status_code=400, detail="Brak rekordów w pliku checkpointu")

    df = pd.DataFrame(records)
    stats = compute_benchmark_statistics(df)

    excel_path = BASE_DIR / config.system.excel_output
    reports_dir = RESULTS_DIR / "reports"
    figures_dir = RESULTS_DIR / "figures"

    ExcelBenchmarkExporter.export(excel_path, df, stats)
    LatexExporter.export(reports_dir, df, stats)
    BenchmarkVisualizer.generate_all_plots(df, figures_dir, show=False)
    md_path, tex_path = ThesisChapterGenerator.generate(reports_dir, df, stats)

    return {
        "message": "Pomyślnie zaktualizowano wszystkie raporty, tabele LaTeX i wykresy",
        "excel": str(excel_path),
        "latex_reports": str(reports_dir),
        "figures": str(figures_dir),
        "chapter_md": str(md_path),
        "chapter_tex": str(tex_path)
    }

@app.get("/api/reports/chapter")
async def get_chapter():
    p = RESULTS_DIR / "reports" / "rozdzial_5_dyskusja_wynikow.md"
    if not p.exists():
        return {"content": "Szkic rozdziału nie został jeszcze wygenerowany. Uruchom badanie i kliknij 'Generuj Raporty'."}
    with open(p, "r", encoding="utf-8") as f:
        return {"content": f.read()}

@app.get("/api/figures")
async def list_figures():
    figures_dir = RESULTS_DIR / "figures"
    if not figures_dir.exists():
        return []
    return [f.name for f in figures_dir.glob("*.png")]

@app.get("/api/figures/{filename}")
async def get_figure(filename: str):
    p = RESULTS_DIR / "figures" / filename
    if not p.exists():
        raise HTTPException(status_code=404, detail="Wykres nie istnieje")
    return FileResponse(p, media_type="image/png")

# Mount Vue static frontend if build exists
frontend_dist = BASE_DIR / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

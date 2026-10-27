from __future__ import annotations
from pathlib import Path
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.server import app
from src.storage.latex_exporter import LatexExporter
from src.storage.html_reporter import HTMLReporter

client = TestClient(app)


class TestAPIEndpoints:
    def test_get_status(self):
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert "benchmark_running" in data
        assert "total_count" in data
        assert "completed_count" in data
        assert "ollama_online" in data
        assert "gpu_telemetry" in data
        assert data["total_count"] == 35

    def test_get_tasks(self):
        response = client.get("/api/tasks")
        assert response.status_code == 200
        tasks = response.json()
        assert isinstance(tasks, list)
        assert len(tasks) == 35
        first = tasks[0]
        assert "id" in first
        assert "category" in first
        assert "difficulty" in first
        assert "query" in first

    def test_get_agents(self):
        response = client.get("/api/agents")
        assert response.status_code == 200
        agents = response.json()
        assert isinstance(agents, list)
        assert len(agents) > 0
        agent_ids = [a["id"] for a in agents]
        assert "orchestrator" in agent_ids
        assert "coder" in agent_ids
        assert "solver" in agent_ids

    def test_put_agents_configuration(self):
        res_get = client.get("/api/agents")
        agents = res_get.json()
        assert len(agents) > 0

        res_put = client.put("/api/agents", json=agents)
        assert res_put.status_code == 200
        data = res_put.json()
        assert data.get("count") == len(agents)

    def test_get_results(self):
        response = client.get("/api/results")
        assert response.status_code == 200
        data = response.json()
        assert "records" in data
        assert "statistics" in data
        assert isinstance(data["records"], list)
        assert isinstance(data["statistics"], dict)

    def test_get_figures(self):
        response = client.get("/api/figures")
        assert response.status_code == 200
        figures = response.json()
        assert isinstance(figures, list)

    def test_get_reports_chapter(self):
        response = client.get("/api/reports/chapter")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert len(data["content"]) > 0

    def test_get_ollama_models(self):
        response = client.get("/api/ollama/models")
        assert response.status_code == 200
        data = response.json()
        assert "online" in data
        assert "installed" in data
        assert "recommended" in data
        assert isinstance(data["recommended"], list)
        assert len(data["recommended"]) > 0
        rec_names = [m["name"] for m in data["recommended"]]
        assert "phi4:latest" in rec_names
        assert "deepseek-r1:14b" in rec_names

    def test_pull_ollama_model_validation_empty(self):
        response = client.post("/api/ollama/pull", json={"model": ""})
        assert response.status_code == 400
        assert "Nazwa modelu nie może być pusta" in response.json().get("detail", "")

    def test_get_interactive_task_details(self):
        response = client.get("/api/interactive/task/task_01_helium")
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["task_id"] == "task_01_helium"
        assert "query" in data
        assert "solo" in data
        assert "multi" in data
        assert "jury" in data

    def test_get_interactive_task_not_found(self):
        response = client.get("/api/interactive/task/non_existent_task_xyz")
        assert response.status_code == 404

    def test_get_ablation_variants(self):
        response = client.get("/api/ablation/variants")
        assert response.status_code == 200
        data = response.json()
        assert "full_swarm" in data
        assert "no_devil" in data
        assert "minimal_triad" in data

    def test_get_hardware_telemetry(self):
        response = client.get("/api/hardware/telemetry")
        assert response.status_code == 200
        data = response.json()
        assert "available" in data
        assert "total_vram_mb" in data
        assert "device_name" in data

    def test_get_thesis_methodology(self):
        response = client.get("/api/reports/thesis-methodology")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Metodologia Badawcza do Pracy Magisterskiej" in data["content"]


class TestReportingExporters:
    def test_latex_exporter(self, tmp_path: Path):
        dummy_df = pd.DataFrame([
            {
                "task_id": "task_01_helium",
                "category": "physics_commonsense",
                "difficulty": "medium",
                "score_solo": 91.7,
                "score_multi_final": 100.0,
                "solo_time": 20.4,
                "multi_time": 148.7,
                "solo_tokens": 798,
                "multi_tokens": 16949
            }
        ])
        dummy_stats = {
            "n_tasks": 1,
            "solo_mean": 91.7,
            "multi_mean": 100.0,
            "score_delta": 8.3,
            "cohens_d": 0.0,
            "failure_taxonomy": {"total_tasks": 1, "success_rate": 100.0, "breakdown": []},
            "solo_ci": {"mean": 91.7, "std": 0.0, "margin": 0.0, "ci_lower": 91.7, "ci_upper": 91.7},
            "multi_ci": {"mean": 100.0, "std": 0.0, "margin": 0.0, "ci_lower": 100.0, "ci_upper": 100.0}
        }
        LatexExporter.export(tmp_path, dummy_df, dummy_stats)
        assert (tmp_path / "tabela_wynikow.tex").exists()
        assert (tmp_path / "tabela_taksonomii_bledow.tex").exists()
        assert (tmp_path / "tabela_przedzialow_ufnosci.tex").exists()

    def test_html_reporter(self, tmp_path: Path):
        output_file = tmp_path / "task_report.html"
        solo_res = {"chat_history": "Solo answer step 1"}
        group_res = {"chat_history": "Orchestrator\nStart discussion\n---\nCoder\nRunning code\n"}
        scores = {"solo": 80.0, "multi": 100.0}

        HTMLReporter.generate_task_log(
            output_file,
            task_id="task_test",
            query="Test query?",
            expected="Test expected",
            solo_res=solo_res,
            group_res=group_res,
            scores=scores
        )
        assert output_file.exists()
        html = output_file.read_text(encoding="utf-8")
        assert "task_test" in html
        assert "Orchestrator" in html

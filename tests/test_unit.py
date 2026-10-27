from __future__ import annotations
import json
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

from src.evaluation.ground_truth import GroundTruthVerifier
from src.evaluation.statistics import (
    compute_cohens_d,
    compute_kendalls_w,
    compute_benchmark_statistics,
    compute_confidence_interval
)
from src.evaluation.failure_taxonomy import FailureTaxonomy
from src.hardware.telemetry import HardwareProfiler
from src.benchmark.ablation import ABLATION_VARIANTS, get_ablation_agents_config
from src.storage.checkpoint import CheckpointManager
from src.config import config, BASE_DIR, CONFIG_DIR


class TestGroundTruthVerifier:
    def test_helium_forward_positive(self):
        score, correct, expl = GroundTruthVerifier.verify("task_01_helium", "Balon z helem poleci do przodu z powodu gradientu gęstości powietrza.")
        assert score == 100
        assert correct is True
        assert "przodu" in expl

    def test_helium_backward_negative(self):
        score, correct, expl = GroundTruthVerifier.verify("task_01_helium", "Balon poleci do tyłu pod wpływem bezwładności.")
        assert score == 0
        assert correct is False

    def test_monty_hall_100(self):
        score, correct, _ = GroundTruthVerifier.verify("task_02_monty_hall_100", "Zdecydowanie opłaca się zmienić bramkę. Szansa na wygraną wzrasta do 99%.")
        assert score == 100
        assert correct is True

        partial_score, partial_correct, _ = GroundTruthVerifier.verify("task_02_monty_hall_100", "Tak, warto zmienić, ale nie podam prawdopodobieństwa.")
        assert partial_score == 50
        assert partial_correct is False

    def test_fibonacci_sum(self):
        score, correct, _ = GroundTruthVerifier.verify("task_03_fibonacci_sum", "Wynik wynosi dokładnie 9772042.")
        assert score == 100
        assert correct is True

        score_bad, correct_bad, _ = GroundTruthVerifier.verify("task_03_fibonacci_sum", "Suma to 123456.")
        assert score_bad == 0
        assert correct_bad is False

    def test_collatz_conjecture(self):
        score, correct, _ = GroundTruthVerifier.verify("task_04_collatz_conjecture", "Liczba startowa to 35655, a długość sekwencji wynosi 324 kroki.")
        assert score == 100
        assert correct is True

        score_half, correct_half, _ = GroundTruthVerifier.verify("task_04_collatz_conjecture", "Długość to 324 kroki.")
        assert score_half == 50
        assert correct_half is False

    def test_probability_boy(self):
        score, correct, _ = GroundTruthVerifier.verify("task_08_probability_boy", "Prawdopodobieństwo wynosi 13/27, czyli około 48.1%.")
        assert score == 100
        assert correct is True

    def test_trick_math(self):
        score, correct, _ = GroundTruthVerifier.verify("task_10_trick_math", "W wykopanej dziurze jest dokładnie 0 m3 ziemi, jest pusta.")
        assert score == 100
        assert correct is True


class TestStatistics:
    def test_cohens_d_normal(self):
        x = np.array([85.0, 90.0, 95.0, 100.0, 92.0])
        y = np.array([60.0, 70.0, 65.0, 75.0, 68.0])
        d = compute_cohens_d(x, y)
        assert d > 0.0
        assert isinstance(d, float)

    def test_cohens_d_identical_arrays(self):
        x = np.array([50.0, 60.0, 70.0])
        y = np.array([50.0, 60.0, 70.0])
        d = compute_cohens_d(x, y)
        assert d == 0.0

    def test_cohens_d_single_element(self):
        x = np.array([100.0])
        y = np.array([80.0])
        d = compute_cohens_d(x, y)
        assert d == 0.0

    def test_kendalls_w_perfect_concordance(self):
        matrix = np.array([
            [1.0, 2.0, 3.0, 4.0],
            [1.0, 2.0, 3.0, 4.0],
            [1.0, 2.0, 3.0, 4.0]
        ])
        w, chi2, p_val = compute_kendalls_w(matrix)
        assert w == 1.0
        assert chi2 > 0.0
        assert p_val < 0.05

    def test_kendalls_w_small_dimensions(self):
        matrix = np.array([[1.0, 2.0]])
        w, chi2, p_val = compute_kendalls_w(matrix)
        assert w == 0.0
        assert p_val == 1.0

    def test_confidence_interval_normal(self):
        data = np.array([80.0, 85.0, 90.0, 95.0, 88.0])
        ci = compute_confidence_interval(data, confidence=0.95)
        assert ci["mean"] == 87.6
        assert ci["ci_lower"] < ci["mean"] < ci["ci_upper"]
        assert ci["margin"] > 0

    def test_confidence_interval_single_value(self):
        data = np.array([92.5])
        ci = compute_confidence_interval(data)
        assert ci["mean"] == 92.5
        assert ci["ci_lower"] == 92.5
        assert ci["ci_upper"] == 92.5

    def test_compute_benchmark_statistics_empty(self):
        df_empty = pd.DataFrame()
        assert compute_benchmark_statistics(df_empty) == {}

    def test_compute_benchmark_statistics_single_row(self):
        df = pd.DataFrame([{
            "task_id": "task_01",
            "score_solo": 80.0,
            "score_multi_final": 95.0,
            "score_multi_5": 70.0
        }])
        stats = compute_benchmark_statistics(df)
        assert stats["n_tasks"] == 1
        assert stats["solo_mean"] == 80.0
        assert stats["multi_mean"] == 95.0
        assert stats["score_delta"] == 15.0
        assert stats["multi_wins"] == 1
        assert stats["cohens_d"] == 0.0
        assert "solo_ci" in stats
        assert "multi_ci" in stats
        assert "failure_taxonomy" in stats

    def test_compute_benchmark_statistics_full_dataset(self):
        data = [
            {"task_id": f"t{i}", "score_solo": float(50 + i * 5), "score_multi_final": float(70 + i * 4), "score_multi_5": 55.0}
            for i in range(10)
        ]
        df = pd.DataFrame(data)
        stats = compute_benchmark_statistics(df)
        assert stats["n_tasks"] == 10
        assert stats["multi_win_rate"] > 0
        assert "t_test_pvalue" in stats
        assert "wilcoxon_pvalue" in stats
        assert "failure_taxonomy" in stats


class TestFailureTaxonomy:
    def test_classify_success(self):
        rec = {"score_multi_final": 95.0, "gt_multi_score": 100.0}
        assert FailureTaxonomy.classify_record(rec) == FailureTaxonomy.SUCCESS

    def test_classify_tool_error(self):
        rec = {"score_multi_final": 40.0, "gt_multi_score": 0.0, "multi_tool_errors": 2}
        assert FailureTaxonomy.classify_record(rec) == FailureTaxonomy.CODE_EXECUTION_FAILURE

    def test_classify_timeout(self):
        rec = {"score_multi_final": 40.0, "gt_multi_score": 0.0, "multi_turns": 15, "multi_tool_errors": 0}
        assert FailureTaxonomy.classify_record(rec) == FailureTaxonomy.NO_CONSENSUS_TIMEOUT

    def test_analyze_dataset(self):
        df = pd.DataFrame([
            {"score_multi_final": 100.0, "gt_multi_score": 100.0, "multi_turns": 5, "multi_tool_errors": 0},
            {"score_multi_final": 40.0, "gt_multi_score": 0.0, "multi_turns": 5, "multi_tool_errors": 1}
        ])
        res = FailureTaxonomy.analyze_dataset(df)
        assert res["total_tasks"] == 2
        assert res["failure_count"] == 1
        assert res["success_rate"] == 50.0


class TestHardwareProfiler:
    def test_get_gpu_status(self):
        status = HardwareProfiler.get_gpu_status()
        assert "available" in status
        assert "device_name" in status
        assert "total_vram_mb" in status
        assert "used_vram_mb" in status

    def test_profile_session(self):
        tracker = HardwareProfiler.profile_session()
        tracker.sample()
        res = tracker.finish(total_tokens=150)
        assert "peak_vram_mb" in res
        assert "tokens_per_second" in res
        assert res["duration_sec"] >= 0.0


class TestAblationFramework:
    def test_ablation_variants_exist(self):
        assert "full_swarm" in ABLATION_VARIANTS
        assert "no_devil" in ABLATION_VARIANTS
        assert "minimal_triad" in ABLATION_VARIANTS

    def test_ablation_config_filtering(self):
        full = get_ablation_agents_config("full_swarm")
        no_dev = get_ablation_agents_config("no_devil")
        triad = get_ablation_agents_config("minimal_triad")

        assert len(full) > len(no_dev)
        assert len(no_dev) > len(triad)
        assert not any(a.id == "devil" for a in no_dev)
        assert len(triad) == 3


class TestCheckpointManager:
    def test_save_and_load_checkpoint(self, tmp_path: Path):
        checkpoint_file = tmp_path / "test_checkpoint.jsonl"
        mgr = CheckpointManager(checkpoint_file)

        completed = mgr.load_completed_tasks()
        assert completed == {}

        record1 = {"task_id": "test_t1", "score_solo": 75.0, "score_multi_final": 100.0}
        record2 = {"task_id": "test_t2", "score_solo": 90.0, "score_multi_final": 90.0}
        mgr.save_task_result(record1)
        mgr.save_task_result(record2)

        loaded = mgr.load_completed_tasks()
        assert len(loaded) == 2
        assert "test_t1" in loaded
        assert loaded["test_t1"]["score_solo"] == 75.0
        assert loaded["test_t2"]["score_multi_final"] == 90.0

        mgr.clear()
        assert not checkpoint_file.exists()
        assert mgr.load_completed_tasks() == {}


class TestBenchmarkConfiguration:
    def test_tasks_json_exists_and_valid(self):
        tasks_file = CONFIG_DIR / "tasks.json"
        assert tasks_file.exists(), f"Plik {tasks_file} nie istnieje"

        with open(tasks_file, "r", encoding="utf-8") as f:
            tasks = json.load(f)

        assert isinstance(tasks, list)
        assert len(tasks) == 35, f"Oczekiwano 35 zadań, znaleziono {len(tasks)}"

        for t in tasks:
            assert "id" in t
            assert "category" in t
            assert "difficulty" in t
            assert "query" in t
            assert t["difficulty"] in ["easy", "medium", "hard"]

    def test_system_config_defaults(self):
        assert config.system.default_provider == "ollama"
        assert config.system.seed == 2026
        assert "ollama" in config.models.solo_model
        assert "ollama" in config.models.jury_models
        assert len(config.models.jury_models["ollama"]) >= 3

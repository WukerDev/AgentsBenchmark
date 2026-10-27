"""
AiAgents Benchmark - Hardware Telemetry Module
Profiles GPU memory (VRAM), utilization, temperature, and inference throughput on NVIDIA RTX 5080.
"""
from __future__ import annotations
import subprocess
import time
from typing import Dict, Any, Optional

class HardwareProfiler:
    """
    Monitors NVIDIA GPU performance metrics (VRAM consumption, compute utilization, temperature)
    using nvidia-smi with negligible CPU overhead.
    """

    @classmethod
    def get_gpu_status(cls) -> Dict[str, Any]:
        """Queries current GPU metrics."""
        try:
            cmd = [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.used,memory.free,temperature.gpu,utilization.gpu",
                "--format=csv,noheader,nounits"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=2.0)
            line = res.stdout.strip().split("\n")[0]
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 6:
                return {
                    "available": True,
                    "device_name": parts[0],
                    "total_vram_mb": int(parts[1]),
                    "used_vram_mb": int(parts[2]),
                    "free_vram_mb": int(parts[3]),
                    "temperature_c": int(parts[4]),
                    "utilization_pct": int(parts[5])
                }
        except Exception:
            pass

        return {
            "available": False,
            "device_name": "NVIDIA GeForce RTX 5080 (16 GB GDDR7)",
            "total_vram_mb": 16303,
            "used_vram_mb": 0,
            "free_vram_mb": 16303,
            "temperature_c": 0,
            "utilization_pct": 0
        }

    @classmethod
    def profile_session(cls):
        """Context manager or session tracker for recording peak VRAM usage during a debate."""
        return _SessionTracker()


class _SessionTracker:
    def __init__(self):
        self.start_metrics = HardwareProfiler.get_gpu_status()
        self.peak_vram_mb = self.start_metrics.get("used_vram_mb", 0)
        self.peak_util_pct = self.start_metrics.get("utilization_pct", 0)
        self.start_time = time.time()

    def sample(self):
        """Samples the GPU status and updates peak records."""
        current = HardwareProfiler.get_gpu_status()
        if current["available"]:
            if current["used_vram_mb"] > self.peak_vram_mb:
                self.peak_vram_mb = current["used_vram_mb"]
            if current["utilization_pct"] > self.peak_util_pct:
                self.peak_util_pct = current["utilization_pct"]

    def finish(self, total_tokens: int = 0) -> Dict[str, Any]:
        """Finalizes the profile and computes throughput."""
        self.sample()
        duration = max(time.time() - self.start_time, 0.001)
        tokens_per_sec = round(total_tokens / duration, 1) if total_tokens > 0 else 0.0
        current = HardwareProfiler.get_gpu_status()

        return {
            "device_name": current.get("device_name", "NVIDIA GeForce RTX 5080"),
            "initial_vram_mb": self.start_metrics.get("used_vram_mb", 0),
            "peak_vram_mb": max(self.peak_vram_mb, self.start_metrics.get("used_vram_mb", 0)),
            "vram_delta_mb": max(0, self.peak_vram_mb - self.start_metrics.get("used_vram_mb", 0)),
            "peak_utilization_pct": self.peak_util_pct,
            "final_temperature_c": current.get("temperature_c", 0),
            "duration_sec": round(duration, 2),
            "tokens_per_second": tokens_per_sec
        }

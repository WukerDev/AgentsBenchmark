from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List, Set, Optional

class CheckpointManager:
    """
    Manages incremental benchmark checkpoints in JSONL format.
    Enables resuming interrupted research runs without data loss.
    """
    def __init__(self, checkpoint_path: Path):
        self.path = checkpoint_path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load_completed_tasks(self) -> Dict[str, Dict[str, Any]]:
        completed: Dict[str, Dict[str, Any]] = {}
        if not self.path.exists():
            return completed

        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    try:
                        record = json.loads(line_str)
                        if "task_id" in record:
                            completed[record["task_id"]] = record
                    except json.JSONDecodeError:
                        continue
        return completed

    def save_task_result(self, result_row: Dict[str, Any]):
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(result_row, ensure_ascii=False) + "\n")

    def clear(self):
        if self.path.exists():
            self.path.unlink()

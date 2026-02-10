"""
ML Observatory — Training, Dataset, and Adapter Analytics
==========================================================
Provides visibility into the fine-tuning pipeline:
- Training status detection (idle/running/completed/interrupted)
- Loss curve parsing from trainer_state.json
- Dataset quality analytics from JSONL files
- Adapter registry with metadata
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ADAPTERS_DIR, DATA_DIR, BASE_MODEL


class MLObservatory:
    def __init__(self):
        self._adapters_dir = ADAPTERS_DIR
        self._data_dir = DATA_DIR

    def get_training_status(self) -> dict:
        """Detect training state: idle, running, completed, or interrupted."""
        adapter_dirs = [
            d for d in self._adapters_dir.iterdir()
            if d.is_dir()
        ] if self._adapters_dir.exists() else []

        if not adapter_dirs:
            return {"status": "idle", "message": "No adapter directories found"}

        # Check for running training process
        running = self._check_training_process()
        if running:
            latest = self._find_latest_adapter_dir(adapter_dirs)
            state = self._parse_trainer_state(latest)
            return {
                "status": "running",
                "message": "Training in progress",
                "adapter_dir": latest.name if latest else None,
                **state,
            }

        # Check latest adapter dir for completion state
        latest = self._find_latest_adapter_dir(adapter_dirs)
        if not latest:
            return {"status": "idle", "message": "No training data found"}

        state = self._parse_trainer_state(latest)
        has_final = (latest / "final_adapter").exists()

        if has_final:
            return {
                "status": "completed",
                "message": "Training completed",
                "adapter_dir": latest.name,
                **state,
            }

        # Has checkpoints but no final adapter — interrupted
        checkpoints = sorted(latest.glob("checkpoint-*"))
        if checkpoints:
            return {
                "status": "interrupted",
                "message": f"Training interrupted at {checkpoints[-1].name}",
                "adapter_dir": latest.name,
                "last_checkpoint": checkpoints[-1].name,
                **state,
            }

        return {"status": "idle", "message": "No training runs detected"}

    def get_training_logs(self) -> dict:
        """Parse trainer_state.json for loss curves."""
        adapter_dirs = [
            d for d in self._adapters_dir.iterdir()
            if d.is_dir()
        ] if self._adapters_dir.exists() else []

        latest = self._find_latest_adapter_dir(adapter_dirs)
        if not latest:
            return {"loss_curve": [], "eval_losses": []}

        # Check main dir and checkpoints for trainer_state.json
        state_file = self._find_trainer_state(latest)
        if not state_file:
            return {"loss_curve": [], "eval_losses": []}

        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
            log_history = state.get("log_history", [])

            loss_curve = []
            eval_losses = []

            for entry in log_history:
                step = entry.get("step", 0)
                epoch = entry.get("epoch", 0)
                if "loss" in entry:
                    loss_curve.append({
                        "step": step,
                        "epoch": round(epoch, 2),
                        "loss": round(entry["loss"], 4),
                    })
                if "eval_loss" in entry:
                    eval_losses.append({
                        "step": step,
                        "epoch": round(epoch, 2),
                        "eval_loss": round(entry["eval_loss"], 4),
                    })

            return {
                "loss_curve": loss_curve,
                "eval_losses": eval_losses,
                "total_steps": state.get("global_step", 0),
                "max_steps": state.get("max_steps", 0),
                "epoch": state.get("epoch", 0),
                "num_train_epochs": state.get("num_train_epochs", 0),
            }
        except Exception:
            return {"loss_curve": [], "eval_losses": []}

    def get_dataset_analytics(self) -> dict:
        """Analyze training dataset quality distribution and counts."""
        result = {
            "train_count": 0,
            "val_count": 0,
            "quality_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            "total_examples": 0,
            "avg_instruction_len": 0,
            "avg_output_len": 0,
        }

        train_file = self._data_dir / "train.jsonl"
        val_file = self._data_dir / "val.jsonl"

        instruction_lens = []
        output_lens = []

        for filepath, key in [(train_file, "train_count"), (val_file, "val_count")]:
            if not filepath.exists():
                continue
            try:
                for line in filepath.open(encoding="utf-8"):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        example = json.loads(line)
                        result[key] += 1
                        result["total_examples"] += 1

                        quality = example.get("quality", example.get("score", 0))
                        if isinstance(quality, (int, float)) and 1 <= quality <= 5:
                            result["quality_distribution"][int(quality)] += 1

                        instruction = example.get("instruction", "")
                        output = example.get("output", "")
                        if instruction:
                            instruction_lens.append(len(instruction))
                        if output:
                            output_lens.append(len(output))
                    except json.JSONDecodeError:
                        continue
            except Exception:
                continue

        if instruction_lens:
            result["avg_instruction_len"] = round(sum(instruction_lens) / len(instruction_lens))
        if output_lens:
            result["avg_output_len"] = round(sum(output_lens) / len(output_lens))

        return result

    def get_training_examples(
        self,
        offset: int = 0,
        limit: int = 20,
        file: str = "train",
    ) -> dict:
        """Return paginated training examples from JSONL files."""
        filename = "train.jsonl" if file == "train" else "val.jsonl"
        filepath = self._data_dir / filename

        if not filepath.exists():
            return {"examples": [], "total": 0, "offset": offset, "file": file}

        examples = []
        total = 0

        try:
            with filepath.open(encoding="utf-8") as f:
                for i, line in enumerate(f):
                    line = line.strip()
                    if not line:
                        continue
                    total += 1
                    if total <= offset or len(examples) >= limit:
                        continue
                    try:
                        example = json.loads(line)
                        examples.append({
                            "index": total - 1,
                            "instruction": example.get("instruction", "")[:500],
                            "input": example.get("input", "")[:200],
                            "output": example.get("output", "")[:1000],
                            "quality": example.get("quality", example.get("score", None)),
                            "system": example.get("system", "")[:200],
                        })
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass

        return {"examples": examples, "total": total, "offset": offset, "file": file}

    def list_adapters(self) -> list[dict]:
        """Scan ADAPTERS_DIR for adapter directories with metadata."""
        if not self._adapters_dir.exists():
            return []

        adapters = []
        for adapter_dir in sorted(self._adapters_dir.iterdir()):
            if not adapter_dir.is_dir():
                continue

            info: dict = {
                "name": adapter_dir.name,
                "path": str(adapter_dir),
            }

            # Total size
            total_size = sum(
                f.stat().st_size for f in adapter_dir.rglob("*") if f.is_file()
            )
            info["size_mb"] = round(total_size / 1e6, 1)

            # Modified time
            try:
                mtime = adapter_dir.stat().st_mtime
                from datetime import datetime
                info["modified"] = datetime.fromtimestamp(mtime).isoformat()
            except Exception:
                info["modified"] = None

            # Check for final_adapter
            info["has_final"] = (adapter_dir / "final_adapter").exists()

            # Checkpoints
            checkpoints = sorted(adapter_dir.glob("checkpoint-*"))
            info["checkpoint_count"] = len(checkpoints)
            if checkpoints:
                info["latest_checkpoint"] = checkpoints[-1].name

            # Read adapter_config.json (in final_adapter or root)
            config = self._read_adapter_config(adapter_dir)
            if config:
                info["base_model"] = config.get("base_model_name_or_path", "unknown")
                info["lora_rank"] = config.get("r", None)
                info["lora_alpha"] = config.get("lora_alpha", None)
                info["target_modules"] = config.get("target_modules", [])
            else:
                info["base_model"] = BASE_MODEL
                info["lora_rank"] = None
                info["lora_alpha"] = None
                info["target_modules"] = []

            # Status
            if info["has_final"]:
                info["status"] = "completed"
            elif checkpoints:
                info["status"] = "interrupted"
            else:
                info["status"] = "empty"

            adapters.append(info)

        return adapters

    def get_adapter_details(self, name: str) -> Optional[dict]:
        """Detailed file listing + training state for one adapter."""
        adapter_dir = self._adapters_dir / name
        if not adapter_dir.exists() or not adapter_dir.is_dir():
            return None

        files = []
        for f in sorted(adapter_dir.rglob("*")):
            if f.is_file():
                files.append({
                    "path": str(f.relative_to(adapter_dir)),
                    "size_bytes": f.stat().st_size,
                    "size_str": self._format_size(f.stat().st_size),
                })

        state = self._parse_trainer_state(adapter_dir)
        config = self._read_adapter_config(adapter_dir)

        return {
            "name": name,
            "files": files,
            "file_count": len(files),
            "training_state": state,
            "adapter_config": config,
            "deploy_command": f"python -m fine_tuning.merge_adapter --adapter {adapter_dir / 'final_adapter'} --create-ollama",
        }

    # === Private helpers ===

    def _check_training_process(self) -> bool:
        """Check if a training process is running."""
        try:
            if sys.platform == "win32":
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV"],
                    capture_output=True, text=True, timeout=5,
                )
                return "train_lora" in result.stdout.lower()
            else:
                result = subprocess.run(
                    ["pgrep", "-f", "train_lora"],
                    capture_output=True, text=True, timeout=5,
                )
                return result.returncode == 0
        except Exception:
            return False

    def _find_latest_adapter_dir(self, adapter_dirs: list[Path]) -> Optional[Path]:
        """Find the most recently modified adapter directory."""
        if not adapter_dirs:
            return None
        return max(adapter_dirs, key=lambda d: d.stat().st_mtime)

    def _find_trainer_state(self, adapter_dir: Path) -> Optional[Path]:
        """Find trainer_state.json in adapter dir or its checkpoints."""
        # Check root
        state = adapter_dir / "trainer_state.json"
        if state.exists():
            return state

        # Check latest checkpoint
        checkpoints = sorted(adapter_dir.glob("checkpoint-*"))
        if checkpoints:
            state = checkpoints[-1] / "trainer_state.json"
            if state.exists():
                return state

        return None

    def _parse_trainer_state(self, adapter_dir: Optional[Path]) -> dict:
        """Extract summary from trainer_state.json."""
        if not adapter_dir:
            return {}

        state_file = self._find_trainer_state(adapter_dir)
        if not state_file:
            return {}

        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
            return {
                "global_step": state.get("global_step", 0),
                "max_steps": state.get("max_steps", 0),
                "epoch": state.get("epoch", 0),
                "num_train_epochs": state.get("num_train_epochs", 0),
                "best_metric": state.get("best_metric"),
                "best_model_checkpoint": state.get("best_model_checkpoint"),
            }
        except Exception:
            return {}

    def _read_adapter_config(self, adapter_dir: Path) -> Optional[dict]:
        """Read adapter_config.json from final_adapter or root."""
        for subdir in [adapter_dir / "final_adapter", adapter_dir]:
            config_path = subdir / "adapter_config.json"
            if config_path.exists():
                try:
                    return json.loads(config_path.read_text(encoding="utf-8"))
                except Exception:
                    continue
        return None

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1e6:
            return f"{size_bytes / 1024:.1f}KB"
        elif size_bytes < 1e9:
            return f"{size_bytes / 1e6:.1f}MB"
        return f"{size_bytes / 1e9:.1f}GB"

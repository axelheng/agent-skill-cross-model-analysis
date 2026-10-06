#!/usr/bin/env python3
"""Run staged controller-assisted debugging on the formal task battery."""
from __future__ import annotations
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = ("tool_debug_task", "boundary_debug_task", "empty_input_debug_task", "parsing_debug_task")
MODELS = ("llama3.1:8b", "qwen3.6:35b")

for model in MODELS:
    for task in TASKS:
        for rep in range(1, 4):
            run_id = f"staged-{model.replace(':', '-')}-{task}-{rep}"
            subprocess.run([sys.executable, str(ROOT / "scripts/run_agent_experiment.py"),
                            "--model", model, "--skill", "debugging-compact.md",
                            "--task", task, "--prompt-variant", "staged",
                            "--force-tool-sequence", "--staged", "--run-id", run_id],
                           cwd=ROOT, check=True)

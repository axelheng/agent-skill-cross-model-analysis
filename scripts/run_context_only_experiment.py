#!/usr/bin/env python3
from __future__ import annotations
import subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
for model in ("llama3.1:8b", "qwen3.6:35b"):
    for task in ("tool_debug_task", "boundary_debug_task", "empty_input_debug_task", "parsing_debug_task"):
        for rep in range(1, 4):
            subprocess.run([sys.executable, str(ROOT / "scripts/run_agent_experiment.py"),
                            "--model", model, "--skill", "debugging-compact.md", "--task", task,
                            "--prompt-variant", "context-only", "--run-id",
                            f"context-only-{model.replace(':','-')}-{task}-{rep}",
                            "--context-only"], cwd=ROOT, check=True)

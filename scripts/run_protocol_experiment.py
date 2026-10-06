#!/usr/bin/env python3
"""Run the focused protocol follow-up: baseline, compact, and controller."""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = ("tool_debug_task", "boundary_debug_task", "empty_input_debug_task", "parsing_debug_task")
MODELS = ("llama3.1:8b", "qwen3.6:35b")

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--repetitions", type=int, default=3)
    p.add_argument("--models", nargs="*", default=MODELS)
    args = p.parse_args()
    runner = ROOT / "scripts" / "run_agent_experiment.py"
    conditions = (
        ("baseline", "debugging-baseline.md", False),
        ("compact", "debugging-compact.md", False),
        ("controller", "debugging-compact.md", True),
    )
    for model in args.models:
        for task in TASKS:
            for condition, skill, forced in conditions:
                for rep in range(1, args.repetitions + 1):
                    run_id = f"protocol-{model.replace(':', '-')}-{condition}-{task}-{rep}"
                    command = [sys.executable, str(runner), "--model", model,
                               "--skill", skill, "--task", task,
                               "--prompt-variant", condition, "--run-id", run_id]
                    if forced:
                        command.append("--force-tool-sequence")
                    subprocess.run(command, cwd=ROOT, check=True)

if __name__ == "__main__":
    main()

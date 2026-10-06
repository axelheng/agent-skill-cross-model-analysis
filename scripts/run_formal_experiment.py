#!/usr/bin/env python3
"""Launch the preregistered formal debugging battery."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--repetitions", type=int)
    p.add_argument("--models", nargs="*")
    p.add_argument("--task", default=None)
    args = p.parse_args()
    design = json.loads((ROOT / "experiments" / "formal_tasks.json").read_text())
    repetitions = args.repetitions or design["repetitions"]
    models = args.models or design["models"]
    runner = ROOT / "scripts" / "run_agent_experiment.py"
    for model in models:
        for skill in design["skills"]:
            task_rows = ([{"name": args.task}] if args.task else design["tasks"])
            for task in task_rows:
                for repetition in range(1, repetitions + 1):
                    run_id = f"formal-{model.replace(':', '-')}-{skill.removesuffix('.md')}-{task['name']}-{repetition}"
                    subprocess.run([sys.executable, str(runner), "--model", model,
                                    "--skill", skill, "--task", task["name"],
                                    "--run-id", run_id], cwd=ROOT, check=True)

if __name__ == "__main__":
    main()

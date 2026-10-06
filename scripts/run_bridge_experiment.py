#!/usr/bin/env python3
"""Run the four-condition bridge experiment with identical repetitions."""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONDITIONS = {
    "minimal": ("minimal", "minimal"),
    "baseline": ("debugging-baseline.md", "full"),
    "revised": ("debugging-revised.md", "full"),
    "compact": ("debugging-compact.md", "compact"),
}

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--repetitions", type=int, default=3)
    p.add_argument("--task", default="tool_debug_task")
    args = p.parse_args()
    runner = ROOT / "scripts" / "run_agent_experiment.py"
    for condition, (skill, variant) in CONDITIONS.items():
        for rep in range(1, args.repetitions + 1):
            run_id = f"bridge-{args.model.replace(':', '-')}-{condition}-{args.task}-{rep}"
            subprocess.run([sys.executable, str(runner), "--model", args.model,
                            "--skill", skill, "--task", args.task,
                            "--prompt-variant", variant, "--run-id", run_id],
                           cwd=ROOT, check=True)

if __name__ == "__main__":
    main()

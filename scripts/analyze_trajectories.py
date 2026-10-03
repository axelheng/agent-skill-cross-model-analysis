#!/usr/bin/env python3
"""Summarize tool-enabled trajectory behavior without inspecting private keys."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def summarize(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    tool_events = [event for event in data["events"] if event["kind"] == "tool"]
    assistant_events = [event for event in data["events"] if event["kind"] == "assistant"]
    tools = [event.get("tool") for event in tool_events]
    return {
        "run_id": data["run_id"],
        "model": data["model"],
        "skill": data["skill"],
        "success": data.get("evaluation", {}).get("passed", False),
        "assistant_turns": len(assistant_events),
        "tool_calls": len(tool_events),
        "tool_sequence": tools,
        "tool_counts": dict(Counter(tools)),
        "duration_seconds": data.get("duration_seconds"),
        "usage": data.get("usage", {}),
        "api_errors": data.get("api_errors", []),
        "final_content": data.get("final_content"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    rows = [summarize(path) for path in args.paths]
    print(json.dumps(rows, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

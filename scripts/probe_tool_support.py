#!/usr/bin/env python3
"""Probe native tool-call support independently of the debugging skill."""

from __future__ import annotations

import argparse
import json
import os
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_env() -> dict[str, str]:
    values = {}
    path = ROOT / "soclaas.env"
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def settings() -> tuple[str, str]:
    env = load_env()
    base = os.environ.get("SOCLAAS_BASE_URL", env.get("SOCLAAS_BASE_URL"))
    key = os.environ.get("SOCLAAS_API_KEY", env.get("SOCLAAS_API_KEY"))
    if not base or not key:
        raise RuntimeError("SOCLAAS_BASE_URL and SOCLAAS_API_KEY are required")
    return base.rstrip("/"), key


TOOL = {
    "type": "function",
    "function": {
        "name": "list_files",
        "description": "List files in a directory.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
            "additionalProperties": False,
        },
    },
}


def call(base: str, key: str, payload: dict) -> dict:
    request = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    context = ssl.create_default_context()
    try:
        import certifi
        context.load_verify_locations(certifi.where())
    except ImportError:
        pass
    try:
        with urllib.request.urlopen(request, timeout=120, context=context) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        return {"_http_error": exc.code, "_detail": exc.read().decode(errors="replace")[-2000:]}
    except Exception as exc:
        return {"_client_error": repr(exc)}


def classify(response: dict) -> dict:
    choice = (response.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    native = message.get("tool_calls") or []
    text = message.get("content")
    parsed = []
    malformed = []
    for item in native:
        function = item.get("function") or {}
        raw = function.get("arguments", "")
        try:
            args = json.loads(raw) if isinstance(raw, str) else raw
            if not isinstance(args, dict):
                raise ValueError("arguments are not an object")
            parsed.append({"name": function.get("name"), "arguments": args})
        except Exception as exc:
            malformed.append({"name": function.get("name"), "raw_arguments": raw, "error": str(exc)})
    textual = bool(text and ("list_files" in text or "tool" in text.lower()))
    return {
        "finish_reason": choice.get("finish_reason"),
        "native_tool_calls": parsed,
        "malformed_native_calls": malformed,
        "textual_or_pseudo_tool_signal": textual,
        "content": text,
        "raw_response": response,
    }


def run_one(base: str, key: str, model: str, condition: str, repetition: int) -> dict:
    messages = [{"role": "user", "content": "Respond with exactly: ordinary response."}]
    payload = {"model": model, "messages": messages, "temperature": 0, "max_tokens": 120}
    if condition != "no_tools":
        messages[0]["content"] = "Use the available tool to list the current directory, then report what happened."
        payload["tools"] = [TOOL]
        payload["tool_choice"] = "auto" if condition == "auto" else {"type": "function", "function": {"name": "list_files"}}
    first = call(base, key, payload)
    result = {"condition": condition, "repetition": repetition, "first": classify(first)}
    calls = result["first"]["native_tool_calls"]
    if condition == "forced" and calls:
        tool_result = {"files": ["README.md"]}
        follow_messages = messages + [
            {"role": "assistant", "content": first.get("choices", [{}])[0].get("message", {}).get("content"), "tool_calls": first.get("choices", [{}])[0].get("message", {}).get("tool_calls")},
            {"role": "tool", "tool_call_id": (first.get("choices", [{}])[0].get("message", {}).get("tool_calls") or [{}])[0].get("id", "probe-call"), "content": json.dumps(tool_result)},
        ]
        follow = call(base, key, {"model": model, "messages": follow_messages, "tools": [TOOL], "tool_choice": "auto", "temperature": 0, "max_tokens": 120})
        result["follow_up"] = classify(follow)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="llama3.1:8b")
    parser.add_argument("--repetitions", type=int, default=3)
    args = parser.parse_args()
    base, key = settings()
    started = time.time()
    results = [run_one(base, key, args.model, condition, repetition)
               for condition in ("no_tools", "auto", "forced")
               for repetition in range(1, args.repetitions + 1)]
    artifact = {"model": args.model, "started_at_unix": started, "results": results}
    output = ROOT / "trajectories" / f"tool-support-{args.model.replace(':', '-')}.json"
    output.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "results": [{"condition": r["condition"], "repetition": r["repetition"], "native": len(r["first"]["native_tool_calls"]), "malformed": len(r["first"]["malformed_native_calls"]), "textual": r["first"]["textual_or_pseudo_tool_signal"], "follow_native": len(r.get("follow_up", {}).get("native_tool_calls", []))} for r in results]}))


if __name__ == "__main__":
    main()

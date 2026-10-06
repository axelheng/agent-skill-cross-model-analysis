#!/usr/bin/env python3
"""Run a reproducible tool-enabled agent trajectory against the debug task."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import ssl
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TASK_ROOT = REPO_ROOT / "experiments" / "tool_debug_task"
SKILLS_ROOT = REPO_ROOT / "experiments" / "skills"
MAX_TOOL_OUTPUT = 12000
PRISTINE_SOURCE = '''"""Helpers for filtering and aggregating a small expense report."""


def summarize_by_category(rows, category=None):
    """Return total amounts grouped by category.

    Categories are case-insensitive and surrounding whitespace is ignored.
    Amounts are integer cents so the function does not introduce float error.
    """
    totals = {}
    for row in rows:
        row_category = row["category"].strip().lower()
        if category is not None and row_category != category:
            continue
        totals[row_category] = totals.get(row_category, 0) + row["cents"]
    return dict(sorted(totals.items()))
'''

def pristine_source(task_name: str) -> str:
    template = REPO_ROOT / "experiments" / "task_templates" / task_name / "expense_report.py"
    return template.read_text(encoding="utf-8") if template.exists() else PRISTINE_SOURCE


def load_env_file(path: Path) -> dict[str, str]:
    values = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def api_settings() -> tuple[str, str]:
    local = load_env_file(REPO_ROOT / "soclaas.env")
    base_url = os.environ.get("SOCLAAS_BASE_URL", local.get("SOCLAAS_BASE_URL"))
    api_key = os.environ.get("SOCLAAS_API_KEY", local.get("SOCLAAS_API_KEY"))
    if not base_url or not api_key:
        raise RuntimeError("SOCLAAS_BASE_URL and SOCLAAS_API_KEY are required")
    return base_url.rstrip("/"), api_key


def safe_path(relative_path: str) -> Path:
    candidate = (TASK_ROOT / relative_path).resolve()
    if candidate != TASK_ROOT and TASK_ROOT not in candidate.parents:
        raise ValueError("path must stay inside the task repository")
    return candidate


def run_tests() -> dict:
    started = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=TASK_ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )
    output = (proc.stdout + proc.stderr)[-MAX_TOOL_OUTPUT:]
    return {
        "passed": proc.returncode == 0,
        "returncode": proc.returncode,
        "duration_seconds": round(time.perf_counter() - started, 4),
        "output": output,
    }


def execute_tool(name: str, arguments: dict) -> dict:
    if name == "list_files":
        root = safe_path(arguments.get("path", "."))
        if not root.is_dir():
            raise ValueError("path is not a directory")
        files = sorted(
            str(path.relative_to(TASK_ROOT))
            for path in root.rglob("*")
            if path.is_file() and ".git" not in path.parts
        )
        return {"files": files}

    if name == "read_file":
        path = safe_path(arguments["path"])
        if not path.is_file():
            raise ValueError("file does not exist")
        return {"path": arguments["path"], "content": path.read_text(encoding="utf-8")}

    if name == "run_tests":
        return run_tests()

    if name == "replace_in_file":
        relative = arguments["path"]
        if relative.startswith("tests/") or "/tests/" in relative:
            raise ValueError("editing tests is not allowed")
        path = safe_path(relative)
        old = arguments["old"]
        new = arguments["new"]
        content = path.read_text(encoding="utf-8")
        occurrences = content.count(old)
        if occurrences != 1:
            raise ValueError(f"expected exactly one match, found {occurrences}")
        path.write_text(content.replace(old, new), encoding="utf-8")
        return {"path": relative, "changed": True, "matches_replaced": occurrences}

    raise ValueError(f"unknown tool: {name}")


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in the task repository or a subdirectory.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Relative directory, default ."}},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a UTF-8 text file using a path relative to the task repository.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_tests",
            "description": "Run the complete unittest suite in the task repository.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "replace_in_file",
            "description": "Replace one exact text span in a source file. Tests cannot be edited.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "old": {"type": "string"},
                    "new": {"type": "string"},
                },
                "required": ["path", "old", "new"],
                "additionalProperties": False,
            },
        },
    },
]


def call_api(base_url: str, api_key: str, payload: dict) -> dict:
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        context = ssl.create_default_context()
        try:
            import certifi

            context.load_verify_locations(certifi.where())
        except ImportError:
            pass
        with urllib.request.urlopen(request, timeout=120, context=context) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[-2000:]
        raise RuntimeError(f"API HTTP {exc.code}: {detail}") from exc


def sha256_json(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def classify_native_or_pseudo(message: dict) -> dict:
    calls = message.get("tool_calls") or []
    content = message.get("content") or ""
    pseudo = any(token in content.lower() for token in ("list_files", "read_file", "run_tests", "replace_in_file", "tool_call"))
    return {"native_call": bool(calls), "pseudo_call": bool(pseudo and not calls), "call_count": len(calls)}


def normalized_tool_calls(calls: list[dict]) -> list[dict]:
    """Keep the conversation valid when a provider emits malformed arguments."""
    normalized = []
    for call in calls:
        item = json.loads(json.dumps(call))
        function = item.setdefault("function", {})
        raw = function.get("arguments", "{}")
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
            if not isinstance(parsed, dict):
                raise ValueError
        except (TypeError, ValueError, json.JSONDecodeError):
            parsed = {}
        function["arguments"] = json.dumps(parsed, ensure_ascii=False)
        normalized.append(item)
    return normalized


def run(model: str, skill_name: str, run_id: str, max_steps: int, force_first_tool: bool,
        task_name: str = "tool_debug_task", prompt_variant: str = "full",
        force_tool_sequence: bool = False, staged: bool = False,
        repair_only: bool = False, context_only: bool = False) -> Path:
    global TASK_ROOT
    TASK_ROOT = REPO_ROOT / "experiments" / task_name
    if not TASK_ROOT.exists():
        raise FileNotFoundError(f"unknown task fixture: {task_name}")
    base_url, api_key = api_settings()
    source = pristine_source(task_name)
    (TASK_ROOT / "src" / "expense_report.py").write_text(source, encoding="utf-8")
    if skill_name == "minimal":
        skill_text = "You have executable tools. Inspect the repository, fix the bug in source, and run the tests after editing. Do not edit tests."
    else:
        skill_path = SKILLS_ROOT / skill_name
        skill_text = skill_path.read_text(encoding="utf-8")
    skill_sha256 = hashlib.sha256(skill_text.encode("utf-8")).hexdigest()
    system = (
        skill_text
        + "\n\nYou have access to a fixed task repository through tools. "
        + "Tool paths are relative to that repository. Do not claim success without validation."
    )
    if staged:
        system += "\nThe controller will provide valid source and test paths. Focus on diagnosing the bug, proposing the minimal source edit, and validating it."
    user = (
        "Fix the failing behavior in the expense-report repository. Use the tools to inspect "
        "the source and tests, reproduce the failure, make the minimal source change, and "
        "run the full test suite after editing. Do not edit tests. When done, summarize the "
        "root cause, changed file, and final test result."
    )
    if repair_only:
        repair_hints = {
            "tool_debug_task": 'The faulty expression is `row_category != category` in `src/expense_report.py`. Normalize the requested category before comparing.',
            "boundary_debug_task": 'The faulty expression is `high - 1` in `src/expense_report.py`. The upper bound is inclusive.',
            "empty_input_debug_task": 'The faulty expression is `sum(values) / len(values)` in `src/expense_report.py`. Empty input should return None.',
            "parsing_debug_task": 'The faulty expression is `text.split()[0]` in `src/expense_report.py`. Invalid trailing text must be rejected.',
        }
        user = ("Make the minimal source-only repair described here: " + repair_hints[task_name] +
                " Use replace_in_file to apply it, then run the full tests. Do not edit tests.")
    if context_only:
        context_hints = {
            "tool_debug_task": 'The failing test is `summarize_by_category(ROWS, "FOOD") == {"food": 1500}` but the result is `{}`. The relevant source compares a normalized row category with the requested category.',
            "boundary_debug_task": 'The failing tests expect clamp_score(100) == 100 and clamp_score(101) == 100, but both return 99. The relevant source clamps with min(max(score, low), high - 1).',
            "empty_input_debug_task": 'The failing test expects average([]) is None, but the function raises ZeroDivisionError. The relevant source returns sum(values) / len(values).',
            "parsing_debug_task": 'The failing test expects parse_amount("12.5 cents") to raise ValueError, but it returns a value. The relevant source parses text.split()[0].',
        }
        user = ("Diagnose and fix this failing behavior using replace_in_file, then run the full tests. "
                "Do not edit tests. Do not assume success without validation. Relevant evidence: " + context_hints[task_name])
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    events = []
    started = time.perf_counter()
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "steps": 0}
    step_usage = []
    final_content = None
    api_errors = []

    for step in range(max_steps):
        request_payload = {
            "model": model,
            "messages": messages,
            "tools": TOOLS,
            "tool_choice": "auto",
            "temperature": 0,
            "max_tokens": 2400,
        }
        if force_first_tool and step == 0:
            request_payload["tool_choice"] = {
                "type": "function",
                "function": {"name": "list_files"},
            }
        if repair_only and step == 0:
            request_payload["tool_choice"] = {"type": "function", "function": {"name": "replace_in_file"}}
        completed_tool_count = sum(1 for event in events if event["kind"] == "tool")
        if force_tool_sequence and completed_tool_count < 6:
            request_payload["tool_choice"] = {
                "type": "function",
                "function": {
                    "name": [
                        "list_files",
                        "read_file",
                        "read_file",
                        "run_tests",
                        "replace_in_file",
                        "run_tests",
                    ][completed_tool_count]
                },
            }
        try:
            response = call_api(base_url, api_key, request_payload)
        except Exception as exc:  # retain an inspectable artifact on failure
            api_errors.append(str(exc))
            break
        choice = response.get("choices", [{}])[0]
        message = choice.get("message", {})
        if response.get("usage"):
            current = response["usage"]
            step_usage.append(current)
            for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
                usage[key] += int(current.get(key, 0) or 0)
            usage["steps"] += 1
        raw_tool_calls = message.get("tool_calls") or []
        safe_tool_calls = normalized_tool_calls(raw_tool_calls)
        assistant_message = {
            "role": "assistant",
            "content": message.get("content"),
        }
        if safe_tool_calls:
            assistant_message["tool_calls"] = safe_tool_calls
        messages.append(assistant_message)
        events.append(
            {
                "step": step,
                "kind": "assistant",
                "content": message.get("content"),
                "tool_calls": raw_tool_calls,
                "finish_reason": choice.get("finish_reason"),
                "call_classification": classify_native_or_pseudo(message),
                "usage": response.get("usage", {}),
            }
        )
        tool_calls = safe_tool_calls
        if staged:
            for call in tool_calls:
                name = call.get("function", {}).get("name")
                if name == "list_files":
                    call["function"]["arguments"] = json.dumps({"path": "."})
                elif name == "read_file":
                    reads = sum(1 for event in events if event["kind"] == "tool" and event.get("tool") == "read_file")
                    call["function"]["arguments"] = json.dumps({"path": "src/expense_report.py" if reads == 0 else "tests/test_expense_report.py"})
                elif name == "run_tests":
                    call["function"]["arguments"] = "{}"
        if not tool_calls:
            final_content = message.get("content")
            break
        for tool_call in tool_calls:
            name = tool_call.get("function", {}).get("name")
            raw_args = tool_call.get("function", {}).get("arguments", "{}")
            arguments = {}
            try:
                arguments = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                result = execute_tool(name, arguments)
            except Exception as exc:
                result = {"error": str(exc)}
            result_text = json.dumps(result, ensure_ascii=False)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.get("id", f"call-{step}"),
                    "content": result_text,
                }
            )
            events.append(
                {
                    "step": step,
                    "kind": "tool",
                    "tool": name,
                    "arguments": arguments,
                    "result": result,
                }
            )
    evaluation = run_tests()
    final_text = (final_content or "").lower()
    grounding = {
        "claims_tests_pass": any(x in final_text for x in ("tests pass", "all tests pass", "test suite pass")),
        "independent_tests_pass": evaluation["passed"],
        "success_claim_grounded": not any(x in final_text for x in ("tests pass", "all tests pass", "test suite pass")) or evaluation["passed"],
        "mentions_changed_file": "expense_report.py" in final_text,
    }
    artifact = {
        "schema_version": 1,
        "run_id": run_id,
        "model": model,
        "skill": skill_name,
        "skill_sha256": skill_sha256,
        "prompt_sha256": hashlib.sha256((system + "\n" + user).encode()).hexdigest(),
        "prompt_variant": prompt_variant,
        "task": task_name,
        "task_fixture_sha256": hashlib.sha256(source.encode() + b"".join(
            p.read_bytes() for p in sorted(TASK_ROOT.rglob("*"))
            if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts
        )).hexdigest(),
        "tool_schema_sha256": sha256_json(TOOLS),
        "started_at_unix": time.time(),
        "duration_seconds": round(time.perf_counter() - started, 3),
        "max_steps": max_steps,
        "force_first_tool": force_first_tool,
        "force_tool_sequence": force_tool_sequence,
        "staged": staged,
        "repair_only": repair_only,
        "context_only": context_only,
        "events": events,
        "final_content": final_content,
        "usage": usage,
        "step_usage": step_usage,
        "api_errors": api_errors,
        "evaluation": evaluation,
        "grounding": grounding,
    }
    output = REPO_ROOT / "trajectories" / f"{run_id}.json"
    output.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "evaluation": evaluation, "api_errors": api_errors}))
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--skill", required=True, help="Skill filename under experiments/skills, or 'minimal'")
    parser.add_argument("--task", default="tool_debug_task")
    parser.add_argument("--prompt-variant", default="full")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--max-steps", type=int, default=12)
    parser.add_argument(
        "--force-first-tool",
        action="store_true",
        help="Diagnostic only: require list_files on the first API response",
    )
    parser.add_argument("--staged", action="store_true", help="Provide valid inspection paths while leaving diagnosis/editing to the model")
    parser.add_argument("--repair-only", action="store_true", help="Supply the diagnosis and test repair generation directly")
    parser.add_argument("--context-only", action="store_true", help="Supply failing evidence and source context without the diagnosis")
    parser.add_argument(
        "--force-tool-sequence",
        action="store_true",
        help="Diagnostic only: require the standard six-step tool sequence",
    )
    args = parser.parse_args()
    run(args.model, args.skill, args.run_id, args.max_steps, args.force_first_tool,
        args.task, args.prompt_variant, args.force_tool_sequence, args.staged, args.repair_only, args.context_only)


if __name__ == "__main__":
    main()

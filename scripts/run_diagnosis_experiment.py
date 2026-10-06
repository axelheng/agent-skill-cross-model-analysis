#!/usr/bin/env python3
"""Evaluate diagnosis without tools, editing, or repository navigation."""
from __future__ import annotations
import json, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_agent_experiment import api_settings, call_api

ROOT = Path(__file__).resolve().parents[1]
CASES = {
 "tool_debug_task": ("The test expects the case-insensitive FOOD filter to return food rows, but gets {}. The source normalizes row categories before comparing.", ("lower", "normalize", "category")),
 "boundary_debug_task": ("The tests expect clamp_score(100) and clamp_score(101) to return 100, but both return 99. The source uses high - 1.", ("inclusive", "high", "bound")),
 "empty_input_debug_task": ("average([]) raises ZeroDivisionError, but the test expects None. The source returns sum(values) / len(values).", ("empty", "none", "len")),
 "parsing_debug_task": ("parse_amount('12.5 cents') should raise ValueError, but returns a value. The source parses text.split()[0].", ("invalid", "reject", "trailing")),
}

def main():
    base, key = api_settings(); rows=[]
    for model in ("llama3.1:8b", "qwen3.6:35b"):
      for task, (evidence, terms) in CASES.items():
       for rep in range(1,4):
        prompt = evidence + "\nIdentify the faulty logic and describe the minimal correction. Do not use tools or edit files."
        response = call_api(base, key, {"model":model,"messages":[{"role":"user","content":prompt}],"temperature":0,"max_tokens":500})
        text=((response.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
        lower=text.lower(); correct=sum(t in lower for t in terms) >= 2
        rows.append({"model":model,"task":task,"repetition":rep,"diagnosis_correct":correct,"response":text,"usage":response.get("usage",{})})
    out=ROOT/"trajectories"/"diagnosis-only-results.json"; out.write_text(json.dumps({"results":rows},indent=2)+"\n")
    print(json.dumps({"output":str(out),"runs":len(rows),"correct":sum(r["diagnosis_correct"] for r in rows)}))

if __name__ == "__main__": main()

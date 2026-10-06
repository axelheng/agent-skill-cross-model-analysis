#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_agent_experiment import api_settings, call_api

ROOT = Path(__file__).resolve().parents[1]
CASES = {
 "tool_debug_task": ("Normalize the requested category before comparing it with normalized row categories.", 'row_category != category', 'row_category != category.strip().lower()'),
 "boundary_debug_task": ("The clamp upper bound is inclusive.", 'high - 1', 'high'),
 "empty_input_debug_task": ("Return None when the input list is empty before dividing.", 'return sum(values) / len(values)', 'if not values:\n        return None\n    return sum(values) / len(values)'),
 "parsing_debug_task": ("Reject input with trailing non-numeric text instead of parsing only its first token.", 'text.split()[0]', 'text'),
}

def main():
    base,key=api_settings(); rows=[]
    for model in ('llama3.1:8b','qwen3.6:35b'):
      for task,(diagnosis,old,new) in CASES.items():
       for rep in range(1,4):
        prompt=(f"Diagnosis: {diagnosis}\nProduce only valid JSON with keys file, old, and new. "
                "The file is src/expense_report.py. The old value must be an exact source span and new must be the minimal replacement.")
        response=call_api(base,key,{"model":model,"messages":[{"role":"user","content":prompt}],"temperature":0,"max_tokens":500})
        text=((response.get('choices') or [{}])[0].get('message') or {}).get('content') or ''
        parsed=None
        try:
         parsed=json.loads(text[text.find('{'):text.rfind('}')+1])
        except Exception: pass
        exact=bool(isinstance(parsed,dict) and parsed.get('file')=='src/expense_report.py' and parsed.get('old')==old and parsed.get('new')==new)
        rows.append({'model':model,'task':task,'repetition':rep,'exact_patch':exact,'response':text})
    out=ROOT/'trajectories'/'structured-patch-results.json'; out.write_text(json.dumps({'results':rows},indent=2)+'\n')
    print(json.dumps({'output':str(out),'runs':len(rows),'exact':sum(r['exact_patch'] for r in rows)}))
if __name__=='__main__': main()

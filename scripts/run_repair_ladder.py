#!/usr/bin/env python3
from __future__ import annotations
import json, shutil, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from run_agent_experiment import api_settings, call_api, pristine_source
ROOT=Path(__file__).resolve().parents[1]
CASES={
"tool_debug_task":("Normalize the requested category before comparing it with normalized row categories.",'The test expects summarize_by_category(ROWS, "FOOD") to return {"food": 1500}.',"row_category != category"),
"boundary_debug_task":("The clamp upper bound is inclusive.",'The tests expect clamp_score(100) and clamp_score(101) to return 100.',"high - 1"),
"empty_input_debug_task":("Return None for an empty list before dividing.",'The test expects average([]) to be None, but it raises ZeroDivisionError.',"sum(values) / len(values)"),
"parsing_debug_task":("Reject trailing non-numeric text instead of parsing only its first token.",'The test expects parse_amount("12.5 cents") to raise ValueError.',"text.split()[0]"),}
TOOL={"type":"function","function":{"name":"submit_patch","description":"Submit one minimal source patch.","parameters":{"type":"object","properties":{"file":{"type":"string"},"old":{"type":"string"},"new":{"type":"string"}},"required":["file","old","new"],"additionalProperties":False}}}
def main():
 base,key=api_settings(); rows=[]
 for task,(diag,test,old_hint) in CASES.items():
  src=pristine_source(task)
  for variant in ('diagnosis','source','source_and_test'):
   for rep in range(1,4):
    extra='' if variant=='diagnosis' else f' Relevant source expression: `{old_hint}`.'
    if variant=='source_and_test': extra+=f' {test}'
    prompt=f"Diagnosis: {diag}.{extra} Use submit_patch exactly once. Submit a minimal patch for src/expense_report.py."
    res=call_api(base,key,{"model":"llama3.1:8b","messages":[{"role":"user","content":prompt}],"tools":[TOOL],"tool_choice":{"type":"function","function":{"name":"submit_patch"}},"temperature":0,"max_tokens":700})
    msg=(res.get('choices') or [{}])[0].get('message') or {}; calls=msg.get('tool_calls') or []; patch=None
    try: patch=json.loads(calls[0]['function']['arguments']) if calls else None
    except Exception: pass
    applied=passed=False
    if isinstance(patch,dict) and patch.get('file')=='src/expense_report.py':
     with tempfile.TemporaryDirectory() as td:
      root=Path(td); (root/'src').mkdir(); shutil.copytree(ROOT/'experiments'/task/'tests',root/'tests'); (root/'src'/'__init__.py').write_text(''); target=root/'src'/'expense_report.py'; target.write_text(src); text=target.read_text()
      if isinstance(patch.get('old'),str) and text.count(patch['old'])==1:
       target.write_text(text.replace(patch['old'],patch.get('new',''))); applied=True; p=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests'],cwd=root,capture_output=True); passed=p.returncode==0
    rows.append({'task':task,'variant':variant,'repetition':rep,'native':bool(calls),'applied':applied,'passed':passed,'patch':patch})
 out=ROOT/'trajectories'/'repair-ladder-results.json'; out.write_text(json.dumps({'results':rows},indent=2)+'\n'); print(json.dumps({'output':str(out),'runs':len(rows),'applied':sum(x['applied'] for x in rows),'passed':sum(x['passed'] for x in rows)}))
if __name__=='__main__': main()

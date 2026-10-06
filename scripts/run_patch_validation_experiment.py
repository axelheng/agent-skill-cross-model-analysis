#!/usr/bin/env python3
from __future__ import annotations
import json, shutil, subprocess, tempfile, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_agent_experiment import api_settings, call_api, pristine_source

ROOT=Path(__file__).resolve().parents[1]
PATCH_TOOL={"type":"function","function":{"name":"submit_patch","description":"Submit one minimal source patch.","parameters":{"type":"object","properties":{"file":{"type":"string"},"old":{"type":"string"},"new":{"type":"string"}},"required":["file","old","new"],"additionalProperties":False}}}
DIAG={"tool_debug_task":"Normalize the requested category before comparing it with normalized row categories.","boundary_debug_task":"The clamp upper bound is inclusive; replace the erroneous high - 1 behavior.","empty_input_debug_task":"Return None for an empty list before dividing.","parsing_debug_task":"Reject trailing non-numeric text instead of parsing only its first token."}

def main():
 base,key=api_settings(); rows=[]
 for model in ('llama3.1:8b','qwen3.6:35b'):
  for task,diagnosis in DIAG.items():
   for rep in range(1,4):
    prompt=(f"Diagnosis: {diagnosis} Use the submit_patch tool exactly once. Submit the minimal source-only repair for src/expense_report.py. Do not write prose.")
    res=call_api(base,key,{"model":model,"messages":[{"role":"user","content":prompt}],"tools":[PATCH_TOOL],"tool_choice":{"type":"function","function":{"name":"submit_patch"}},"temperature":0,"max_tokens":700})
    msg=(res.get('choices') or [{}])[0].get('message') or {}; calls=msg.get('tool_calls') or []; patch=None
    if calls:
     try: patch=json.loads(calls[0]['function']['arguments'])
     except Exception: pass
    passed=False; applied=False; test_output=''
    if isinstance(patch,dict) and patch.get('file')=='src/expense_report.py':
     with tempfile.TemporaryDirectory() as td:
      root=Path(td); (root/'src').mkdir(); (root/'tests').mkdir()
      shutil.copytree(ROOT/'experiments'/task/'tests',root/'tests',dirs_exist_ok=True)
      (root/'src'/'__init__.py').write_text(''); (root/'src'/'expense_report.py').write_text(pristine_source(task))
      target=root/'src'/'expense_report.py'; text=target.read_text();
      if isinstance(patch.get('old'),str) and text.count(patch['old'])==1:
       target.write_text(text.replace(patch['old'],patch.get('new',''))); applied=True
       proc=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests'],cwd=root,text=True,capture_output=True); passed=proc.returncode==0; test_output=(proc.stdout+proc.stderr)[-1200:]
    rows.append({'model':model,'task':task,'repetition':rep,'native_patch':bool(calls),'applied':applied,'tests_passed':passed,'patch':patch,'text':msg.get('content'),'test_output':test_output})
 out=ROOT/'trajectories'/'patch-validation-results.json'; out.write_text(json.dumps({'results':rows},indent=2)+'\n'); print(json.dumps({'output':str(out),'runs':len(rows),'native':sum(r['native_patch'] for r in rows),'applied':sum(r['applied'] for r in rows),'passed':sum(r['tests_passed'] for r in rows)}))
if __name__=='__main__': main()

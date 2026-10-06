#!/usr/bin/env python3
from __future__ import annotations
import json, shutil, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from run_agent_experiment import api_settings, call_api, pristine_source
ROOT=Path(__file__).resolve().parents[1]
CASES={"tool_debug_task":("Normalize the requested category before comparing it with normalized row categories.",'row_category != category'),"boundary_debug_task":("The clamp upper bound is inclusive.",'high - 1'),"empty_input_debug_task":("Return None for an empty list before dividing.",'return sum(values) / len(values)'),"parsing_debug_task":("Reject trailing non-numeric text instead of parsing only its first token.",'text.split()[0]')}
TOOL={"type":"function","function":{"name":"submit_replacement","description":"Submit only replacement code for the provided faulty span.","parameters":{"type":"object","properties":{"replacement":{"type":"string"}},"required":["replacement"],"additionalProperties":False}}}
def main():
 base,key=api_settings(); rows=[]
 for model in ('llama3.1:8b','qwen3.6:35b'):
  for task,(diag,old) in CASES.items():
   for rep in range(1,4):
    prompt=f"The controller has located this exact faulty source span: {old!r}. Diagnosis: {diag} Return only the corrected replacement code using submit_replacement."
    res=call_api(base,key,{"model":model,"messages":[{"role":"user","content":prompt}],"tools":[TOOL],"tool_choice":{"type":"function","function":{"name":"submit_replacement"}},"temperature":0,"max_tokens":400})
    msg=(res.get('choices') or [{}])[0].get('message') or {}; calls=msg.get('tool_calls') or []; replacement=None
    try: replacement=json.loads(calls[0]['function']['arguments']).get('replacement') if calls else None
    except Exception: pass
    applied=passed=False
    if isinstance(replacement,str):
     with tempfile.TemporaryDirectory() as td:
      root=Path(td); (root/'src').mkdir(); shutil.copytree(ROOT/'experiments'/task/'tests',root/'tests'); (root/'src'/'__init__.py').write_text(''); target=root/'src'/'expense_report.py'; text=pristine_source(task); target.write_text(text)
      if text.count(old)==1:
       target.write_text(text.replace(old,replacement)); applied=True; p=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests'],cwd=root,capture_output=True); passed=p.returncode==0
    rows.append({'model':model,'task':task,'repetition':rep,'native':bool(calls),'applied':applied,'passed':passed,'replacement':replacement})
 out=ROOT/'trajectories'/'replacement-only-results.json'; out.write_text(json.dumps({'results':rows},indent=2)+'\n'); print(json.dumps({'output':str(out),'runs':len(rows),'applied':sum(x['applied'] for x in rows),'passed':sum(x['passed'] for x in rows)}))
if __name__=='__main__': main()

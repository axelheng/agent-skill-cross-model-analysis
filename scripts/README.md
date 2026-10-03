# Scripts

Store small utilities used to run, parse, or summarize experiments here.

Run a trajectory without exposing the local API key:

```bash
python3 scripts/run_agent_experiment.py \
  --model llama3.1:8b \
  --skill debugging-baseline.md \
  --run-id tool-baseline-llama3.1-8b
```

The skill filename is resolved under `experiments/skills/`. The runner reads
`soclaas.env`, resets the fixture, records all assistant/tool events, and
writes the result under the ignored `trajectories/` directory. The optional
`--force-first-tool` flag is diagnostic only and should not be mixed into the
primary skill comparison.

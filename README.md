# Agent Skill Cross-Model Analysis

Research workspace for the UROP trial on how agent behavior changes across
models of different capability, and whether those observations can improve a
skill for weaker models.

## Project layout

- `experiments/` — experiment plans and run configurations
- `trajectories/` — saved agent trajectories (keep large/private data out of Git)
- `analysis/` — notebooks, metrics, and written analysis
- `scripts/` — reproducible utilities
- `report.md` — working research report

## Current milestone: formal experiment and diagnostic follow-ups

The repository contains the original tool-enabled pilot, a completed 48-run
formal battery, and follow-up protocol and scaffolding experiments. It compares
a baseline debugging skill with an evidence-gated revision, using the same
tools and related debugging fixtures across models. The runner saves full
trajectories under `trajectories/` (ignored by Git), and
`scripts/analyze_trajectories.py` summarizes tool behavior.

The initial pilot result is a useful capability boundary: `qwen3.6:35b` completed
the task with six native tool calls, while `llama3.1:8b` produced hypothetical
JSON tool-call examples and made no executable calls under either skill
revision. This is exploratory evidence, not yet the formal experiment or a
claim that the revised skill improves performance. See `analysis/tool-pilot.md`
and `report.md` for the phase labels, evidence, and limitations.

## Main result

The stronger model completed all formal tasks, while the weaker model failed to
sustain autonomous tool use under either skill. Follow-up scaffolding shows
that external sequencing and supplied diagnoses can partially recover behavior,
but do not demonstrate autonomous improvement. See `report.md` for the full
analysis and limitations.

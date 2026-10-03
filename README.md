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

## Current milestone: reconnaissance and pilots

The first tool-enabled pilot is implemented in
`experiments/tool_debug_task/`. It compares a baseline debugging skill with an
evidence-gated revision, using the same four tools and task repository for each
model. The runner saves full trajectories under `trajectories/` (ignored by
Git), and `scripts/analyze_trajectories.py` summarizes tool behavior.

The initial pilot result is a useful capability boundary: `qwen3.6:35b` completed
the task with six native tool calls, while `llama3.1:8b` produced hypothetical
JSON tool-call examples and made no executable calls under either skill
revision. This is exploratory evidence, not yet the formal experiment or a
claim that the revised skill improves performance. See `analysis/tool-pilot.md`
and `report.md` for the phase labels, evidence, and limitations.

## Next milestone: formal experiment

Before drawing conclusions, run 3–5 related tasks with repeated model/task
conditions, record the exact configuration, and evaluate whether any skill
change generalizes beyond the motivating pilot task.

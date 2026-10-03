# Analysis

Store metric definitions, notebooks, and analysis notes here.

## Primary pilot metrics

- **Task success:** independent post-run test suite passes.
- **Native tool-call compliance:** whether the model emits executable tool
  calls rather than describing them in prose.
- **Trajectory length:** assistant turns and tool calls.
- **Action sequence:** ordered tool names, including repeated tests or reads.
- **Cost and time:** API usage fields and wall-clock duration when available.
- **Grounding:** whether the final diagnosis matches observed tool results.

The first qualitative analysis is in `tool-pilot.md`.

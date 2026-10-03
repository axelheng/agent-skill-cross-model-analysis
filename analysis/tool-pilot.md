# Reconnaissance and initial tool-enabled pilot

This document records exploratory work completed before the formal experiment.
It establishes the task, trajectory schema, and an initial behavioral
hypothesis; it is not itself a statistically powered evaluation of skill
improvement.

## Design

The pilot uses a fixed Python repository with one known bug: row categories
are normalized with `strip().lower()`, but the optional filter argument is
compared without the same normalization. The tests contain one failing
case-insensitive filter assertion and two passing assertions. Every run starts
from the same buggy source and exposes the same tools:

1. `list_files`
2. `read_file`
3. `run_tests`
4. `replace_in_file`

The baseline skill gives general debugging instructions. The revised skill
adds explicit understand/reproduce/localize/patch/validate phases and requires
evidence before claiming success. A later protocol revision explicitly says
that the first response must be a native `list_files` call and forbids prose
JSON examples or hypothetical filenames.

## Results

| Run | Model | Skill condition | Success | Native tool calls | Sequence |
| --- | --- | --- | ---: | ---: | --- |
| baseline-small | `llama3.1:8b` | baseline | no | 0 | - |
| revised-small | `llama3.1:8b` | phased revision | no | 0 | - |
| baseline-large | `qwen3.6:35b` | baseline | yes | 6 | list, read, read, test, replace, test |
| revised-v2-small | `llama3.1:8b` | phase + protocol/evidence gates | no | 0 | - |
| forced-first-small | `llama3.1:8b` | diagnostic client-forced first tool | no | 0 | - |

The large model’s successful trajectory was concise and evidence-grounded:
it inspected the repository, read source and tests, reproduced the failure,
made one source-only replacement, reran the full suite, and reported the
observed result. The small model instead produced a prose plan containing
JSON-looking examples, invented filenames such as `source.py`, and claimed a
successful hypothetical fix. Its final repository still failed the same test.

Adding phase structure improved neither native-call compliance nor task
success in this sample. Requiring `list_files` through the client also did not
change the response, suggesting that the smaller model/endpoint combination
does not honor the native tool-call protocol in this configuration. This is a
diagnostic result, not proof that the model cannot use tools in every serving
configuration.

## Status and next phase

The pilot is complete. The formal experiment has not started. The next phase
should use multiple related tasks, repeated runs, exact configuration records,
and a predeclared success rubric. Only after that should a revised skill be
evaluated as an intervention.

## Interpretation and limits

The most informative difference is behavioral, not length: successful tool
execution versus simulated tool use. The sample is intentionally small—one
task, one run per main condition, and one strong/weak pair—so it cannot
support broad model rankings or causal claims about the revised skill. The
next experiment should add several related debugging tasks, repeated seeds if
the service exposes them, and a model/endpoint condition known to support
native tool calls for the weaker capability level.

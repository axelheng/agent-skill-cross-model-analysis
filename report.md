# Cross-Model Analysis and Optimization of Agent Skills

## Research questions

### Primary question

How does execution behavior differ when the same skill and task are executed
by models of substantially different capabilities?

### Secondary question

Can observed differences be used to modify the skill so that a weaker model
performs better?

## Study status and phase labels

This repository currently contains reconnaissance and pilot work, not a
completed formal experiment. The work is organized as:

1. **Reconnaissance:** read the brief, verify SoCLaaS access, inspect available
   models, and choose a candidate skill/task design.
2. **Pilot 1:** compare direct chat responses without tools or an external
   skill.
3. **Pilot 2:** compare tool-enabled trajectories on one controlled debugging
   task.
4. **Formal experiment (not yet run):** repeat the selected conditions across
   multiple related tasks and repetitions.
5. **Skill revision and re-evaluation (planned):** modify the skill based on
   trajectory evidence, then test generalization on held-out related tasks.

The pilot findings below are therefore hypothesis-generating. They should not
be presented as the final estimate of skill improvement.

## Experimental setup

The study uses two capability-separated SoCLaaS chat models from the initial
pilot: `llama3.1:8b` as the weaker model and `qwen3.6:35b` as the stronger
reference. The first agent task is a small Python repository-debugging task in
`experiments/tool_debug_task/`. Every run starts from the same buggy source,
receives the same user task, skill/task files, tool schemas, and independent
post-run test evaluation.

The tool interface has four actions: list files, read a file, run the complete
test suite, and replace one exact source span. Editing tests is rejected by the
runner. The baseline skill gives general debugging instructions. The revised
skill adds explicit phases, tool-use guidance, recovery guidance, and an
evidence gate for success claims. The runner records assistant messages,
native tool calls, tool results, API usage, duration, errors, and final test
status as JSON under the ignored `trajectories/` directory.

Primary metrics are task success, native tool-call compliance, ordered tool
sequence, repeated actions, token usage, duration, and final-answer grounding.

## Observations

### Pilot 1: direct chat comparison

The first pilot used the same prompt with two models:

> Explain how to debug a Python program that crashes at startup.

The request was sent directly to the SoCLaaS chat-completions endpoint. This
was a response-quality comparison, not yet an agent-trajectory experiment:
neither run used tools or an external skill.

| Model | Prompt tokens | Completion tokens | Total tokens | Response length |
| --- | ---: | ---: | ---: | ---: |
| `llama3.1:8b` | 23 | 684 | 707 | 79 lines / 3,172 characters |
| `qwen3.6:35b` | 25 | 1,583 | 1,608 | 255 lines / 6,479 characters |

Both responses completed normally with `finish_reason: stop`. The larger model
produced a substantially longer and more structured answer, with a broader
diagnostic checklist and more detailed examples. The smaller model also gave a
useful debugging procedure, but covered the topic more compactly.

These observations are preliminary: they come from one run per model, and
longer answers are not automatically better. Follow-up runs should use a
defined correctness rubric and, for the actual trial, the same skill and task
inside an agent environment so that tool calls, retries, and intermediate
actions can be compared.

### Pilot 2: tool-enabled repository debugging (reconnaissance)

For this pilot, each model received a small Python project with one known bug.
The project groups expenses by category. It changes row labels such as
`"Food"` into lowercase, `"food"`, but it does not make the user’s filter
input lowercase. As a result, asking for `"FOOD"` returns no results even
though food expenses exist. The expected fix is to normalize both values in
the same way.

Each model received the same four tools:

- list the project files
- read a file
- run the tests
- replace one exact piece of source code

A run means one model attempting the task from start to finish. The model had
to inspect the files, find the failing test, edit the source code, and run the
tests again.

| Run | Model | Skill | Success | Native tool calls | Ordered actions |
| --- | --- | --- | ---: | ---: | --- |
| baseline-small | `llama3.1:8b` | baseline | no | 0 | none |
| revised-small | `llama3.1:8b` | phase-gated revision | no | 0 | none |
| baseline-large | `qwen3.6:35b` | baseline | yes | 6 | list → read → read → test → replace → test |
| revised-v2-small | `llama3.1:8b` | protocol/evidence revision | no | 0 | none |

The stronger model completed the task correctly. Its recorded actions were:

```text
list files → read source and tests → run tests → edit source → run tests again
```

All three tests passed after its edit.

The weaker model behaved differently. It wrote examples of tool calls in its
answer, but did not actually call any tools. It also invented filenames and
claimed that the tests passed. The independent test check showed that the
source code had not changed and the original test was still failing.

We then gave the weaker model more detailed instructions: inspect first, run
the tests, edit only after finding the cause, and validate the fix. It still
did not make any real tool calls. We also ran a diagnostic where the client
asked for `list_files` as the first tool call. The model still returned text
instead of a real tool call. This suggests that the problem may be with the
model’s or serving system’s support for tool calls, rather than only with the
debugging instructions.

This leads to a simpler question: can the weaker model use tools when we give
it a setup that is known to support tool calls?

If it can, we should improve the skill instructions. If it still cannot, the
problem is probably a limitation of the model or tool interface, not the skill
itself.

## Formal experiment plan

The next phase should not reuse the single pilot task as its only evidence.
The proposed minimum design is 3–5 related debugging tasks, the same tool
schemas and skill text across models, and repeated runs for each model/task
condition. Before collecting results, record the exact model identifiers,
sampling parameters, tool protocol, task versions, success rubric, and
trajectory schema in `experiments/`.

The formal analysis should compare task success and native tool-call
compliance first, then inspect action sequences, redundant actions, failed
recoveries, cost, duration, and final-answer grounding. A skill change should
be motivated by a recurring failure pattern and evaluated on tasks that did
not motivate the change.

## Reproducibility

The task fixture and skill variants are in `experiments/`; the runner and
trajectory summarizer are in `scripts/`. For a new run, use the commands in
`scripts/README.md` with a local `soclaas.env`; that file is ignored and its
API key is never included in the repository. The committed code does not
contain credentials or generated trajectory data.

## Limitations and next steps

The agent pilot has one task, one main run per condition, and no repeated
seeds. The small model’s failure prevents a meaningful before/after estimate
of the revised skill’s task success. The current evidence is still useful for
trajectory taxonomy and for identifying native tool-call compliance as a
necessary prerequisite. A stronger follow-up would add 3–5 related debugging
tasks, repeat each condition, verify tool support independently, and manually
inspect representative successes and failures before drawing general claims.

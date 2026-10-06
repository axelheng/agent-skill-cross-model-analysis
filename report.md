# Debugging-Agent Experiment Report

## Executive summary

This study asks whether a written debugging skill can help a weaker model use
tools to repair code. We compare `llama3.1:8b` and `qwen3.6:35b` on the same
debugging tasks, first with a baseline skill and then with a revised skill that
explicitly requires inspection, reproduction, localization, patching, and
validation.

The main result is a clear capability separation, not a demonstrated skill
improvement. The stronger model completed every primary task under both skills.
The weaker model completed none of them and did not produce native tool calls
in the primary autonomous condition. Additional diagnostic experiments show
that the weaker model can emit tool calls, identify many bugs when given source
evidence, and sometimes repair code when given the diagnosis. Its main failure
is sustaining a grounded chain from evidence, to diagnosis, to an exact edit,
and then to passing tests.

The revised skill did not improve autonomous success in this study. The result
does not show that the revised wording made the weaker model worse. Both skill
versions produced zero successful runs for that model, so there is no observed
decline to attribute to the wording. The weaker model usually failed before
completing a multi-step tool-use trajectory, while the stronger model already
performed at the maximum observed success rate.

## Research questions

The study has two linked questions:

1. How does execution behavior change when the same skill and task are run with
   models of different capabilities?
2. Can observed differences in their trajectories motivate a skill revision
   that improves weaker-model performance and generalizes beyond the motivating
   examples?

The primary unit of success is an independently verified repair. A run
succeeds only when the independent test suite passes after the model's source
edit. Tests may not be edited.

The model can request a tool in two ways. A **native tool call** is a structured
API request that the runner can execute. A **pseudo-call** is ordinary text that
looks like a tool request but is not executable. Only native calls count as tool
use in this report.

## Study design

The primary comparison uses two models with a substantial capability gap, one
debugging skill in two versions, four small but distinct bug classes, and three
repetitions per condition:

| Factor | Choices |
| --- | --- |
| Models | `llama3.1:8b`, `qwen3.6:35b` |
| Skill versions | baseline, revised |
| Tasks | case normalization, inclusive boundary, empty input, parsing |
| Repetitions | 3 per model-skill-task condition |
| Primary outcome | independent test suite passes after the edit |
| Secondary outcomes | native calls, trajectory behavior, diagnosis, patch applicability |

This gives 2 models × 2 skills × 4 tasks × 3 repetitions = 48 primary runs.
The models were selected to make behavioral differences observable rather than
to estimate performance across the full model landscape. The tasks were kept
small so that a successful repair could be independently checked and the
failure point could be inspected in the trajectory.

The two skill files used in the primary comparison are
`experiments/skills/debugging-baseline.md` and
`experiments/skills/debugging-revised.md`. The compact and compact-recovery
skill files were used only in diagnostic prompt experiments.

## Task suite

| Task | Fault | Expected repair |
| --- | --- | --- |
| Case normalization | Requested category is not normalized before comparison. | Normalize it before comparing. |
| Boundary | Clamp uses `high - 1`, excluding the inclusive upper bound. | Use `high`. |
| Empty input | Empty average divides by zero. | Return `None` before division. |
| Parsing | Parser accepts trailing text such as `12.5 cents`. | Reject malformed trailing text. |

## Primary comparison

| Model | Skill | Runs | Successes | Native-call runs |
| --- | --- | ---: | ---: | ---: |
| `llama3.1:8b` | baseline | 12 | 0 | 0 |
| `llama3.1:8b` | revised | 12 | 0 | 0 |
| `qwen3.6:35b` | baseline | 12 | 12 | 12 |
| `qwen3.6:35b` | revised | 12 | 12 | 12 |

The revised skill made five stages explicit. **Inspect** means finding and
reading the relevant files. **Reproduce** means running the failing behavior or
tests. **Localize** means identifying the specific faulty logic. **Patch** means
making the smallest intended source change. **Validate** means running the
independent tests after the edit.

The revised skill produced no measurable improvement in this design. The
weaker model failed before completing an autonomous native multi-step
trajectory under either skill; the stronger model succeeded under both.

## Trajectory analysis

An agent trajectory is the complete sequence of model messages, tool requests,
tool results, edits, and test results produced during one run. We analyzed the
trajectories in two ways.

First, we counted outcomes such as successful repairs and native tool calls.
We also recorded whether a tool request was executable or only pseudo-call
text. Second, we manually inspected representative trajectories to identify
where the debugging process broke down. We used the following six stages:

1. tool-call emission;
2. repository and file navigation;
3. reproduction or interpretation of the failing behavior;
4. localization of the faulty logic;
5. generation of an exact source edit; and
6. validation of the resulting behavior.

The experiment runner also stores technical reproducibility information,
including the prompt, skill, fixture, and tool-schema hashes, as well as
per-step usage. These details make it possible to check that runs used the
intended inputs, but they are not themselves measures of task success.

This distinction matters because native-call counts alone do not measure
successful debugging. A model can make the expected calls and still produce an
incorrect edit or fail to validate it.

## What the diagnostic trials add

The additional trials are not independent primary evaluations. They are
capability-isolation experiments used to explain the primary result.

### Tool use and control

This section separates the ability to call tools from the ability to use them
successfully. In an isolated tool probe, the weaker model produced native calls
in all six tool-enabled repetitions. In the bridge experiment, we tested shorter
prompt variants. Shorter prompts enabled native calls, but paths and arguments
remained unreliable:

| Condition | Native calls | Successes |
| --- | ---: | ---: |
| Minimal prompt | 3/3 | 0/3 |
| Baseline | 0/3 | 0/3 |
| Revised | 0/3 | 0/3 |
| Compact | 3/3 | 0/3 |

We then tested two forms of external assistance. In the **controller**
experiment, an external program selected the next tool instead of asking the
model to choose it. The forced sequence was
`list_files → read_file → read_file → run_tests → replace_in_file → run_tests`.
In the **staged controller** experiment, the external program also supplied
valid file paths. Thus, these trials reduced two possible sources of failure:
choosing the wrong tool and navigating to the wrong file.

| Experiment | Model | Runs | Successes | Native-call runs |
| --- | --- | ---: | ---: | ---: |
| Controller | weaker | 12 | 0 | 12 |
| Controller | stronger | 12 | 12 | 12 |
| Staged controller | weaker | 12 | 0 | 12 |
| Staged controller | stronger | 12 | 12 | 12 |

The external controller made tool calls reliable, and the staged version made
file navigation reliable. Neither intervention made the weaker model diagnose
and repair the code reliably. This suggests that the central bottleneck is not
only tool availability, tool ordering, or path selection.

### Diagnosis and repair isolation

When the exact diagnosis and intended behavior were supplied, the model only
had to generate the replacement and validate it:

| Model | Runs | Successes |
| --- | ---: | ---: |
| Weaker | 12 | 6 |
| Stronger | 12 | 12 |

When the model received failing behavior and source evidence but had no tools or
editing responsibility, manual review found:

| Model | Runs | Diagnoses identifying the faulty logic |
| --- | ---: | ---: |
| Weaker | 12 | 9 |
| Stronger | 12 | 12 |

The weaker model missed the parsing diagnoses. These results show that the
weaker model has partial diagnosis and repair ability when the surrounding
workflow is simplified, but not reliable end-to-end debugging ability.

### Source grounding

**Source grounding** means referring to the literal code that is actually in the
file, rather than describing the code conceptually. For example, a patch should
quote the exact old source text that it intends to replace.

The structured-patch trial required a native `submit_patch` call with an `old`
source span and a replacement. The runner applied each patch to a temporary
copy of the fixture before testing. A patch was **applicable** if its `old` span
matched the file. It was **passing** if the resulting file passed the tests.

| Model | Runs | Native patch calls | Applicable patches | Passing patches |
| --- | ---: | ---: | ---: | ---: |
| Weaker | 12 | 12 | 0 | 0 |
| Stronger | 12 | 12 | 0 | 0 |

Both models followed the tool protocol, but none of the submitted `old` spans
matched the actual source. For example, the weaker model used a conceptual name
such as `requested_category` instead of literal code. The patches were therefore
validly formatted but unusable. This is a source-grounding failure, not merely
a JSON-format failure.

In a replacement-only control, the controller supplied the exact faulty span
and the model returned only replacement code. This removed the need for the
model to quote the old source, allowing us to test repair generation separately:

| Model | Runs | Applicable replacements | Passing replacements |
| --- | ---: | ---: | ---: |
| Weaker | 12 | 9 | 0 |
| Stronger | 12 | 11 | 3 |

Removing the burden of quoting the old source improved applicability, but the
weaker model still produced no passing repairs. The stronger model passed the
case-normalization task in all three repetitions but not the other tasks under
this particular protocol.

## Representative trajectories

- **Autonomous weaker-model failure:** In a baseline formal run, the model made
  zero native calls. It wrote hypothetical JSON examples for `list_files`,
  `run_tests`, and `read_file`, invented paths, and claimed a procedure rather
  than executing it. The independent tests remained failing.
- **Controller-assisted weaker-model failure:** With the next tool forced, the
  model made the expected native calls, including an edit and a final test. The
  final tests still failed, and its answer named an invented path
  (`expense-report/expense_report.py`) instead of the actual
  `src/expense_report.py`.
- **Repair-only weaker-model success:** In one empty-input run, the model used
  `replace_in_file` and `run_tests`, added the empty-input guard, and passed all
  tests. This demonstrates partial repair ability when diagnosis is supplied.
- **Stronger-model success:** In a baseline formal run, the stronger model
  followed `list_files → read_file → read_file → run_tests → replace_in_file →
  run_tests`, localized the normalization mismatch, changed one source line,
  and passed all tests.

## Skill modification and held-out evaluation

The revised skill was motivated by the stronger model's orderly trajectory and
the weaker model's premature or ungrounded actions. It made the implied
procedure explicit: inspect the repository, reproduce the failure, localize the
fault, make a minimal patch, and run the tests again.

The primary comparison found no improvement. A held-out evaluation then tested
the same baseline and revised workflows on a new zero-denominator percentage
task:

| Model | Runs | Successes | Native-call runs |
| --- | ---: | ---: | ---: |
| `llama3.1:8b` | 6 | 0 | 0 |
| `qwen3.6:35b` | 6 | 6 | 6 |

The held-out result matches the primary pattern. It strengthens the
model-separation finding, but it does not demonstrate that the revised skill
improves weaker-model performance.

## Overall interpretation

The evidence supports the following layered conclusion:

1. The weaker model has basic native tool-call capability.
2. It does not reliably sustain tool use in the full debugging loop.
3. External tool sequencing improves native calls but not task success.
4. Valid paths still do not make it reliably diagnose and edit code.
5. Supplying the diagnosis produces partial repair success.
6. Structured patch output is possible, but it is not reliably grounded in
   literal source text.

In plain language, the weaker model can sometimes use tools, identify a bug,
and make a repair when the hard reasoning or source span is supplied. It cannot
reliably manage the complete chain from evidence to diagnosis to exact edit to
passing tests.

## Limitations

- The study uses one model pair, three repetitions per primary condition, and
  four small related tasks.
- The weaker model's zero-success floor and the stronger model's perfect-score
  ceiling limit what can be learned about skill wording.
- The tasks are code-debugging tasks and may not represent other agent skills.
- Some diagnostic trials use externally supplied tools, paths, diagnoses, or
  source spans. Their success cannot be described as autonomous improvement.
- The diagnostic analyses are primarily counts and manual case studies; they do
  not yet provide a statistically powered analysis of token cost, latency, or
  trajectory length.

## Research directions

The results suggest several focused next steps:

1. **Grounded intermediate state:** Require the model to quote the exact file,
   function, and source span before proposing an edit, then test whether this
   reduces conceptual rather than literal patches.
2. **Failure-point intervention:** Compare separate interventions for tool
   emission, diagnosis, source grounding, and validation instead of treating
   the whole debugging skill as one block.
3. **Workflow scaffolding:** Test whether a controller that asks the model to
   produce a structured diagnosis before editing improves autonomous repair,
   while measuring the cost of that additional structure.
4. **Generalization:** Evaluate the best intervention on more held-out tasks,
   programming languages, and repository layouts.
5. **Predictive trajectory metrics:** Measure whether retries, repeated reads,
   premature edits, failed patches, or missing final tests predict success more
   reliably than raw tool-call counts.

The most immediate experiment is a grounded-diagnosis checkpoint: before any
edit, require the model to identify the literal source span, expected behavior,
and failing test. This directly targets the strongest failure pattern observed
in the diagnostic trials.

## Reproduction

The formal battery can be launched from the repository root with:

```bash
python3 scripts/run_formal_experiment.py --repetitions 3
```

This runs both models, both primary skills, all four formal tasks, and three
repetitions per condition. Individual runs can instead be launched with
`scripts/run_agent_experiment.py`; its `--skill` argument resolves filenames
under `experiments/skills/`.

For example:

```bash
python3 scripts/run_agent_experiment.py \
  --model llama3.1:8b \
  --skill debugging-baseline.md \
  --task tool_debug_task \
  --run-id example-baseline
```

Runs are saved as JSON files under `trajectories/`. Selected trajectory files
can be summarized with:

```bash
python3 scripts/analyze_trajectories.py trajectories/example-baseline.json
```

The runner reads the local model configuration, resets the fixture before each
run, executes the independent tests, and records the trajectory. Diagnostic
experiments use the additional launchers in `scripts/`, including
`run_bridge_experiment.py`, `run_staged_experiment.py`,
`run_diagnosis_experiment.py`, and `run_repair_only_experiment.py`.

## Reproducibility

Fixtures are under `experiments/`; launchers and evaluators are under `scripts/`;
raw trajectories are under ignored `trajectories/`. The runner records prompt,
skill, fixture, and tool-schema hashes, per-step usage, native/pseudo-call
classification, and independent test results. The repository therefore
contains the code and scripts needed to reproduce the primary experiments and
the diagnostic analyses.

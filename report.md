# Cross-Model Analysis and Optimization of Agent Skills

## Research questions

### Primary question

How does execution behavior differ when the same skill and task are executed
by models of substantially different capabilities?

### Secondary question

Can observed differences be used to modify the skill so that a weaker model
performs better?

## Experimental setup

To be filled in after reconnaissance of the available skills, tasks, models,
trajectory format, and evaluation interface.

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

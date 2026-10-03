# Tool-enabled debugging task

The agent receives a small Python repository with one failing behavior. Its
task is to use the provided tools to identify the root cause, make the minimal
code change, run the test suite, and report what changed.

The task is intentionally small enough for manual trajectory inspection while
still requiring a sequence of inspect -> diagnose -> edit -> validate actions.
The runner exposes the same tool definitions and repository snapshot to every
model and skill variant.

## Success criterion

The agent succeeds when all tests pass after its change and its final answer
correctly identifies the case-normalization bug in the category filter.

The expected fix is to normalize the requested filter in the same way as row
categories before comparing them. The agent should not change the tests or
remove the filtering behavior.

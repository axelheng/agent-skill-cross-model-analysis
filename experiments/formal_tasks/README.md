# Formal debugging task battery

`formal_tasks.json` defines the minimum formal design: four related tasks,
three repetitions, and two models. The existing case-normalization fixture is
the first task. The other three fixtures cover boundary conditions, empty
input, and parsing/validation; their tests intentionally fail before repair.

The bridge experiment compares minimal, baseline, revised, and compact prompts
on the existing fixture.

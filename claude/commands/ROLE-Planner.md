---
description: The planner drafts a step-by-step plan before a big change and waits for your approval
argument-hint: <what you want to build or change>
---
Use the `planificador` subagent to plan this: $ARGUMENTS

If nothing was given above, ask me what I want to plan before calling it.

Pass it the request as written plus any context from this conversation that helps (decisions
already made, files we looked at, constraints). When the plan comes back:
1. Show it to me in full.
2. If it has open questions, ask them.
3. **Do not implement anything** until I approve the plan.

Once I approve it, follow the plan step by step, run the project's tests after each step that
changes code, and offer `/ROLE-Reviewer` at the end.

Talk to me in Spanish.

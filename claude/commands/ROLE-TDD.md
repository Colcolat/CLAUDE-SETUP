---
description: Build a feature or fix a bug test-first - failing test, then the code, then cleanup
argument-hint: <new feature or bug to fix>
---
Use the `guia-tdd` subagent to implement this test-first: $ARGUMENTS

If nothing was given above, ask me what to build or fix before calling it.

When it finishes:
1. Run the full test suite yourself to confirm it passes; do not rely only on its report.
2. Show me the tests and code it added, and its explanation of the red → green → refactor
   cycle.
3. If it could not find how the project runs its tests, tell me instead of guessing.
4. Offer to run `/ROLE-Reviewer` before committing.

Talk to me in Spanish.

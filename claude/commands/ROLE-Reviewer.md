---
description: The reviewer checks your changes (or the last commit) and reports findings by severity
argument-hint: [file, folder or commit range; empty = uncommitted changes]
---
Use the `revisor` subagent to review: $ARGUMENTS

If nothing was given above, have it review the uncommitted changes (or the last commit if
there are none).

When it finishes, show me its full report. Check every critical and high finding in the code
yourself before proposing a fix, and tell me if one turns out to be wrong. Ask me before
changing anything.

Talk to me in Spanish.

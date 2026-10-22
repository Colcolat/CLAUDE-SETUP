---
description: Security audit of your changes or the project - secrets, injection, data leaks, dependencies
argument-hint: [file, folder or topic; empty = uncommitted changes]
---
Use the `seguridad` subagent to audit: $ARGUMENTS

If nothing was given above, have it audit the uncommitted changes (or the last commit if
there are none).

When it finishes, show me its full report. Check every critical and high finding in the code
yourself before proposing a fix, and tell me if one turns out to be wrong. If it found a real
secret already committed, tell me first: it has to be revoked, because deleting it from the
code is not enough. Do not change anything until I ask.

Talk to me in Spanish.

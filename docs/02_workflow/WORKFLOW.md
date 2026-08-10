# FleetVision Workflow

## Default task lifecycle

```text
Read core context
→ reconcile live Git state
→ define one task
→ read only task-specific references
→ Audit
→ Apply/Execute
→ Verify
→ update durable state if needed
→ explicit-path stage
→ commit/push only when authorized
→ remote verification
→ end session
```

## Operating rules

- Treat repository files, live Git facts, and cryptographic identities as durable evidence; chat is supporting context, not durable storage or authorization.
- Reconcile the current branch, `HEAD`, remote tracking state, worktree status, allowed paths, protected assets, and the applicable Gate before modification.
- Define one bounded task. Stop when the request conflicts with governance, expands scope, risks a protected asset, or lacks required authorization.
- Use Audit → Apply/Execute → Verify for high-risk work. Preserve no-overwrite behavior and inspect final paths before promotion.
- Stage explicit paths only. Never use broad staging commands such as `git add .` or `git add -A`.
- Commit and push only when the task explicitly authorizes them. Verify local `HEAD`, `origin/main`, and remote `main` after an authorized push.

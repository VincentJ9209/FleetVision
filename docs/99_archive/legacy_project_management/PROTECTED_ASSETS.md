# FleetVision Protected Assets

<!-- FLEETVISION-MANAGED:ASSET-REGISTER:BEGIN -->
## Protected asset register

| Asset | Protection rule |
|---|---|
| `outputs/metadata/external_assets/` | Protected untracked directory. Never stage, commit, delete, clean, move, or rewrite. |
| `dataset/01_raw/` and raw external-source roots | Immutable unless a specifically authorized controlled-restore/intake Gate says otherwise. |
| Canonical COCO annotations and canonical dataset manifests | No direct edit. Changes require proposal/staging, audit, promotion authorization, and post-promotion verification. |
| Registry files | No direct edit or repeated promotion. Registry mutation requires an explicit one-time Gate and before/after SHA256. |
| Failed staging and recovery evidence | Preserve until an explicit retention/disposal decision is recorded. |
| Model and training acceptance artifacts | Do not relabel acceptance based on narrative summaries; use authoritative metrics and Gate evidence. |

## Worktree invariant

Permitted final states:

- clean worktree; or
- only `?? outputs/metadata/external_assets/`

Any other staged, modified, deleted, renamed, or untracked path blocks Apply, Commit, and Push.
<!-- FLEETVISION-MANAGED:ASSET-REGISTER:END -->


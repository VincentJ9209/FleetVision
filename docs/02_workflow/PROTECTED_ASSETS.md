# FleetVision Protected Assets

The following assets are protected unless an active Gate explicitly authorizes the exact mutation, with the required audit and verification evidence.

| Protected class | Rule |
|---|---|
| `outputs/metadata/external_assets/` | Never stage, commit, delete, clean, move, or rewrite. |
| `dataset/01_raw/` | Never modify. |
| Completed or active human-review workbooks | Never overwrite, rebuild, or save merely for inspection. |
| Reviewer manifests and manual-review ZIPs | Preserve as formal review artifacts. |
| Frozen backups and SHA256 manifests | Preserve identity and recovery evidence. |
| Canonical CSV, COCO, and dataset manifests | No direct mutation without an explicit controlled promotion Gate. |
| External source archives | Preserve source lineage and licensing evidence. |
| Internal holdout definitions | Keep separate from external data and do not change for performance. |
| Registry assets | No direct edit or repeated promotion without explicit authorization. |
| Model and training acceptance artifacts | Do not relabel acceptance from narrative summaries. |

Use read-only inspection whenever possible. Keep failed or staging evidence until a recorded retention decision permits disposal. Use isolated temporary paths for tests and no-overwrite promotion with SHA256 verification for high-risk replacement.

Current portfolio maintenance does not authorize Frozen Test access, raw or canonical mutation, Registry mutation, training, fine-tuning, model replacement, or Phase 05S-A3 implementation.

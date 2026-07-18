# G0 preflight and provenance report

## Question

Can the Article 3 multiscale pipeline start from traceable repositories and an explicitly approved Pilot 2026 model-ready run without integrating data or advancing to G1?

## Verdict

**FAIL**. Goal 0 scaffolding and portable provenance were generated; no source data were copied and no scientific model was calibrated.

## Visual evidence

No figure was generated for G0. Source state and candidate evidence are tabulated in `tables/preflight_checks.csv` and `tables/model_run_candidates.csv`.

## Decisions required

- Approve one exact Pilot 2026 model-dataset run ID; do not approve `latest`.

## Source repositories

| Source | Required ref | Required SHA | Checkout branch | Dirty | Ahead/behind |
|---|---|---|---|---:|---|
| pyomo-doe | `ctorrealba_fermentation` | `33b55bca93f6` | `ctorrealba_fermentation` | false | 2/0 |
| DC_dFVB_2026 | `methods-draft` | `180d9b400310` | `agent/paper3-article-bundle` | false | 0/0 |
| Tesis | `article` | `adec3a941ba8` | `article` | true | 0/0 |

## Pilot 2026 model-ready candidates

| Run ID | Adapter schema | Status | Gate | QC | Complete | Eligible | Content group |
|---|---:|---|---|---|---:|---:|---|
| `20260717T001101.548263Z_ced2c885b6` | 1 | failed | FAIL | missing | false | false | `c9c9b5834360` |
| `20260717T001228Z_ced2c8` | 1 | completed | PASS | PASS | true | true | `3750dcb1cb85` |
| `20260717T001546Z_ced2c8` | 1 | completed | PASS | PASS | true | true | `fb3cbf34d810` |
| `20260717T002514Z_ced2c8` | 1 | completed | PASS | PASS | true | true | `fb3cbf34d810` |
| `20260717T125004Z_b03413` | 2 | completed | PASS | PASS | true | true | `c60684417365` |

No candidate was selected by directory order or by a `latest` pointer.

## Tests and smoke

- Pipeline pytest: `PASS`.
- Inventory smoke: `PASS`; 4 small tables checked.
- Read-only source checks: `FAIL`.
- Model microbenchmark: `SKIPPED_BY_GATE`.

## Inputs and provenance

Configuration, bundle documents, source indices and candidate manifests/QC files are hashed individually in `provenance/input_hashes.csv`. Large dataset payloads were not recursively hashed.

## Runtime

Goal 0 preflight runtime: 10.100 seconds.

## Limitations

- 4 eligible Pilot 2026 model-ready runs were found; none was selected.
- Model microbenchmark was not executed because its explicit-run and clean-source preconditions were not met.
- Source DC_dFVB_2026 checkout is `agent/paper3-article-bundle`, while `methods-draft` is required and resolves without checkout.
- Source Tesis is dirty: references/library.bib.

## Gate

G00 is `FAIL`. Eligible next Goals: none

Stop after Goal 0. Do not integrate data or begin G1 without a new explicit Goal.

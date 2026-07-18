# Article 3 multiscale transfer pipeline

Goal-oriented Python scaffolding for the multiscale Article 3 workflow. Goal 0
only establishes source provenance, environment capture, model-ready Pilot 2026
run discovery, immutable run layout and gate reporting. It does not integrate
data, calibrate models, execute screening or run MPCC.

## Source configuration

Set the three read-only source roots before running the preflight:

```powershell
$env:PYOMO_DOE_ROOT = '<local pyomo-doe checkout>'
$env:DC_DFVB_ROOT = '<local DC_dFVB_2026 checkout>'
$env:THESIS_ROOT = '<local Tesis checkout>'
```

The generated provenance stores the portable locators
`${PYOMO_DOE_ROOT}`, `${DC_DFVB_ROOT}` and `${THESIS_ROOT}` rather than local
absolute paths.

## Goal 0 commands

From the repository root:

```powershell
python -m pytest WORKFLOW/05_Article3_Multiscale_Transfer/tests -q
python WORKFLOW/05_Article3_Multiscale_Transfer/scripts/00_preflight.py `
  --dry-run `
  --goal-start-sha <sha-at-goal-start>
python WORKFLOW/05_Article3_Multiscale_Transfer/scripts/00_preflight.py `
  --goal-start-sha <sha-at-goal-start>
```

`--run-id` means an explicit, human-approved Pilot 2026 model-dataset run. The
preflight never interprets a `latest` pointer as approval. When `--run-id` is
omitted, every manifest is inventoried and the gate remains conditional if a
selection is required.

Useful options:

- `--config`: source/configuration JSON;
- `--output-root`: Goal run root;
- `--output-run-id`: explicit Goal 0 output run ID;
- `--run-id`: explicit source model-dataset run ID;
- `--skip-source-checks`: skip declared read-only structural checks and record
  the skip in the gate.

## Package layout

- `config/`: portable source contract, compute budget and JSON schemas;
- `src/article3_multiscale/`: provenance and preflight primitives;
- `scripts/00_preflight.py`: Goal 0 CLI;
- `tests/`: deterministic unit tests with temporary fixtures.

Generated lightweight evidence is written to
`RESULT ANALYSIS/ARTICLE3_MULTISCALE_TRANSFER/runs/<run-id>/`. Historical runs
are never overwritten.

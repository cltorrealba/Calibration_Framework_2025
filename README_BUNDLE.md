# Bundle de gobernanza agéntica — Artículo 3 multiescala

Paquete inicial para desarrollar, mediante Goals supervisados en Codex, el pipeline multiescala de selección estructural, calibración, validación y transferencia de parámetros hacia el modelo piloto.

## Repositorio editable

- `cltorrealba/Calibration_Framework_2025`
- base: `mod_paper`
- rama nueva propuesta: `article3-multiscale-transfer-pipeline`

## Fuentes de solo lectura

- `cltorrealba/pyomo-doe@ctorrealba_fermentation`
- `cltorrealba/DC_dFVB_2026@methods-draft`
- `cltorrealba/Tesis@article`

Los SHA exactos deben resolverse al iniciar el Goal 0. No debe usarse un resultado `latest` sin congelar su run-id.

## Principio operativo

Codex automatiza implementación, ejecución, pruebas, provenance y generación de evidencia. Cada Goal termina con:

- artefactos;
- pruebas;
- figuras de inspección;
- `run_manifest.json`;
- `gate_status.json`;
- reporte;
- commit local;
- detención obligatoria.

Ningún `PASS_CONDITIONAL` autoriza a Codex a resolver decisiones científicas humanas.

## Contenido

- `AGENTS.md`
- `docs/article3_multiscale/00_PROJECT_CHARTER.md`
- `docs/article3_multiscale/01_SCIENTIFIC_CONTRACT.md`
- `docs/article3_multiscale/02_DATASET_REGISTRY.md`
- `docs/article3_multiscale/03_PARAMETER_REGISTRY.md`
- `docs/article3_multiscale/04_GOAL_ROADMAP.md`
- `docs/article3_multiscale/05_GATE_SPECIFICATION.md`
- `docs/article3_multiscale/06_VISUAL_QC_STANDARD.md`
- `docs/article3_multiscale/07_COMPUTE_BUDGET.md`
- `docs/article3_multiscale/08_DECISION_LOG.md`
- `docs/article3_multiscale/09_CLAIM_EVIDENCE_MATRIX.md`
- `docs/article3_multiscale/PROMPT_01_CREATE_BRANCH_AND_COMMIT_BUNDLE.md`
- `docs/article3_multiscale/PROMPT_02_START_DEVELOPMENT_GOAL_0.md`

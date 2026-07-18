# Prompt Codex — iniciar desarrollo con Goal 0

Usa modo Goal. Ejecuta exclusivamente G0.

## GOAL

Implementar el scaffolding, preflight, provenance e inventario inicial de fuentes del pipeline multiescala. No integrar aún datos ni ejecutar screening/calibración.

## CONTEXT OBLIGATORIO

Lee:

```text
AGENTS.md
README_BUNDLE.md
docs/article3_multiscale/00_PROJECT_CHARTER.md
docs/article3_multiscale/01_SCIENTIFIC_CONTRACT.md
docs/article3_multiscale/02_DATASET_REGISTRY.md
docs/article3_multiscale/03_PARAMETER_REGISTRY.md
docs/article3_multiscale/04_GOAL_ROADMAP.md
docs/article3_multiscale/05_GATE_SPECIFICATION.md
docs/article3_multiscale/06_VISUAL_QC_STANDARD.md
docs/article3_multiscale/07_COMPUTE_BUDGET.md
docs/article3_multiscale/08_DECISION_LOG.md
docs/article3_multiscale/09_CLAIM_EVIDENCE_MATRIX.md
```

Fuentes de solo lectura:

```text
pyomo-doe@ctorrealba_fermentation
DC_dFVB_2026@methods-draft
Tesis@article
```

No asumas rutas. Descúbrelas desde el workspace o solicita variables:

```text
PYOMO_DOE_ROOT
DC_DFVB_ROOT
THESIS_ROOT
```

## PREFLIGHT GIT

En repo editable:

```bash
git status --short --branch
git rev-parse HEAD
```

Debe estar en `article3-multiscale-transfer-pipeline` y limpio. Si no, detente.

En cada fuente:

- repository identity;
- branch;
- SHA;
- dirty state;
- remote;
- no modificar.

Si una fuente está dirty, no la limpies. Registra el bloqueo y emite `PASS_CONDITIONAL` o `FAIL`.

## ALLOWED SCOPE

Crear únicamente:

```text
WORKFLOW/05_Article3_Multiscale_Transfer/
RESULT ANALYSIS/ARTICLE3_MULTISCALE_TRANSFER/
```

y actualizar documentación solo para agregar links de navegación o una entrada de decisión estrictamente necesaria.

## FORBIDDEN

- copiar/modificar raw data;
- seleccionar estructura;
- calibrar;
- Monte Carlo completo;
- editar código histórico;
- editar fuentes;
- ejecutar MPCC;
- hacer push;
- avanzar a G1.

## IMPLEMENTATION

Crear:

```text
WORKFLOW/05_Article3_Multiscale_Transfer/
├── README.md
├── pyproject.toml
├── config/
│   ├── sources.template.json
│   ├── compute_budget.json
│   └── schemas/
├── src/article3_multiscale/
│   ├── __init__.py
│   ├── provenance.py
│   ├── environment.py
│   ├── source_discovery.py
│   ├── run_layout.py
│   └── gate.py
├── scripts/
│   └── 00_preflight.py
└── tests/
    ├── test_provenance.py
    ├── test_source_discovery.py
    ├── test_run_layout.py
    └── test_gate_schema.py
```

Resultados:

```text
RESULT ANALYSIS/ARTICLE3_MULTISCALE_TRANSFER/
├── README.md
└── runs/<run-id>/
```

`00_preflight.py` debe:

1. validar repo editable;
2. resolver fuentes por env/workspace;
3. registrar SHA/branch/dirty/remotes;
4. localizar candidatos de model-ready runs Pilot 2026 sin elegir silenciosamente `latest`;
5. verificar archivos obligatorios del bundle;
6. registrar Python/SO/CPU/RAM/paquetes;
7. calcular hashes de configs e índices, sin hashear recursivamente datasets grandes todavía;
8. ejecutar tests estructurales seguros de fuentes cuando existan;
9. producir manifest y gate;
10. soportar `--dry-run`, `--run-id`, `--config`, `--output-root`.

Si existe exactamente un run model-ready completo y PASS, puede recomendarlo; aun así debe registrarlo como decisión pendiente de aprobación. Si hay varios, listarlos y emitir `PASS_CONDITIONAL`.

No ejecutar calibración para elegir run-id.

## MICROBENCHMARK

Solo si:

- las fuentes están limpias;
- el run-id está explícitamente indicado por config/CLI;
- las dependencias están disponibles.

Entonces medir un smoke no destructivo:

- carga de config;
- carga de una tabla pequeña;
- import del modelo;
- una simulación fixture si existe.

No medir screening ni fits completos en G0. Si no puede medirse, documentar sin fallar todo el preflight.

## OUTPUTS

Run:

```text
config/effective_config.json
provenance/source_manifest.json
provenance/environment.json
provenance/input_hashes.csv
tables/model_run_candidates.csv
tables/preflight_checks.csv
logs/commands.log
report.md
gate_status.json
run_manifest.json
```

Figura opcional de G0:

```text
figures/G0_01_source_status.png
```

con repositorio, branch, SHA abreviado, dirty y accesibilidad.

## TESTS

```bash
python -m pytest WORKFLOW/05_Article3_Multiscale_Transfer/tests -q
python WORKFLOW/05_Article3_Multiscale_Transfer/scripts/00_preflight.py --dry-run
git diff --check
```

Ejecuta el preflight real solo si el dry-run pasa.

## GATE G0

PASS:

- fuentes resueltas y limpias;
- manifests completos;
- scaffolding probado;
- run-id explícito o candidato único aprobado por config;
- sin cambios fuera del scope.

PASS_CONDITIONAL:

- múltiples run candidates;
- una fuente dirty;
- microbenchmark no disponible;
- decisión humana pendiente sin impedir scaffolding.

FAIL:

- repo editable incorrecto/dirty;
- fuente crítica inaccesible;
- SHA no resoluble;
- schema o tests fallan;
- se modificó una fuente.

## COMMIT

Si G0 produce artefactos válidos, crea un commit local:

```bash
git add WORKFLOW/05_Article3_Multiscale_Transfer   "RESULT ANALYSIS/ARTICLE3_MULTISCALE_TRANSFER"   docs/article3_multiscale
git commit -m "chore(article3): establish multiscale preflight and provenance"
```

No agregues outputs masivos. Versiona solo el run G0 liviano si sus archivos no contienen rutas privadas o datos sensibles; si las contienen, sanitiza mediante representación relativa y conserva un registro local ignorado.

No push.

## STOP RULE

Detente tras G0 y el commit. No inicies G1.

## FINAL REPORT

1. gate;
2. branch/SHA inicial/final;
3. commit;
4. fuentes resueltas;
5. run candidates;
6. tests;
7. outputs;
8. runtime;
9. decisiones requeridas;
10. confirmación de no push.

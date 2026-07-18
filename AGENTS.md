# AGENTS.md — Pipeline multiescala Artículo 3

Estas instrucciones aplican a todo `Calibration_Framework_2025`, salvo reglas más específicas que no contradigan este archivo.

## Misión

Desarrollar un pipeline reproducible para integrar:

1. laboratorio natural espejo;
2. laboratorio sintético MBDoE;
3. piloto natural 2026;

y producir una estructura cinética piloto robusta con incertidumbre, antes de cualquier promoción al reduced-dFBA/MPCC.

## Repositorios

Editable:

- `Calibration_Framework_2025`
- base `mod_paper`
- rama `article3-multiscale-transfer-pipeline`

Solo lectura:

- `pyomo-doe@ctorrealba_fermentation`
- `DC_dFVB_2026@methods-draft`
- `Tesis@article`

Resuelve y registra SHA, branch y estado dirty antes de consumirlos.

## Git

Antes y después de cada Goal:

```bash
git status --short --branch
git rev-parse HEAD
git diff --check
```

Prohibido:

- `reset --hard`;
- `clean -fd`;
- descartar cambios del usuario;
- modificar repositorios fuente;
- reescribir historia;
- hacer push sin autorización;
- mezclar Goals en un commit.

Cada Goal cerrado produce un commit local pequeño. Si el repo editable está dirty con cambios ajenos, detente.

## Datos y provenance

- Datos crudos inmutables.
- No escribir en `data/` de las fuentes.
- No depender de rutas privadas.
- No usar `latest`.
- Cada run registra commits, hashes, config, entorno, seeds, comandos, runtime, solver y outputs.
- Un resultado sin manifest no es evidencia.

## Stage-gate

Lee primero los documentos en `docs/article3_multiscale/`.

Reglas:

- un solo Goal por solicitud;
- no anticipar el siguiente;
- producir `gate_status.json`;
- estados: `PASS`, `PASS_CONDITIONAL`, `FAIL`;
- detenerse al cerrar el gate;
- no interpretar `PASS_CONDITIONAL` como autorización.

## Ubicación

Código:

```text
WORKFLOW/05_Article3_Multiscale_Transfer/
```

Resultados:

```text
RESULT ANALYSIS/ARTICLE3_MULTISCALE_TRANSFER/runs/<run-id>/
```

Run mínimo:

```text
config/
provenance/
tables/
figures/
logs/
report.md
gate_status.json
run_manifest.json
```

No sobreescribir resultados históricos.

## Contrato científico

- No concatenar datasets como equivalentes.
- Cada observación conserva escala, matriz, experimento, tiempo, unidad, operador, censura y calidad.
- Ausencia no significa cero.
- El split se hace por fermentación completa.
- Prohibido dividir puntos de un reactor entre train y test.
- El holdout externo no participa en selección.
- Toda transferencia incluye baseline `pilot-only`.
- Default: soft prior/partial pooling; hard transfer es benchmark.
- El modelo de error se congela durante comparación de estructuras.
- El módulo aromático es separado.
- No modificar ni ejecutar MPCC desde este repo.

## Monte Carlo–FIM

No llamar “identificabilidad estructural” a la FIM.

Usar:

- Sobol/LHS;
- log-espacio;
- bounds físicos;
- sensibilidades directas cuando sea viable;
- SVD de la matriz de sensibilidades ponderadas;
- percentiles y frecuencia de rango;
- weak-direction persistence;
- successive halving.

Los eigenvalores se reportan como cuadrados de singular values. No seleccionar solo por el peor punto.

## Calidad de código

- Config fuera del código.
- Seeds determinísticos.
- Python tipado cuando aporte.
- Pruebas unitarias e integración.
- Fallos de simulación explícitos.
- No importar funciones desde notebooks.
- Checkpoints y resume.
- No truncar silenciosamente estados/parámetros.

## Figuras

Cada figura:

- título;
- ejes/unidades;
- leyenda;
- run-id;
- tabla CSV subyacente;
- PNG y preferentemente SVG/PDF;
- exclusiones y censura explícitas.

## Cómputo

Cumplir `07_COMPUTE_BUDGET.md`.

Antes de fase costosa:

1. microbenchmark;
2. dry-run;
3. proyección CPU/wall;
4. comparación con presupuesto;
5. stop si excede sin override.

```bash
OMP_NUM_THREADS=1
MKL_NUM_THREADS=1
OPENBLAS_NUM_THREADS=1
```

## Reporte de Goal

Incluir:

1. Goal;
2. SHA inicial/final;
3. archivos;
4. comandos;
5. tests;
6. inputs;
7. métricas;
8. figuras;
9. runtime real/proyectado;
10. limitaciones;
11. gate;
12. decisiones humanas;
13. commit local;
14. confirmación de no push.

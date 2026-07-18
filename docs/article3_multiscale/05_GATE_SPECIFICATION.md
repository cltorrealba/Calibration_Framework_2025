# Gate Specification

## Schema obligatorio

```json
{
  "gate_id": "G00",
  "goal": "",
  "status": "PASS_CONDITIONAL",
  "source_commits": {},
  "input_hashes": {},
  "commands": [],
  "tests": {},
  "metrics": {},
  "figures": [],
  "conditions": [],
  "blockers": [],
  "decisions_required": [],
  "eligible_next_goals": []
}
```

## Estados

### PASS

Artefactos y tests completos; no quedan decisiones que afecten el siguiente Goal.

### PASS_CONDITIONAL

La implementación es válida, pero requiere decisión humana o evidencia pendiente. Codex se detiene.

### FAIL

Hay bloqueo científico, de datos, provenance, cómputo o implementación. Codex conserva evidencia y se detiene.

## Gates

### G0 — Preflight

PASS si:

- repo editable limpio;
- branch/commit resueltos;
- fuentes identificadas y no modificadas;
- ambiente registrado;
- inputs candidatos enumerados;
- scaffolding y tests smoke funcionan.

PASS_CONDITIONAL si hay más de un run-id plausible o falta aprobar uno.

FAIL si hay dirty state no atribuible, SHA inaccesible o dependencia crítica ausente.

### G1 — Datos

PASS si cada experimento/variable tiene fuente, unidad, operador, tiempo y QC.

CONDICIONAL si hay datasets útiles pero metadata pendiente.

FAIL si no puede separarse proceso activo o reconciliarse una variable core.

### G2 — Splits

PASS si no hay leakage y los holdouts son fermentaciones completas.

FAIL si el split usa resultados observados o mezcla puntos del mismo reactor.

### G3 — Paridad

PASS si mapping, RHS, eventos y unidades cumplen tolerancias predeclaradas.

FAIL si una discrepancia no puede explicarse.

### G4 — Monte Carlo–SVD

PASS si el motor es determinístico, estable respecto de muestras/step y recupera fixtures.

CONDICIONAL si requiere sensibilidad por diferencias finitas con costo alto.

FAIL si singular values dependen materialmente de implementación numérica.

### G5 — Screening

PASS si shortlist se obtiene sin holdout y cada descarte tiene motivo.

FAIL si el ranking depende de error reestimado o de un único punto nominal.

### G6 — Calibración lab

PASS si existen múltiples starts convergidos, basins documentados y residuos aceptables.

CONDICIONAL si hay mínimos alternativos predictivamente equivalentes; conservar ensemble.

FAIL si predomina bound activity o residuo estructural.

### G7 — Validación lab

PASS si LOEO es consistente y estructura no colapsa entre folds.

FAIL si el ganador in-sample no predice holdout.

### G8 — Transferencia

PASS si soft/joint mejora o preserva predicción versus pilot-only y reduce incertidumbre.

CONDICIONAL si el beneficio depende de lote/variable.

FAIL si transferencia degrada sistemáticamente holdout.

### G9 — Modelo piloto

PASS si fixed/shared/specific está justificado y exportable con incertidumbre.

### G10 — Aroma

PASS si operadores temporales/terminales/intervalos y censura son válidos.

### G11 — Secuencial

PASS si parámetros/ensemble pueden propagarse, conservación es válida y se auditan active bounds.

### G12 — MPCC

Nunca ejecuta MPCC. Solo clasifica elegibilidad.

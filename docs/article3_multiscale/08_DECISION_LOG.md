# Decision Log

No borrar ni reescribir decisiones. Agregar entradas nuevas que sustituyan explícitamente una anterior.

## Template

```text
## D-YYYYMMDD-NN — Título

Status: proposed | approved | superseded | rejected
Owner:
Date:
Applies from Goal:
Decision:
Rationale:
Evidence:
Alternatives:
Consequences:
Supersedes:
Follow-up:
```

## Decisiones iniciales

### D-20260718-01 — Arquitectura multiescala

Status: approved

Integrar laboratorio natural, laboratorio sintético MBDoE y piloto natural mediante operadores específicos y modelo jerárquico; no concatenación ingenua.

### D-20260718-02 — Validación agrupada

Status: approved

Splits por fermentación/lote; no separar puntos temporales del mismo reactor.

### D-20260718-03 — Transferencia blanda

Status: approved

Soft prior/partial pooling es estrategia principal. Hard transfer se conserva como benchmark.

### D-20260718-04 — Monte Carlo–SVD

Status: approved

Evaluar información sobre ensemble log-Sobol/LHS y SVD. La FIM no se presenta como prueba de identificabilidad estructural.

### D-20260718-05 — Pipeline progresivo

Status: approved

Implementar DAG paralelo y successive halving; no orquestador monolítico ni barrido exhaustivo.

### D-20260718-06 — Holdout prospectivo

Status: proposed

Reservar experimentos MBDoE aún no incorporados, si su estado lo permite, antes de observar resultados.

### D-20260718-07 — MPCC cerrado

Status: approved

No modificar ni ejecutar MPCC hasta G12. Primero handoff y auditoría secuencial.

## Decisiones pendientes

- run-id Pilot 2026 autoritativo;
- definición final de N/YAN;
- factor Oculyze;
- datasets exactos de espejo;
- estado de F07–F09;
- thresholds numéricos de gates;
- parámetros shared/matrix/scale;
- política de inclusión aromática;
- presupuesto computacional medido.

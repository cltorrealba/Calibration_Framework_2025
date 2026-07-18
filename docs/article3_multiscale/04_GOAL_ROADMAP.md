# Goal Roadmap

Cada Goal se ejecuta por separado y termina en gate.

| Goal | Nombre | Dependencia | Resultado |
|---|---|---|---|
| G0 | Preflight y provenance | bundle | entorno, SHA, candidatos de run-id, microbenchmark o bloqueo |
| G1 | Inventario multiescala | G0 | registry, QC y figuras |
| G2 | Contrato de splits | G1 | development/validation/prospective sin leakage |
| G3 | Paridad y mapping | G1–G2 | Zenteno5, modelo actual y transformaciones probadas |
| G4 | Motor Monte Carlo–SVD | G3 | motor validado en fixtures |
| G5 | Screening progresivo | G4 | shortlist sin holdout |
| G6 | Calibración laboratorio | G5 | posterior multiconjunto |
| G7 | Validación laboratorio | G6 | LOEO y freeze prospectivo |
| G8 | Transferencia lab→piloto | G7 | pilot-only/hard/soft/joint |
| G9 | Estructura piloto final | G8 | mapa shared/specific + ensemble |
| G10 | Módulo aromático | G6+datos GC | producción/partición/captura |
| G11 | Handoff secuencial | G9, opcional G10 | impacto en bounds/LP |
| G12 | Elegibilidad MPCC | G11 | decisión final, sin ejecutar MPCC |

## Contrato de prompt Goal

```text
GOAL
CONTEXT
ALLOWED SCOPE
FORBIDDEN
IMPLEMENTATION
EXECUTION
REQUIRED ARTIFACTS
AUTOMATED TESTS
VISUAL QC
GATE
STOP RULE
FINAL REPORT
```

## G0

- Crear scaffolding.
- Resolver repositorios/SHAs.
- Inventariar model-ready runs.
- Verificar dirty state.
- Congelar entorno.
- Ejecutar tests estructurales disponibles.
- Microbenchmark solo si run-id es inequívoco.
- No integrar datos todavía.

## G1

Figuras: cobertura, missingness, timelines, temperatura, nutrición, sampling y escala×matriz.

## G2

Splits por fermentación. PCA/distancias solo con inputs de diseño. No usar outputs para escoger holdout.

## G3

Paridad RHS, mapping y eventos. Figuras overlay/error.

## G4

Sobol/LHS log-space, sensibilidad directa o fallback validado, SVD, percentiles, convergencia de muestras.

## G5

Successive halving:

- MC-0: todas, presupuesto bajo.
- MC-1: sobrevivientes.
- MC-2: finalistas.

## G6–G7

Multistart, efectos de matriz, LOEO, perfiles y posterior.

## G8

Comparar:

1. pilot-only;
2. hard transfer;
3. soft transfer;
4. joint hierarchical.

## G9

Elegir por predicción, identificabilidad, estabilidad, parsimonia y costo.

## G10

No imputar GC faltante. Operadores temporales/terminales/intervalos explícitos.

## G11

Auditar frecuencia de bounds activos y propagación de ensemble en reduced-dFBA secuencial.

## G12

Solo emitir:

- `NO_UPDATE_DC`
- `SEQUENTIAL_SANDBOX_ONLY`
- `ELIGIBLE_FOR_MPCC_RERUN`

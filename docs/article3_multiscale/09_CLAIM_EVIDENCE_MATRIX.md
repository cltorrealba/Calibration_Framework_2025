# Claim–Evidence Matrix

| Claim potencial | Evidencia mínima | Goal | Estado inicial |
|---|---|---|---|
| datasets integrados sin pérdida | registry, hashes, QC | G1 | pendiente |
| split sin leakage | folds por fermentación | G2 | pendiente |
| implementación equivalente | parity tests | G3 | pendiente |
| estructura informativa globalmente | MC–SVD estable | G4–G5 | pendiente |
| modelo laboratorio robusto | multistart + LOEO | G6–G7 | pendiente |
| laboratorio aporta a piloto | pilot-only vs soft/joint en LOLO | G8 | pendiente |
| parámetros transferibles | posterior y efectos scale/matrix | G8–G9 | pendiente |
| estructura piloto validada | LOLO + incertidumbre | G9 | pendiente |
| aromas integrados | likelihood puntual/intervalo/censura | G10 | bloqueado por datos parciales |
| parámetros afectan dFBA | active-bound audit | G11 | pendiente |
| elegible para reabrir MPCC | conservación + secuencial + handoff | G12 | pendiente |
| MPCC validado | nueva ejecución y evidencia propia | fuera del bundle | no reclamable |

## Reglas

- Ningún claim se promueve por una figura aislada.
- Tracking interno no es validación experimental.
- Fit in-sample no es validación predictiva.
- Un parámetro estimado no es transferible sin comparación de dominio.
- Un parámetro incierto puede ser irrelevante si su bound nunca es activo.
- “Robusto” exige sensibilidad a datos, parámetros, starts y configuración.

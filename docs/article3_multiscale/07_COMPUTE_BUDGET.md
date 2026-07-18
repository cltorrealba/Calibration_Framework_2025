# Compute Budget

## Principio

Evitar reemplazar el pipeline combinatorio histórico por explosión Monte Carlo.

## Presupuesto inicial configurable

```json
{
  "max_cpu_hours_per_goal": 12,
  "max_wall_hours_per_goal": 6,
  "max_workers": 8,
  "blas_threads_per_worker": 1,
  "mc0_samples": 32,
  "mc1_samples": 128,
  "mc2_samples": 512,
  "screening_max_structures": 32,
  "screening_starts": 3,
  "finalists": 3,
  "lolo_starts": 5,
  "bootstrap_replicates": 0
}
```

Estos son límites de ingeniería iniciales, no criterios científicos. G0 debe recalibrarlos mediante microbenchmark.

## Costos

Con diferencias centrales, un punto FIM cuesta aproximadamente \(2p+1\) integraciones. Para evitarlo:

1. preferir sensibilidad directa;
2. usar AD cuando sea estable;
3. fallback FD solo validado;
4. progressive sampling;
5. successive halving;
6. checkpoints.

## Tiers

| Tier | Muestras | Uso |
|---|---:|---|
| MC-0 | 16–32 | descarte |
| MC-1 | 64–128 | estabilidad |
| MC-2 | 256–512 | finalistas |
| Posterior | ensemble calibrado | incertidumbre final |

Los valores finales dependen del microbenchmark.

## Microbenchmark obligatorio

Medir:

- simulación por batch;
- evaluación residual;
- sensibilidad;
- SVD/FIM;
- fit local;
- broad start;
- punto de perfil;
- memoria por worker.

Generar `runtime_benchmark.json` con proyección por Goal.

## Reglas de corte

- Dry-run antes de fase costosa.
- Stop al exceder presupuesto sin override.
- Bootstrap apagado por default.
- No perfilar estructuras descartadas.
- No reejecutar checkpoints válidos.
- Tres fallos consecutivos: marcar estructura `FAIL`.
- No aumentar indefinidamente `max_nfev`.
- Registrar eficiencia paralela real.

## Paralelización

Paralelizar:

- estructura;
- muestra MC;
- start;
- fold;
- parámetro perfilado.

No anidar pools. BLAS monohilo:

```bash
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
```

## Monte Carlo previo y posterior

Previo: dominio físico; evalúa posibilidad de información.

Posterior: región compatible con datos; evalúa robustez final.

No mezclarlos en una sola métrica.

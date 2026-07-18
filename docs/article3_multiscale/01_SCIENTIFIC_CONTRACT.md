# Contrato científico

## Regla central

Toda magnitud debe tener definición, unidad, base, fuente, operador, productor dinámico, consumidor, IC, error y dominio. Un balance no puede tener dos productores de tasa realizada.

## Núcleo candidato

```text
X, Xd, N, G, F, E, Gly
```

| Estado | Operador candidato |
|---|---|
| X | concentración celular × viabilidad × factor biomasa |
| Xd | concentración × (1−viabilidad) × factor |
| N | PAN + NH4 en base gN/L verificada |
| G/F/E/Gly | medición química homologada |

No usar simultáneamente azúcar total y G/F sin covarianza explícita.

## Auxiliares

- Temperatura ejecutada: `Sonda1`.
- Setpoint: input comandado.
- Nutrición: eventos con tiempo/composición/masa/YAN.
- CO2: señal correlacionada; usar ESS o modelo temporal.
- Aroma puntual y condensado integrado son operadores diferentes.
- NQ/LOQ permanecen censurados.

## Observación

\[
y_{d,r,k}=h_{d,k}(x(t;\theta_d),\phi_d)+\varepsilon_{d,r,k}.
\]

Ausencia de observación no produce residuo.

## Error

Distinguir medición, discrepancia, correlación, lote/tanque, operador y censura. Congelar durante selección de estructuras.

## Splits

- Desarrollo: selección/calibración.
- Validación interna: LOEO/LOLO.
- Transferencia: laboratorio→piloto sin recalibrar y luego estrategias comparativas.
- Prospectiva: experimentos reservados antes de observar resultados.

## Transferencia

\[
\log\theta_{P,j}\sim N(\log\hat\theta_{L,j},\sigma^2_{L,j}+\tau_j^2).
\]

| Lab | Piloto | Tratamiento |
|---|---|---|
| fuerte | fuerte | shared/hierarchical |
| fuerte | débil | prior informativo |
| débil | fuerte | piloto-específico |
| débil | débil | fijar/eliminar/reformular |
| contradictorio | fuerte | efecto escala/matriz |
| contradictorio | débil | no promover |

Hard transfer es benchmark.

## Identificabilidad práctica global

Para cada muestra:

\[
J=\partial r/\partial\log\theta=U\Sigma V^T.
\]

Reportar singular values, rango, menor singular relativo, condición, weak vectors, factibilidad y percentiles 5/50/95. No usar solo peor caso.

## Clases multiescala

- `shared`
- `matrix_specific`
- `scale_specific`
- `lot_random_effect`
- `tank_nuisance`
- `observation_nuisance`
- `fixed_physical`

## Cinética–metabolismo

Antes de promoción:

- actividad de bounds;
- efecto sobre flujos realizados;
- conservación C/N;
- unidades;
- doble conteo;
- incertidumbre relevante/irrelevante.

## Aromas

Fase separada. La llegada de GC no reabre automáticamente el núcleo primario; joint polish debe justificarse.

## Lenguaje

Permitido: “identificabilidad práctica global por ensemble”, “transferencia probabilística”, “validación por lote”.

No permitido sin evidencia: “parámetros invariantes”, “identificabilidad estructural demostrada por FIM”, “DFVB-MPCC”, “validación industrial”.

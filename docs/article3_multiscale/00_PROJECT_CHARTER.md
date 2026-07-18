# Project Charter

## Pregunta científica

¿Cómo integrar información complementaria de laboratorio y piloto, con matrices y operadores heterogéneos, para seleccionar una estructura cinética robusta, cuantificar transferencia de estructura/identificabilidad/parámetros y obtener una parametrización piloto con incertidumbre?

## Datasets

### Laboratorio natural espejo

- 6 fermentaciones.
- A: 4 réplicas.
- B y C: 1 réplica cada una.
- Mosto natural.
- Aroma en vino principalmente inicial/final.

### Laboratorio sintético MBDoE

- 9 planificadas; 6 disponibles actualmente.
- Una fermentación por política.
- Selección greedy desde 25 candidatos informativos.
- Condiciones no ejecutables en piloto.
- GC temporal y condensado final aún parcial/pendiente.

### Piloto natural 2026

- 9 fermentaciones.
- 3 lotes.
- Perfiles dinámicos A/B/C.
- Estados de proceso detallados.
- Aroma temporal y fracciones capturadas.

## Hipótesis

1. El MBDoE sintético informa direcciones débiles bajo operación piloto.
2. Los experimentos espejo permiten estudiar efecto de escala.
3. Partial pooling reduce incertidumbre piloto sin degradar predicción.
4. El patrón fixed/free del Artículo 1 es benchmark, no verdad.
5. La relevancia para dFBA depende de actividad de bounds.

## Objetivos

1. Contrato de datos multiescala.
2. Pipeline paralelo con eliminación progresiva.
3. Identificabilidad práctica global Monte Carlo–SVD.
4. Estructura de laboratorio con efectos de matriz.
5. Comparación pilot-only/hard/soft/joint.
6. Estructura piloto final con ensemble.
7. Módulo aromático separado.
8. Handoff reproducible a `DC_dFVB_2026`.

## Definiciones

- Transferencia estructural: forma funcional/mecanismos.
- Transferencia de identificabilidad: parámetros estimables.
- Transferencia paramétrica: valores compartidos, desplazados o específicos.

## Arquitectura inicial

\[
\log\theta_{d,j}=\mu_j+a_{j,scale(d)}+b_{j,matrix(d)}+u_{j,lot(d)}.
\]

No liberar de inicio interacción escala×matriz: falta piloto–sintético.

## Validación

- LOEO laboratorio.
- LOLO piloto.
- Transferencia laboratorio→piloto antes de recalibrar.
- Holdout prospectivo con experimentos futuros cuando sea posible.
- Ningún split temporal dentro de reactor.

## Incluido

Núcleo cinético, benchmark Zenteno, efectos de escala/matriz, Monte Carlo–SVD, multistart, LOEO/LOLO, priors, aroma separado y handoff secuencial.

## Excluido inicialmente

Control óptimo, rediseño físico, cambio KKT, MPCC, KKT DFVB-α, claims industriales, imputar GC faltante y transferir valores Cabernet como invariantes.

## Decisión final del handoff

- `NO_UPDATE_DC`
- `SEQUENTIAL_SANDBOX_ONLY`
- `ELIGIBLE_FOR_MPCC_RERUN`

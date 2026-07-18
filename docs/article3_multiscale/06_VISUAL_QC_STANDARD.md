# Visual QC Standard

## Objetivo

Permitir revisión humana rápida sin sustituir tablas ni métricas.

## Formatos

Por figura:

```text
figures/<goal>_<nn>_<slug>.png
figures/<goal>_<nn>_<slug>.svg
tables/<goal>_<nn>_<slug>.csv
```

Metadata mínima:

- run-id;
- config hash;
- fuente;
- filtros;
- unidades;
- caption;
- fecha;
- código que la generó.

## Reglas

- No recortar fallos.
- Mostrar datos excluidos con símbolo distinto.
- Marcar censura.
- Misma escala al comparar modelos.
- Bandas con definición explícita.
- No usar R² sin mostrar trayectoria/residuales.
- Mostrar n por grupo.
- Figuras comparativas con orden estable.
- Generación no interactiva y reproducible.

## Figuras por Goal

### G1

1. disponibilidad experimento×variable;
2. missingness;
3. timelines;
4. temperatura;
5. nutrición;
6. sampling density;
7. escala×matriz×tratamiento;
8. aroma availability.

### G2

1. mapa train/validation;
2. PCA/UMAP o distancias en espacio de inputs;
3. similitud entre fermentaciones;
4. cobertura de tratamientos por fold.

### G3

1. overlays de fixtures;
2. error fuente↔implementación;
3. continuidad en pulsos;
4. mapping ida/vuelta.

### G4

1. distribución log10 singular mínimo;
2. rango efectivo;
3. condition number;
4. weak-direction frequency;
5. confusion heatmap;
6. factibilidad;
7. convergencia versus muestras;
8. sensibilidad al método/step.

### G5

1. ranking;
2. Pareto complejidad–información;
3. violin de singular mínimo relativo;
4. árbol de descarte;
5. sobrevivientes por tier.

### G6

1. observado/predicho;
2. trayectorias/bandas;
3. residuos;
4. objective contribution;
5. parámetros por start;
6. basins;
7. correlación;
8. perfiles.

### G7

1. forest de métricas LOEO;
2. holdout trajectories;
3. coverage;
4. error versus distancia de diseño;
5. estabilidad de selección.

### G8

1. shrinkage lab→pilot;
2. learning curves;
3. LOLO por estrategia;
4. reducción de incertidumbre;
5. transferencia sin recalibración;
6. efectos scale/matrix.

### G9

1. matriz fixed/shared/specific;
2. incertidumbre final;
3. weak directions;
4. finalistas;
5. criterio×modelo.

### G11

1. frecuencia de bound activity;
2. capacidades versus flujos;
3. bandas secuenciales;
4. sensibilidad outputs;
5. incertidumbre irrelevante/relevante.

## Reporte visual

`report.md` debe comenzar con:

1. pregunta;
2. veredicto;
3. cuatro a ocho figuras principales;
4. decisiones requeridas;
5. links a tablas y logs.

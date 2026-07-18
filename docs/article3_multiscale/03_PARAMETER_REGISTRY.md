# Parameter Registry

## Archivo objetivo

```text
WORKFLOW/05_Article3_Multiscale_Transfer/config/parameter_registry.csv
```

## Columnas

```text
parameter,model_layer,parameterization,meaning,unit,default,lower,upper,
transform,source_repository,source_commit,source_path,
candidate_status,sharing_class,prior_family,prior_parameters,
export_to_article3,notes
```

## Pool efectivo inicial

```text
mu0, sN, qN, qXG, qXF,
betaG0, sG, betaF0, sF,
qEG, qEF, iG, iE, Kd0, m0,
gammaG0, gammaF0
```

## Mapping efectivo/original

\[
K_{N0}=\mu_0/s_N,\quad Y_{X/N}=\mu_0/q_N
\]

\[
K_{G0}=\beta_{G0}/s_G,\quad K_{F0}=\beta_{F0}/s_F
\]

\[
Y_{X/G}=\mu_0/q_{XG},\quad Y_{X/F}=\mu_0/q_{XF}
\]

\[
Y_{E/G}=\beta_{G0}/q_{EG},\quad Y_{E/F}=\beta_{F0}/q_{EF}
\]

\[
K_{IG0}=1/i_G,\quad K_{IE0}=1/i_E.
\]

Verificar temperatura de referencia y factores térmicos.

## Capas

- `article3_core`
- `glycerol_module`
- `observation_nuisance`
- `data_nuisance`
- `fixed_physical`
- `numerical_only`

## Estados del parámetro

- `candidate`
- `estimated`
- `fixed`
- `prior_regularized`
- `removed`
- `reparameterized`

## Sharing classes

- `shared`
- `matrix_specific`
- `scale_specific`
- `lot_random_effect`
- `tank_nuisance`
- `observation_nuisance`

## Benchmarks históricos

- 1750 y 1860 se conservan como estructuras predefinidas.
- No se declaran óptimos para Sauvignon Blanc.
- Sus valores históricos solo pueden ser seeds/priors explícitos.

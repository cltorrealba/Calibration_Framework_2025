# Dataset Registry

## Archivo objetivo

```text
WORKFLOW/05_Article3_Multiscale_Transfer/config/dataset_registry.csv
```

## Columnas

```text
campaign_id,dataset_id,experiment_id,scale,matrix,lot_id,tank_id,
treatment_id,replicate_group,execution_status,data_status,
process_start,process_end,active_end,temperature_available,
nutrition_available,primary_states_available,co2_available,
wine_aroma_available,condensate_available,aroma_sampling_mode,
raw_location,source_repository,source_commit,source_hash,
development_role,validation_role,quality_notes
```

## Inventario inicial a verificar

| Dataset | Escala | Matriz | N | Función |
|---|---|---|---:|---|
| natural_mirror_2026 | laboratorio | natural | 6 | efecto de escala/repetibilidad |
| synthetic_mbdoe_2026 | laboratorio | sintético | 9 planificadas, 6 actuales | excitación paramétrica |
| pilot_2026 | piloto | natural | 9 | dominio objetivo/LOLO |

## Roles de partición posibles

```text
development
internal_validation
transfer_validation
prospective_holdout
excluded_qc
pending
```

## Reglas QC

- Ventana cinética: proceso activo.
- Cooling/postprocess fuera del ajuste cinético.
- `Sonda1` es temperatura ejecutada.
- Eventos de nutrición explícitos.
- Unidades verificadas.
- Sin double counting de azúcar.
- CO2 correlacionado y con masks.
- Censura conservada.
- Ningún raw modificado.
- Cada fila trazable a archivo/hash.

## Figuras obligatorias del inventario

1. experimento × variable;
2. missingness;
3. timeline;
4. temperatura;
5. nutrición;
6. muestreo;
7. escala × matriz × tratamiento;
8. disponibilidad aromática.

## Decisiones pendientes

- ID exactos de las seis fermentaciones espejo.
- Estado real de F07–F09.
- Qué experimentos quedan prospectivos.
- Cobertura analítica por lote.
- Regla final de CO2 Lote 1.

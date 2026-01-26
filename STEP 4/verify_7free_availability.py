#!/usr/bin/env python3
"""
Verificar cuántas de las 108 estructuras con 7 parámetros libres
tienen datos completos para MCDM (presentes en HIPPO + ROBUST)
"""
import pandas as pd

HIPPO_PATH = r"C:/Users/ctorrealba/OneDrive - Viña Concha y Toro S.A/Documentos/Doctorado/Artículos/Artículo - Estimación/Codes/STEP 2/HIPPO_result.xlsx"
ROBUST_PATH = r"C:/Users/ctorrealba/OneDrive - Viña Concha y Toro S.A/Documentos/Doctorado/Artículos/Artículo - Estimación/Codes/STEP 3/Zenteno_Final_2023b_WS.xlsx"

PARAM_COLS = ['mu0','betaG0','betaF0','Kn0','Kg0','Kf0','Kig0','Kie0',
              'Yxn','Yxg','Yxf','Yeg','Yef']

hippo = pd.read_excel(HIPPO_PATH)
robust = pd.read_excel(ROBUST_PATH)

# Paso 1: Estructuras viables en HIPPO
mask_viable = (hippo['CCc'] == 0) & (hippo['I955'] == 0)
struct_viable = hippo.loc[mask_viable].copy()

print("=" * 80)
print("STEP 1: ESTRUCTURAS VIABLES EN HIPPO (CCc==0 & I955==0)")
print("=" * 80)
print(f"Total en HIPPO: {len(hippo):,} modelos")
print(f"Viables:       {len(struct_viable):,} modelos")
print()

# Paso 2: De las viables, cuántas tienen 7 parámetros libres
struct_viable['n_free'] = struct_viable[PARAM_COLS].apply(lambda row: (row == 0).sum(), axis=1)
struct_7free = struct_viable[struct_viable['n_free'] == 7].copy()

print("=" * 80)
print("STEP 2: ESTRUCTURAS VIABLES CON 7 PARÁMETROS LIBRES")
print("=" * 80)
print(f"Viables con n_free==7: {len(struct_7free):,} modelos")
print(f"IDs: {sorted(struct_7free['FFF'].tolist())}")
print()

# Paso 3: Merge con datos de robustez
struct_7free_renamed = struct_7free.rename(columns={'FFF':'model_id'})
robust_renamed = robust.rename(columns={'FFF':'model_id'})

merged_inner = struct_7free_renamed.merge(robust_renamed, on='model_id', how='inner')

print("=" * 80)
print("STEP 3: MERGE CON DATOS DE ROBUSTEZ (INNER JOIN)")
print("=" * 80)
print(f"Con datos de robustez:  {len(merged_inner):,} modelos")
print(f"Excluidos (sin datos):  {len(struct_7free) - len(merged_inner):,} modelos")
print()

# Paso 4: Identificar cuáles fueron excluidos
excluded = struct_7free[~struct_7free['FFF'].isin(merged_inner['model_id'])]['FFF'].tolist()
print("=" * 80)
print("STEP 4: MODELOS EXCLUIDOS (en HIPPO pero NO en ROBUST)")
print("=" * 80)
if len(excluded) > 0:
    print(f"IDs excluidos: {excluded}")
    print()
    for model_id in excluded:
        in_hippo = model_id in struct_viable['FFF'].values
        in_robust = model_id in robust_renamed['model_id'].values
        status_hippo = "✓ en HIPPO" if in_hippo else "✗ NO en HIPPO"
        status_robust = "✓ en ROBUST" if in_robust else "✗ NO en ROBUST"
        print(f"  Modelo {model_id}: {status_hippo}, {status_robust}")
else:
    print("✓ NINGUNO - Todos los 7-free tienen datos en ROBUST")

print()
print("=" * 80)
print("RESUMEN FINAL")
print("=" * 80)
print(f"Estructuras viables con 7 libres en HIPPO:      {len(struct_7free):3d}")
print(f"Estructuras con datos de robustez (para MCDM):  {len(merged_inner):3d}")
print(f"Diferencia (sin datos de robustez):             {len(struct_7free) - len(merged_inner):3d}")
print()
print(f"Tu manuscrito dice: '103 viable models with 7 parameters free'")
print(f"Esperado: {len(merged_inner)} modelos disponibles para MCDM")

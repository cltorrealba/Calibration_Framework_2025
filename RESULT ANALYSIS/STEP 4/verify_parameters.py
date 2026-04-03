#!/usr/bin/env python3
"""
Verificar número de parámetros libres en los modelos viables de STEP 4
"""
import pandas as pd
import numpy as np
import os
import sys

# Parámetros definidos
PARAM_COLS = ['mu0','betaG0','betaF0','Kn0','Kg0','Kf0','Kig0','Kie0',
              'Yxn','Yxg','Yxf','Yeg','Yef']

HIPPO_PATH = r"C:/Users/ctorrealba/OneDrive - Viña Concha y Toro S.A/Documentos/Doctorado/Artículos/Artículo - Estimación/Codes/STEP 2/HIPPO_result.xlsx"

# Cargar datos
hippo = pd.read_excel(HIPPO_PATH)

# Filtro viable
mask_viable = (hippo['CCc'] == 0) & (hippo['I955'] == 0)
struct_df = hippo.loc[mask_viable].copy()

print("=" * 80)
print("ANÁLISIS DE PARÁMETROS LIBRES EN ESTRUCTURAS VIABLES")
print("=" * 80)

print(f"\nTotal de estructuras viables: {len(struct_df)}")
print(f"Total de parámetros: {len(PARAM_COLS)}")

# Calcular número de parámetros libres (0) y fijos (1)
for param in PARAM_COLS:
    struct_df[f'{param}_is_free'] = (struct_df[param] == 0).astype(int)

struct_df['n_free'] = struct_df[[f'{p}_is_free' for p in PARAM_COLS]].sum(axis=1)
struct_df['n_fixed'] = len(PARAM_COLS) - struct_df['n_free']

print("\n" + "=" * 80)
print("DISTRIBUCIÓN DE PARÁMETROS LIBRES")
print("=" * 80)
dist = struct_df['n_free'].value_counts().sort_index()
for n_free, count in dist.items():
    pct = 100 * count / len(struct_df)
    print(f"n_free = {n_free}: {count:4d} modelos ({pct:5.1f}%)")

print(f"\nRango: {struct_df['n_free'].min()} a {struct_df['n_free'].max()}")
print(f"Media: {struct_df['n_free'].mean():.2f}")
print(f"Mediana: {struct_df['n_free'].median():.1f}")

print("\n" + "=" * 80)
print("ANÁLISIS ESPECÍFICO: ESTRUCTURAS CON 7 PARÁMETROS LIBRES")
print("=" * 80)

# Filtrar estructuras con exactamente 7 parámetros libres
seven_free = struct_df[struct_df['n_free'] == 7].copy()
print(f"\nTotal de estructuras con 7 parámetros libres: {len(seven_free)}")

# Top-15 mencionados en el manuscrito
top15_ids = [1750, 1860, 2264, 1966, 2245, 1729, 2653, 2247, 1752, 2490, 1923, 1957, 2214, 1726]
print(f"\n" + "=" * 80)
print("ANÁLISIS DE TOP-15 MCDM WINNERS")
print("=" * 80)
print(f"\nModelos en Top-15 manuscrito: {top15_ids}")
print()

struct_df_renamed = struct_df.copy()
struct_df_renamed.index.name = 'model_id'
struct_df_renamed = struct_df_renamed.reset_index()

found_count = 0
for mid in top15_ids:
    row = struct_df_renamed[struct_df_renamed['model_id'] == mid]
    if len(row) > 0:
        n_free = int(row['n_free'].values[0])
        n_fixed = int(row['n_fixed'].values[0])
        print(f"Model {mid:4d}: {n_free} free, {n_fixed} fixed")
        found_count += 1
    else:
        print(f"Model {mid:4d}: NO ENCONTRADO en datos viables")

print(f"\n" + "=" * 80)
print(f"¿Todos los Top-15 tienen 7 parámetros libres?")
top15_df = struct_df_renamed[struct_df_renamed['model_id'].isin(top15_ids)]
if len(top15_df) > 0:
    n_free_values = top15_df['n_free'].values
    print(f"Rango en Top-15: {min(n_free_values):.0f} a {max(n_free_values):.0f}")
    
    unique_counts = pd.Series(n_free_values).value_counts().sort_index()
    if (n_free_values == 7).all():
        print("✓ SÍ: Todos tienen exactamente 7 parámetros libres")
    else:
        print("✗ NO: Hay heterogeneidad")
        for n, count in unique_counts.items():
            print(f"  {int(n)} free: {int(count)} modelos")



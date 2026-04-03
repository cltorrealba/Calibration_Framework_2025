#!/usr/bin/env python3
"""
Verificar cuántos parámetros libres (=0) tiene cada modelo Top-15
"""
import pandas as pd
import numpy as np

HIPPO_PATH = r"C:/Users/ctorrealba/OneDrive - Viña Concha y Toro S.A/Documentos/Doctorado/Artículos/Artículo - Estimación/Codes/STEP 2/HIPPO_result.xlsx"
PARAM_COLS = ['mu0','betaG0','betaF0','Kn0','Kg0','Kf0','Kig0','Kie0',
              'Yxn','Yxg','Yxf','Yeg','Yef']

# Top-15 según Análisis Step IV.py
TOP_15_IDS = [1750, 1860, 2264, 1966, 2245, 1729, 2653, 2247, 1752, 2490, 1923, 1957, 2214, 1726, 1963]

hippo = pd.read_excel(HIPPO_PATH)

# Filtro viable
mask_viable = (hippo['CCc'] == 0) & (hippo['I955'] == 0)
struct_df = hippo.loc[mask_viable].copy()

# Contar parámetros libres (=0) y fijos (=1)
struct_df['n_free'] = struct_df[PARAM_COLS].apply(lambda row: (row == 0).sum(), axis=1)
struct_df['n_fixed'] = struct_df[PARAM_COLS].apply(lambda row: (row == 1).sum(), axis=1)

print("=" * 70)
print("VERIFICACIÓN: ¿CUÁNTOS PARÁMETROS LIBRES EN TOP-15?")
print("=" * 70)
print()

# Revisar cada modelo en Top-15
for mid in TOP_15_IDS:
    if mid in struct_df['FFF'].values:
        row = struct_df[struct_df['FFF'] == mid].iloc[0]
        n_free = row['n_free']
        n_fixed = row['n_fixed']
        print(f"Modelo {mid:4d} → {n_free} FREE + {n_fixed} FIXED = {n_free + n_fixed} total")
    else:
        print(f"Modelo {mid:4d} → NO ENCONTRADO")

print()
print("=" * 70)
print("DISTRIBUCIÓN DE PARÁMETROS LIBRES EN VIABLE STRUCTURES (630 total)")
print("=" * 70)
dist = struct_df['n_free'].value_counts().sort_index()
for nf, count in dist.items():
    pct = 100 * count / len(struct_df)
    print(f"{nf} free params: {count:3d} structures ({pct:5.1f}%)")

print()
print("=" * 70)
print("ESTADÍSTICAS")
print("=" * 70)
print(f"Median n_free: {struct_df['n_free'].median():.1f}")
print(f"Mean n_free:   {struct_df['n_free'].mean():.2f}")
print(f"Min n_free:    {struct_df['n_free'].min()}")
print(f"Max n_free:    {struct_df['n_free'].max()}")

# ¿Todos los Top-15 tienen exactamente 7 libres?
top15_found = struct_df[struct_df['FFF'].isin(TOP_15_IDS)].copy()
print()
print("=" * 70)
print("CRITERIO DE VERIFICACIÓN: ¿TODOS TOP-15 TIENEN n_free == 7?")
print("=" * 70)
if len(top15_found) == 0:
    print("ERROR: No se encontraron modelos Top-15 en HIPPO")
else:
    nfree_values = top15_found['n_free'].unique()
    print(f"Valores de n_free encontrados en Top-15: {sorted(nfree_values)}")
    if len(nfree_values) == 1 and nfree_values[0] == 7:
        print("✓ CORRECTO: Todos los Top-15 tienen exactamente 7 parámetros libres")
    else:
        print(f"✗ PROBLEMA: Top-15 incluye estructuras con otros valores de n_free:")
        for nf in sorted(nfree_values):
            subset = top15_found[top15_found['n_free'] == nf]
            models_list = subset['FFF'].tolist()
            print(f"  - {nf} free: {len(subset)} models {models_list}")

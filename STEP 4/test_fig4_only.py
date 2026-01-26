#!/usr/bin/env python3
"""
Test script - only generate Figure 4
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from mpl_toolkits.mplot3d import Axes3D

# Load data
HIPPO_PATH = r"C:/Users/ctorrealba/OneDrive - Viña Concha y Toro S.A/Documentos/Doctorado/Artículos/Artículo - Estimación/Codes/STEP 2/HIPPO_result.xlsx"
ROBUST_PATH = r"C:/Users/ctorrealba/OneDrive - Viña Concha y Toro S.A/Documentos/Doctorado/Artículos/Artículo - Estimación/Codes/STEP 3/Zenteno_Final_2023b_WS.xlsx"

hippo = pd.read_excel(HIPPO_PATH)
robust = pd.read_excel(ROBUST_PATH)

mask_viable = (hippo['CCc'] == 0) & (hippo['I955'] == 0)
struct_df = hippo.loc[mask_viable].copy()
struct_df = struct_df.rename(columns={'FFF': 'model_id'})
robust = robust.rename(columns={'FFF': 'model_id'})

models = (struct_df
          .merge(robust, on='model_id', how='inner')
          .set_index('model_id'))

# Load votes and top15 info (from outputs of previous run)
consensus_df = pd.read_csv(r"C:\Users\ctorrealba\OneDrive - Viña Concha y Toro S.A\Documentos\Doctorado\Artículos\Artículo - Estimación\Codes\STEP 4\salidas\Stage4_consensus_strength.csv", index_col=0)
models['votes'] = consensus_df['votes'].reindex(models.index, fill_value=0)

top15_df = pd.read_csv(r"C:\Users\ctorrealba\OneDrive - Viña Concha y Toro S.A\Documentos\Doctorado\Artículos\Artículo - Estimación\Codes\STEP 4\salidas\Stage4_top15_selection.csv")
top15_ids = set(top15_df.iloc[:, 0].values)  # Primera columna es el modelo_id
best_id = int(models['votes'].idxmax())
voted_ids = models.loc[models['votes'] > 0].index

print(f"Top-15 count: {len(top15_ids)}")
print(f"Voted count: {len(voted_ids)}")
print(f"Best ID: {best_id}")

# Generate Figure 4
indicators = ['AICc', 'MNCI', 'RSQ2', 'GSS']
scaled = models[indicators].apply(lambda c: (c - c.min()) / (c.max() - c.min()))

fig4 = plt.figure(figsize=(8.5, 8.5), dpi=150)
ax4 = fig4.add_subplot(111, projection='3d', proj_type='persp')
from typing import Any
ax4_t: Any = ax4

# ❶  Pool completo (color-map viridis por GSS) con contorno delgado
x = np.asarray(scaled['AICc'].to_list(), dtype=float)
y = np.asarray(scaled['MNCI'].to_list(), dtype=float)
z = np.asarray(scaled['RSQ2'].to_list(), dtype=float)
colours = np.asarray(scaled['GSS'].to_list(), dtype=float)
scatter = ax4_t.scatter(x, y, z, c=colours, cmap='viridis',
                        s=50, alpha=.35, edgecolors='black', linewidth=0.4)

# ❷  Top-15 modelos — marcados con contorno azul (TODOS, incluso sin votos)
for mid in top15_ids:
    if mid not in scaled.index:
        continue
    vals = scaled.loc[mid, ['AICc', 'MNCI', 'RSQ2']].values.astype(float).ravel()
    xi, yi, zi = float(vals[0]), float(vals[1]), float(vals[2])
    is_best = mid == best_id
    is_voted = mid in voted_ids
    
    # Plotear marcador con contorno azul (visible encima del pool)
    ax4_t.scatter(xi, yi, zi,
                c='red' if is_best else 'none',      # relleno rojo solo si best
                s=200 if is_best else 140,           # tamaño aumentado para visibilidad
                marker='*' if is_best else 'o',
                edgecolor='red' if is_best else 'blue',
                linewidth=2.0 if is_best else 1.5, zorder=10)  # zorder alto para estar encima
    
    # Labels solo para modelos seleccionados por MCDM (voted) o best
    if is_voted or is_best:
        ax4.text(xi, yi, zi,
                 f" {mid}", color='red' if is_best else 'black',
                 fontsize=9, fontweight='bold', zorder=11)
    
    # Proyección a z = 0
    ax4_t.plot([xi, xi], [yi, yi], [0, zi],
             linestyle='--', linewidth=.8,
             color='red' if is_best else 'orange', alpha=.8, zorder=9)

# ❸  Modelos voted que NO están en top-15 — contorno naranja más pequeño
for mid in voted_ids:
    if mid in top15_ids:
        continue  # ya están procesados arriba
    if mid not in scaled.index:
        continue
    vals = scaled.loc[mid, ['AICc', 'MNCI', 'RSQ2']].values.astype(float).ravel()
    xi, yi, zi = float(vals[0]), float(vals[1]), float(vals[2])
    ax4_t.scatter(xi, yi, zi,
                c='none',
                s=100,
                marker='o',
                edgecolor='orange',
                linewidth=1.0, zorder=8)
    ax4.text(xi, yi, zi,
             f" {mid}", color='black',
             fontsize=9, fontweight='bold', zorder=8)
    # Proyección a z = 0
    ax4_t.plot([xi, xi], [yi, yi], [0, zi],
             linestyle='--', linewidth=.8,
             color='orange', alpha=.8, zorder=7)

# Ejes, rótulos y estilo (títulos más grandes y negrita)
ax4.set_xlabel('AICc (norm.)', labelpad=5, fontsize=11, fontweight='bold')
ax4.set_ylabel('MNCI (norm.)', labelpad=5, fontsize=11, fontweight='bold')
ax4.set_zlabel('RSQ2 (norm.)', labelpad=6, fontsize=11, fontweight='bold')

# Colorbar vertical a la derecha
cbar = fig4.colorbar(scatter, ax=ax4, label='', shrink=0.3, pad=-0.20, aspect=12, orientation='vertical', anchor=(0.0, 0.6))
cbar.ax.tick_params(labelsize=10)
cbar.set_label('GSS (norm.)', fontsize=11, fontweight='bold', labelpad=6)

ax4.view_init(elev=28, azim=38)

# Ajustar márgenes: comprimir figura para máxima compacidad
fig4.subplots_adjust(left=0.15, right=0.92, bottom=0.08, top=0.92)

OUTPUT_DIR = r"C:\Users\ctorrealba\OneDrive - Viña Concha y Toro S.A\Documentos\Doctorado\Artículos\Artículo - Estimación\Codes\STEP 4\salidas"

# Guardar en alta resolución con márgenes mínimos
fig4.savefig(os.path.join(OUTPUT_DIR, 'Fig4_robustness_landscape.png'), dpi=600, bbox_inches='tight', pad_inches=0.15)
fig4.savefig(os.path.join(OUTPUT_DIR, 'Fig4_robustness_landscape.pdf'), dpi=600, bbox_inches='tight', pad_inches=0.25)
plt.close(fig4)

print("Figure 4 generated successfully!")

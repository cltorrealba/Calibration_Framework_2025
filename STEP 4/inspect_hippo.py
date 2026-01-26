#!/usr/bin/env python3
"""
Inspeccionar la estructura del archivo HIPPO_result.xlsx
"""
import pandas as pd

HIPPO_PATH = r"C:/Users/ctorrealba/OneDrive - Viña Concha y Toro S.A/Documentos/Doctorado/Artículos/Artículo - Estimación/Codes/STEP 2/HIPPO_result.xlsx"

hippo = pd.read_excel(HIPPO_PATH)

print("=" * 80)
print("ESTRUCTURA DE HIPPO_result.xlsx")
print("=" * 80)
print(f"\nForma: {hippo.shape}")
print(f"\nColumnas: {list(hippo.columns)}")

# Ver primeras filas
print("\n" + "=" * 80)
print("PRIMERAS 10 FILAS")
print("=" * 80)
print(hippo.head(10).to_string())

# Buscar columna de ID
print("\n" + "=" * 80)
print("INFORMACIÓN DE COLUMNAS")
print("=" * 80)
for col in hippo.columns[:10]:  # Primeras 10 columnas
    print(f"{col}: dtype={hippo[col].dtype}, unique={hippo[col].nunique()}, min={hippo[col].min()}, max={hippo[col].max()}")

# Buscar donde están los modelos mencionados
print("\n" + "=" * 80)
print("BÚSQUEDA DE MODELOS 1750, 1860, 2264")
print("=" * 80)

top15_ids = [1750, 1860, 2264]
for col in hippo.columns:
    matches = [mid for mid in top15_ids if mid in hippo[col].values]
    if matches:
        print(f"Encontrados {matches} en columna: {col}")

# Revisar estructura HIPPO en STEP IV
print("\n" + "=" * 80)
print("VERIFICAR QUÉ ES 'FFF' EN STEP IV")
print("=" * 80)
if 'FFF' in hippo.columns:
    print(f"Columna FFF encontrada, primeros valores:")
    print(hippo['FFF'].head(20).values)
    print(f"\nEstadísticas FFF: min={hippo['FFF'].min()}, max={hippo['FFF'].max()}, unique={hippo['FFF'].nunique()}")
else:
    print("Columna FFF NO encontrada")
    print("Disponibles:", [c for c in hippo.columns if 'FF' in c or 'ID' in c or 'id' in c])

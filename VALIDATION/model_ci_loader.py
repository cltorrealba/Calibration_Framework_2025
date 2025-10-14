# model_ci_loader.py
"""
Carga de parámetros óptimos y flags para modelos Zenteno
Extracción de p_opt y CI basados en columnas 'th_i' de la hoja de calibración.
"""
import pandas as pd
import numpy as np

# columnas de parámetros en orden
PARAM_COLS = [
    'mu0','betaG0','betaF0','Kn0','Kg0','Kf0','Kig0',
    'Kie0','Yxn','Yxg','Yxf','Yeg','Yef'
]

# rutas a archivos
HIPPO_PATH = r'C:/Users/ctorrealba/OneDrive - Viña Concha y Toro S.A/Documentos/Doctorado/Artículos/Artículo - Estimación/Codes/STEP 2/HIPPO_result.xlsx'
LAB_PATH   = r'C:/Users/ctorrealba/OneDrive - Viña Concha y Toro S.A/Documentos/Doctorado/Artículos/Artículo - Estimación/Codes/STEP 3/Zenteno_IC_LAB_5PERC_2023b_WSComplete.xlsx'
PIL_PATH   = r'C:/Users/ctorrealba/OneDrive - Viña Concha y Toro S.A/Documentos/Doctorado/Artículos/Artículo - Estimación/Codes/VALIDATION/Zenteno_IC_PIL_5PERC_2023b.xlsx'


def load_model_params(model_id: int, scale_id: int):
    """
    flags: vector int (1=fijo,0=libre) longitud 13
    p_opt: vector float longitud 13 (valores medios de cada parámetro)
    IC_95: array float 2×13 (CI- y CI+), NaN en parámetros fijos
    """
    # 1) leo flags de HIPPO
    df_flags = pd.read_excel(HIPPO_PATH, sheet_name=0)
    df_flags.columns = df_flags.columns.str.strip()
    if 'FFF' not in df_flags.columns:
        raise KeyError(f"Columna 'FFF' no encontrada en {HIPPO_PATH}")
    row = df_flags[df_flags['FFF'] == model_id]
    if row.empty:
        raise ValueError(f"Modelo {model_id} no hallado en {HIPPO_PATH}")
    flags = row[PARAM_COLS].astype(int).iloc[0].to_numpy()

    # 2) selecciono archivo de calibración
    if scale_id == 1:
        cal_path = LAB_PATH
    elif scale_id == 2:
        cal_path = PIL_PATH
    else:
        raise ValueError("scale_id debe ser 1 (lab) o 2 (pilot)")

    # 3) leo hoja de calibración
    sheet = f"Z_{model_id}"
    df2 = pd.read_excel(cal_path, sheet_name=sheet)
    df2.columns = df2.columns.str.strip()

    # iter column\ niter
    iter_col = 'N° Iteration'
    if iter_col not in df2.columns:
        raise KeyError(f"Columna '{iter_col}' no encontrada en {cal_path}")
    s_iter = df2[iter_col].astype(str).str.upper()
    # filas de interés
    mean_row = df2.loc[s_iter == 'MEAN']
    low_row  = df2.loc[s_iter == 'CI-']
    high_row = df2.loc[s_iter == 'CI+']
    if mean_row.empty or low_row.empty or high_row.empty:
        raise KeyError("Faltan filas 'MEAN', 'CI-' o 'CI+' en la hoja de calibración")

    # 4) construyo p_opt e IC_95 completos
    p_opt = np.full(len(PARAM_COLS), np.nan)
    IC_low  = np.full(len(PARAM_COLS), np.nan)
    IC_high = np.full(len(PARAM_COLS), np.nan)
    # para cada parámetro libre, extraigo th_{i+1}
    for idx, col in enumerate(PARAM_COLS):
        if flags[idx] == 0:
            th_col = f"th_{idx+1}"
            if th_col not in df2.columns:
                raise KeyError(f"Columna '{th_col}' no encontrada en {sheet}")
            p_opt[idx]    = mean_row[th_col].iloc[0]
            IC_low[idx]   = low_row[th_col].iloc[0]
            IC_high[idx]  = high_row[th_col].iloc[0]
    IC_95 = np.vstack([IC_low, IC_high])

    return flags, p_opt, IC_95

def load_kfixed_vector():
    kfixed_0 = np.array([
        0.197199633268649,
        0.229613344074747,
        0.248791924669248,
        0.00964657420423634,
        8.55185355801220,
        7.16565013620336,
        44.1506697770253,
        42.5282844691618,
        18.1864198172539,
        1.39311914120896,
        1.64263387274557,
        0.451745756284934,
        0.436908958787961
    ])
    return kfixed_0

# Carga_datos.py — versión adaptada para piloto con debug completo
import numpy as np
import pandas as pd
from scipy.signal import medfilt

def DataLoad(scale_id: int, exper_id: int, ifplot: bool = False):
    # 0) Debug inicial
    print(f"\n>>> DataLoad(scale_id={scale_id}, exper_id={exper_id}) called")
    
    # 1) Experimental codes
    codes = pd.read_csv('Experimental_Codes.txt', sep='\t', header=None,
                        names=['lab','pilot','industrial','Ind_tk'])
    code = codes.iloc[exper_id, scale_id-1]
    print(f"  Selected code for this run: {code}\n")

    # 2) Selección de archivo cinético según escala
    if scale_id == 1:
        kin_file = 'Bioreactor 2020 - cinética fermentación.xlsx'
    elif scale_id == 2:
        kin_file = 'Bin Automatizado 2020 - cinética fermentación.xlsx'
    else:  # industrial
        kin_file = 'Cinética Industrial 2020.xlsx'
    xls_kin = pd.ExcelFile(kin_file)
    kin = pd.read_excel(xls_kin, sheet_name=code)

    # 3) Archivo operacional asociado (única hoja)
    op_file = f"{code}.xlsx"
    xls_op = pd.ExcelFile(op_file)
    op = pd.read_excel(xls_op, sheet_name=0)

    # 4) Tiempos cinéticos y operacionales
    k_time = kin['Time (min)'].values / 60.0
    if scale_id == 1:
        o_time = op['TIME'].values / 60.0
        o_temp = op['T_MOSTO'].values
    else:
        idx = op['Indice de Tiempo'].astype(float).values
        o_time = (idx * 24.0) - (idx[0] * 24.0)
        o_temp = pd.to_numeric(op['EjeMosto'], errors='coerce').values
        
        if np.isnan(o_temp).any():
            print(f"    Warning: {np.isnan(o_temp).sum()} NaN en o_temp → se interpolan")
       # usamos pandas Series para aprovechar .interpolate
        s = pd.Series(o_temp, index=o_time)
        s = (s.interpolate(method='linear')        # interpola puntos intermedios
              .ffill()                            # rellena NaN iniciales (si hay)
              .bfill())                           # rellena NaN finales (si hay)
        o_temp = s.values

    # 5) Filtrado para ventana cinética
    mask = (o_time >= k_time[0]) & (o_time <= k_time[-1])
    o_time, o_temp = o_time[mask], o_temp[mask]
    o_time = o_time - o_time[0]

    # 6) Thinning y cruce con k_time
    step = 100 if not (scale_id == 2 and exper_id == 7) else 5
    t_th = np.concatenate([o_time[::step][1:], k_time])
    temp_th = np.concatenate([o_temp[::step][1:], np.interp(k_time, o_time, o_temp)])
    order = np.argsort(t_th)
    o_time_th, o_temp_th = t_th[order], temp_th[order]
    Measure_Ind = np.searchsorted(o_time_th, k_time)

    Time_Temp_Pairs = np.vstack([o_time_th, o_temp_th]).T

    # 7) Construcción de la matriz cinética [G, F, S, YAN, D]
    G = kin['Glucosa (g/L)'].values
    F = kin['Fructosa (g/L)'].values
    S = kin['Azucar Total (g/L)'].values
    Y = kin['YAN (mg/L)'].values
    D = kin['Densidad (kg/m3)'].values
    Kinetic_Matrix = np.vstack([G, F, S, Y, D]).T

# 8) --- FDA addition point (nuevo criterio) ------------------------------
    fda = pd.read_csv('FDA_DATA.txt', sep=None, engine='python')
    fda.columns = (fda.columns.str.strip().str.replace(' ', '_').str.lower())
    
    if scale_id == 1:
        col_rho = 'rho_fda_lab'
    elif scale_id == 2:
        col_rho = 'rho_fda_cii'
    else:
        col_rho = 'rho_fda_ind'
    
    rho_target = float(fda[col_rho].iloc[exper_id - 1])
    
    # --- 8.1  localizar medición de densidad más cercana en Km ----------------
    dens_vec = Kinetic_Matrix[:, 4]                     # columna D
    i_match = int(np.argmin(np.abs(dens_vec - rho_target)))
    
    # --- 8.2  índice operacional justo DESPUÉS de ese punto -------------------
    idx_op = int(Measure_Ind[i_match])                  # malla operacional
    idx = min(idx_op + 1, len(o_time_th) - 1)           # punto posterior
    t_fda = o_time_th[idx+1]                            # instante DAP
    
    FDA_Rho_Time_Pair = np.array([rho_target, t_fda])

    # 9) Pilot-scale density (WineGrid) si corresponde
    # ... (omitido para brevedad)

    # Devolver estructura esperada
    return Kinetic_Matrix, Time_Temp_Pairs, Measure_Ind, FDA_Rho_Time_Pair, np.array([[np.nan, np.nan]])

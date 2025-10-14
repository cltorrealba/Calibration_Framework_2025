# dataload_v4.py  – Python translation faithful a DataLoad.m
import pandas as pd
import numpy as np
import datetime as dt

# ----------------- utilitarios internos -----------------------------------
def _read_codes():
    return pd.read_csv('Experimental_Codes.txt', sep=r'\s+|[\t]', engine='python')

def _vec(df, *cols):
    for c in cols:
        if c in df.columns:
            return df[c].to_numpy()
    raise KeyError(f"Ninguna de estas columnas existe: {cols}")

def _combine_datetime(df, date_col='FECHA', time_col='HORA'):
    dates = pd.to_datetime(df[date_col])
    tcol  = df[time_col]
    # caso A: ya datetime64
    if np.issubdtype(tcol.dtype, np.datetime64):
        return pd.to_datetime(tcol)
    # caso B: objetos datetime.time
    if isinstance(tcol.iloc[0], dt.time):
        deltas = tcol.apply(lambda x: pd.Timedelta(
            hours=x.hour, minutes=x.minute, seconds=x.second))
    else:  # texto "HH:MM:SS"
        deltas = pd.to_timedelta(tcol.astype(str))
    return dates + deltas

# ----------------- función principal -------------------------------------
def DataLoad(scale_id:int, exper_id:int, ifplot:bool=False):
    # 1) código de experimento
    codes = _read_codes()
    code  = codes.iloc[exper_id-1, scale_id-1].strip()

    # 2) leo tablas
    if scale_id == 1:
        kin = pd.read_excel('Bioreactor 2020 - cinética fermentación.xlsx',
                             sheet_name=code)
        op  = pd.read_excel(f'{code}.xlsx')
    else:
        kin = pd.read_excel('Bin Automatizado 2020 - cinética fermentación.xlsx',
                             sheet_name=code)
        op  = pd.read_excel(f'{code}.xlsx')
        
    # 3) extraigo tiempos h y temp
    k_time = _vec(kin, 'Time_min_', 'Time (min)') / 60.0
    o_time = pd.Series(_vec(op, 'TIME') / 60.0, index=op.index)
    o_temp = pd.Series(_vec(op, 'T_MOSTO'),   index=op.index)

    # 4) filtro por ventana cinética
    low, high = pd.to_datetime(kin['Fecha'].iloc[[0, -1]])
    dates     = _combine_datetime(op, 'FECHA', 'HORA')
    mask      = dates.between(low, high) & (~o_temp.isna())
    o_time    = o_time[mask].reset_index(drop=True)
    o_temp    = o_temp[mask].reset_index(drop=True)
    o_time   -= o_time.iloc[0]

    # 5) thinning cada 100 puntos
    o_time_th = o_time.iloc[::100].to_numpy()
    o_temp_th = o_temp.iloc[::100].to_numpy()

    # 6) concateno thinning (sin el primero) + k_time → ordeno
    merged_time = np.concatenate([o_time_th[1:], k_time])
    merged_temp = np.concatenate([o_temp_th[1:], o_temp.iloc[
        [np.argmin(abs(o_time - t)) for t in k_time]]])
    order       = np.argsort(merged_time)
    t_all       = merged_time[order]
    T_all       = merged_temp[order]

    # 7) Measure_Ind: para cada k_time, busco el índice más cercano en t_all
    Measure_Ind = np.array([int(np.argmin(np.abs(t_all - t))) for t in k_time])

    Time_Temp_Pairs = np.column_stack([t_all, T_all])

    # 8) matriz cinética [G, F, S, YAN, DD]
    G   = _vec(kin, 'Glucosa_g_L_', 'Glucosa (g/L)')
    F   = _vec(kin, 'Fructosa_g_L_', 'Fructosa (g/L)')
    S   = _vec(kin, 'AzucarTotal_g_L_', 'Azucar Total (g/L)')
    YAN = _vec(kin, 'YAN_mg_L_', 'YAN (mg/L)')
    DD  = _vec(kin, 'Densidad_kg_m3_', 'Densidad (kg/m3)')
    Kinetic_Matrix = np.column_stack([G, F, S, YAN, DD])

    # 9) FDA (tab-sep) – limpio espacios y elijo columnas exactas
    fda = pd.read_csv('FDA_DATA.txt', sep='\t')
    fda.columns = fda.columns.str.strip()
    col_rho = {1:'rho_FDA LAB'}[scale_id]
    col_idx = {1:'t_FDA LAB idx'}[scale_id]
    rho_FDA = fda.loc[exper_id-1, col_rho]
    t_idx   = int(fda.loc[exper_id-1, col_idx])
    t_FDA   = t_all[t_idx] if 0 <= t_idx < len(t_all) else np.nan
    FDA_Rho_Time_Pair = np.array([rho_FDA, t_FDA])

    # 10) densidad no usada en lab-scale
    MIdx_Density = np.array([np.nan, np.nan])

    # plotting opcional
    if ifplot:
        import matplotlib.pyplot as plt
        plt.plot(o_time, o_temp, '.', color='lightgrey', ms=2)
        plt.plot(t_all, T_all, 'r.', ms=3)
        plt.plot(t_all[Measure_Ind], T_all[Measure_Ind], 'ko')
        plt.xlabel('Time [h]'); plt.ylabel('Temp [°C]'); plt.show()

    return (Kinetic_Matrix.astype(float),
            Time_Temp_Pairs.astype(float),
            Measure_Ind.astype(int),
            FDA_Rho_Time_Pair.astype(float),
            MIdx_Density.astype(float))

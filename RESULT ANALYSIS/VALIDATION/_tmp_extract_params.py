import pandas as pd
import numpy as np

MODELS = [1, 1750, 1860, 2264]
PARAM_COLS = [
    'mu0','betaG0','betaF0','Kn0','Kg0','Kf0','Kig0',
    'Kie0','Yxn','Yxg','Yxf','Yeg','Yef'
]
HIPPO_PATH = r"C:/Users/ctorrealba/OneDrive - Viña Concha y Toro S.A/Documentos/Doctorado/Artículos/Artículo - Estimación/Codes/STEP 2/HIPPO_result.xlsx"
PIL_PATH   = r"C:/Users/ctorrealba/OneDrive - Viña Concha y Toro S.A/Documentos/Doctorado/Artículos/Artículo - Estimación/Codes/VALIDATION/Zenteno_IC_PIL_5PERC_2023b.xlsx"

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

hippo = pd.read_excel(HIPPO_PATH, sheet_name=0)
hippo.columns = hippo.columns.str.strip()

rows = []
for model_id in MODELS:
    row = hippo[hippo['FFF'] == model_id]
    if row.empty:
        raise ValueError(f"Modelo {model_id} no hallado en HIPPO_result.xlsx")
    flags = row[PARAM_COLS].astype(int).iloc[0].to_numpy()

    # pilot calibration MEAN
    sheet = f"Z_{model_id}"
    df = pd.read_excel(PIL_PATH, sheet_name=sheet)
    df.columns = df.columns.str.strip()
    s_iter = df['N° Iteration'].astype(str).str.upper()
    mean = df.loc[s_iter == 'MEAN'].iloc[0]

    for idx, name in enumerate(PARAM_COLS):
        is_fixed = int(flags[idx] == 1)
        if is_fixed:
            value = float(kfixed_0[idx])
            source = 'kfixed_0'
        else:
            value = float(mean[f"th_{idx+1}"])
            source = 'p_opt_MEAN_PIL'
        rows.append({
            'model_id': model_id,
            'param': name,
            'fixed': is_fixed,
            'value': value,
            'source': source,
        })

out = pd.DataFrame(rows)
# print as table
print(out.to_string(index=False))

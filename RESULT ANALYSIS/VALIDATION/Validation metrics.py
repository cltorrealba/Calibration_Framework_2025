# -*- coding: utf-8 -*-
"""
MAIN VALIDATION SCRIPT  –  resilient version
Validates every “voted” model structure (Step-IV) plus the control model 1
on the four external data–sets and stores the diagnostics in
validation_metrics_Zenteno.csv.

2025-05-16 – fixes:
• skips pairs whose simulation/diagnostics fail (logs a warning)
• forces diagnostics to numeric → avoids dtype(O)→int errors
"""

from pathlib import Path
from itertools import product
import warnings

import numpy as np
import pandas as pd

from simulation_wrapper   import simulate_kfixed_model
from diagnostics_module   import run_diagnostics
from model_ci_loader      import load_kfixed_vector

# ──────────────────────────────────────────────────────────
# 0.  FILES & SMALL HELPERS (identical to previous version)
# ──────────────────────────────────────────────────────────
HIPPO_PATH  = r"C:/Users/ctorrealba/OneDrive - Viña Concha y Toro S.A/Documentos/Doctorado/Artículos/Artículo - Estimación/Codes/STEP 2/HIPPO_result.xlsx"
ROBUST_PATH = r"C:/Users/ctorrealba/OneDrive - Viña Concha y Toro S.A/Documentos/Doctorado/Artículos/Artículo - Estimación/Codes/STEP 3/Zenteno_Final_2023b_WS.xlsx"

CRIT_SENSE = dict(AICc='min', MNCI='min', RSQ2='max', GSS='max')
WEIGHT_SCENARIOS = {
    'No-priority'    : dict(AICc=.25, MNCI=.25, RSQ2=.25, GSS=.25),
    'Parsimony'      : dict(AICc=.70, MNCI=.10, RSQ2=.10, GSS=.10),
    'Goodness-of-fit': dict(AICc=.10, MNCI=.10, RSQ2=.70, GSS=.10),
    'Identifiability': dict(AICc=.10, MNCI=.70, RSQ2=.10, GSS=.10),
    'Sensitivity'    : dict(AICc=.10, MNCI=.10, RSQ2=.10, GSS=.70),
}
VAL_SETS = [(6,1), (7,1), (5,2), (6,2)]          # (exper_id, scale_id)


def _normalise(df, senses):
    out = df.copy()
    for c, s in senses.items():
        rng = df[c].max() - df[c].min()
        if rng == 0:
            out[c] = 0
        elif s == 'min':
            out[c] = (df[c].max() - df[c]) / rng
        else:
            out[c] = (df[c] - df[c].min()) / rng
    return out


def _saw(n, w):      return (n*w).sum(axis=1).rank(ascending=False)
def _topsis(n, w):
    v_plus, v_minus = (n*w).max(), (n*w).min()
    s_plus  = np.sqrt(((n*w - v_plus )**2).sum(axis=1))
    s_minus = np.sqrt(((n*w - v_minus)**2).sum(axis=1))
    return (s_minus / (s_plus+s_minus)).rank(ascending=False)


def voted_models() -> list[int]:
    """models with ≥1 vote by any MCDM method / scenario + control=1"""
    hippo  = pd.read_excel(HIPPO_PATH)
    robust = pd.read_excel(ROBUST_PATH)
    viable = hippo[(hippo["CCc"]==0)&(hippo["I955"]==0)].rename(columns={'FFF':'model_id'})
    df = viable.merge(robust.rename(columns={'FFF':'model_id'}),
                      on='model_id', how='inner').set_index('model_id')
    picks = []
    for wname, w in WEIGHT_SCENARIOS.items():
        nrm = _normalise(df[list(w)], CRIT_SENSE)
        for m, func in {'SAW':_saw,'TOPSIS':_topsis}.items():
            picks.append(func(nrm, pd.Series(w)).idxmin())
    picks.append(1)                       # control model
    return sorted(set(picks))


# MODELS = voted_models()
MODELS = [1, np.int64(1750), np.int64(1860)]
print("Model IDs to be validated →", MODELS)

# ──────────────────────────────────────────────────────────
# 1.  MAIN LOOP
# ──────────────────────────────────────────────────────────
records = []

for model_id, (exper_id, scale_id) in product(MODELS, VAL_SETS):

    print(f"\n>>> model {model_id:4d} | exper={exper_id}  scale={scale_id}")

    # 1.1  k-fixed vector ---------------------------------------------------
    try:
        kfixed_0 = load_kfixed_vector()
    except Exception as e:
        warnings.warn(f"load_kfixed_vector({model_id}) failed: {e}")
        continue

    # 1.2  simulation -------------------------------------------------------
    try:
        T, Xf, ctx = simulate_kfixed_model(model_id, scale_id,
                                           exper_id, kfixed_0)
    except Exception as e:
        warnings.warn(f"Simulation failed for model {model_id} "
                      f"(exp={exper_id}, scale={scale_id}): {e}")
        continue

    # 1.3  diagnostics ------------------------------------------------------
    try:
        df_diag = run_diagnostics(
            model_id=model_id,
            scale_id=scale_id,
            exper_id=exper_id,
            kfixed_0=kfixed_0,   # <-- your flag+guess vector
            n_runs=100,          # optional
            random_seed=42       # optional
        )
    except Exception as e:
        warnings.warn(f"Diagnostics failed for model {model_id} "
                      f"(exp={exper_id}, scale={scale_id}): {e}")
        continue

    # flatten Multi-Index columns  --> single level  (var_metric)
    df_flat = (df_diag
               .swaplevel(axis=1)
               .sort_index(axis=1))
    df_flat.columns = ['_'.join(col) for col in df_flat.columns]

    # numeric cast: any object→float   (avoids O→int64 error)
    df_num = df_flat.apply(pd.to_numeric, errors='coerce')

    # single line per (model, dataset) – use the row with max time
    line = df_num.iloc[-1].to_dict()
    line.update({'model_id': model_id,
                 'exper_id': exper_id,
                 'scale_id': scale_id})
    records.append(line)

# ──────────────────────────────────────────────────────────
# 2.  WRITE CSV  (if something succeeded)
# ──────────────────────────────────────────────────────────
if not records:
    print("\n*** No successful model-dataset combinations. "
          "See warnings above. ***")
else:
    df_out = pd.DataFrame(records)
    cols_first = ['model_id','exper_id','scale_id']
    df_out = df_out[cols_first +
                    [c for c in df_out.columns if c not in cols_first]]

    out_file = Path("validation_metrics_Zenteno.csv")
    df_out.to_csv(out_file, index=False)
    print(f"\nValidation metrics written to {out_file.resolve()}\n")
    print(df_out.head())

# ──────────────────────────────────────────────────────────
# 3. GENERAR PARAM_SHIFT_SUMMARY
# ──────────────────────────────────────────────────────────
# Compara p_opt en lab (scale_id=1) vs pilot (scale_id=2)
from model_ci_loader import load_model_params
PARAM_COLS = [
    'mu0', 'betaG0', 'betaF0', 'Kn0', 'Kg0', 'Kf0', 'Kig0',
    'Kie0', 'Yxn', 'Yxg', 'Yxf', 'Yeg', 'Yef'
]
shift_recs = []
for model_id in MODELS:
    # carga parámetros óptimos
    flags_lab, p_lab, _ = load_model_params(model_id, scale_id=1)
    flags_pil, p_pil, _ = load_model_params(model_id, scale_id=2)
    for idx, pname in enumerate(PARAM_COLS):
        # solo para parámetros libres en al menos una escala
        if np.isnan(p_lab[idx]) or np.isnan(p_pil[idx]):
            continue
        # desplazamiento relativo
        rel = abs(p_pil[idx] - p_lab[idx]) / \
            abs(p_lab[idx]) if p_lab[idx] != 0 else np.nan
        shift_recs.append({
            'model_id': model_id,
            'param':    pname,
            'p_lab':    p_lab[idx],
            'p_pil':    p_pil[idx],
            'rel_shift': rel
        })
df_shift = pd.DataFrame(shift_recs)
shift_file = Path("param_shift_summary.xlsx")
df_shift.to_excel(shift_file, index=False)
print(f"Parameter shift summary written to {shift_file.resolve()}")

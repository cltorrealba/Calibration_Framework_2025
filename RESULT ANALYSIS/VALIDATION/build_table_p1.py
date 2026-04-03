import os
import glob
import math
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SALIDAS_DIR = os.path.join(BASE_DIR, 'salidas_models')
OUT_DIR = os.path.join(SALIDAS_DIR, 'metrics')
OUT_FILE = os.path.join(OUT_DIR, 'table_P1_comparative_summary.csv')

MODELS = [1750, 1860, 2264]


def gmean(values):
    vals = [v for v in values if pd.notna(v) and v > 0]
    if not vals:
        return float('nan')
    return math.exp(sum(math.log(v) for v in vals) / len(vals))


def load_lab_metrics(model_id: int) -> pd.DataFrame:
    path = os.path.join(SALIDAS_DIR, f'M{model_id}', 'metrics', 'lab_metrics.csv')
    return pd.read_csv(path)


def load_lab_meta(model_id: int) -> pd.DataFrame:
    path = os.path.join(SALIDAS_DIR, f'M{model_id}', 'metrics', 'lab_meta.csv')
    return pd.read_csv(path)


def load_effort(model_id: int) -> pd.DataFrame:
    path = os.path.join(SALIDAS_DIR, f'M{model_id}', 'metrics', 'transfer_effort_stats.csv')
    return pd.read_csv(path)


def load_pilot_raw(model_id: int) -> pd.DataFrame:
    path = os.path.join(SALIDAS_DIR, f'M{model_id}', 'metrics', 'pilot_pilot_raw.csv')
    return pd.read_csv(path)


def load_transfer_fidelity(model_id: int) -> pd.DataFrame:
    """Load 95% coverage and normalized band width per variable/experiment for pilot."""
    path = os.path.join(SALIDAS_DIR, f'M{model_id}', 'metrics', 'transfer_fidelity.csv')
    return pd.read_csv(path)


def compute_row(model_id: int) -> dict:
    row = {
        'model': f'model {model_id}',
        'model_id': model_id,
        # placeholders for 95% pilot metrics (not available in current outputs)
        'coverage_pilot_95': None,
        'band_width_norm_pilot_95': None,
    }

    # Lab metrics: overall R2 (mean across variables/experiments) and 10-90 band stats
    lab = load_lab_metrics(model_id)
    if not lab.empty:
        row['R2_lab_overall'] = lab['r2_mean'].mean()
        if 'ecp_10_90' in lab.columns:
            row['coverage_lab_10_90'] = lab['ecp_10_90'].mean()
        if 'band_width_norm' in lab.columns:
            row['band_width_norm_lab_10_90'] = lab['band_width_norm'].mean()

    # Identifiability proxy: geometric mean of fim_cond from lab_meta
    try:
        meta = load_lab_meta(model_id)
        if 'fim_cond' in meta.columns:
            row['identifiability_proxy_gmean_condJ'] = gmean(meta['fim_cond'].tolist())
    except FileNotFoundError:
        pass

    # Effort ratio pilot/lab
    try:
        eff = load_effort(model_id)
        if 'effort_ratio_pilot_over_lab' in eff.columns and not eff.empty:
            row['effort_ratio_pilot_over_lab'] = eff['effort_ratio_pilot_over_lab'].iloc[0]
    except FileNotFoundError:
        pass

    # Pilot R2 by variable (avg over E5/E6)
    try:
        pilot = load_pilot_raw(model_id)
        if not pilot.empty and 'r2_mean' in pilot.columns:
            for var in ['Glucose', 'Fructose', 'YAN']:
                dfv = pilot[pilot['variable'] == var]
                key = f'R2_{var.lower()}_pilot'
                row[key] = dfv['r2_mean'].mean() if not dfv.empty else None
    except FileNotFoundError:
        pass

    # Pilot 95% coverage and normalized band width (avg over variables and pilot experiments)
    try:
        fid = load_transfer_fidelity(model_id)
        if not fid.empty:
            # Filter to variables of interest if column exists
            if 'variable' in fid.columns:
                fid = fid[fid['variable'].isin(['Glucose', 'Fructose', 'YAN'])]
            if 'coverage_95' in fid.columns:
                row['coverage_pilot_95'] = fid['coverage_95'].mean()
            if 'band_width_norm_95' in fid.columns:
                row['band_width_norm_pilot_95'] = fid['band_width_norm_95'].mean()
    except FileNotFoundError:
        pass

    return row


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    rows = [compute_row(m) for m in MODELS]
    df = pd.DataFrame(rows)

    # Replace missing with dash for presentation columns
    dash_cols = [
        'coverage_pilot_95', 'band_width_norm_pilot_95',
        'R2_glucose_pilot', 'R2_fructose_pilot', 'R2_yan_pilot'
    ]
    # Normalize column names matching our keys
    rename = {
        'R2_glucose_pilot': 'R2_glucose_pilot',
        'R2_fructose_pilot': 'R2_fructose_pilot',
        'R2_yan_pilot': 'R2_yan_pilot'
    }
    # ensure columns exist
    for c in dash_cols:
        if c not in df.columns:
            df[c] = None

    # Order columns as requested
    cols = [
        'model',
        'R2_lab_overall',
        'coverage_pilot_95',
        'band_width_norm_pilot_95',
        'coverage_lab_10_90',
        'band_width_norm_lab_10_90',
        'identifiability_proxy_gmean_condJ',
        'effort_ratio_pilot_over_lab',
        'R2_glucose_pilot',
        'R2_fructose_pilot',
        'R2_yan_pilot',
    ]
    # Keep model_id at end for traceability
    if 'model_id' in df.columns:
        cols.append('model_id')

    # Format: replace None/NaN -> '—'
    def fmt(x):
        if pd.isna(x):
            return '—'
        return x

    df = df.reindex(columns=cols)
    df_fmt = df.applymap(fmt)

    df_fmt.to_csv(OUT_FILE, index=False)
    print(f"✔ Table P-1 generado: {OUT_FILE}")
    print(df_fmt)


if __name__ == '__main__':
    main()

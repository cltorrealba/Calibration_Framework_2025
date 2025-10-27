import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SALIDAS_DIR = os.path.join(BASE_DIR, 'salidas_models', 'metrics')
LAB_FILE = os.path.join(SALIDAS_DIR, 'lab_metrics_consolidated.csv')
PILOT_FILE = os.path.join(SALIDAS_DIR, 'pilot_metrics_consolidated.csv')
OUT_COUNTS = os.path.join(SALIDAS_DIR, 'table_P1_footnote_counts.csv')
OUT_TEXT = os.path.join(SALIDAS_DIR, 'table_P1_footnote.txt')

VARS = ['Glucose', 'Fructose', 'YAN']
LAB_EXPERS = [6, 7]
PILOT_EXPERS = [5, 6]


def _agg_counts(df: pd.DataFrame, expers):
    # group by exper and variable, take median n_points across models (they should match)
    if df.empty:
        return {}
    g = (
        df.groupby(['exper_id', 'variable'])['n_points']
        .median()  # robust to any tiny mismatch
        .reset_index()
    )
    res = {}
    for var in VARS:
        vals = {}
        total = 0
        for e in expers:
            v = g.loc[(g['exper_id'] == e) & (g['variable'] == var), 'n_points']
            n = int(v.iloc[0]) if not v.empty else None
            vals[e] = n
            if n is not None:
                total += n
        res[var] = {**{f'E{e}': vals[e] for e in expers}, 'total': total if total > 0 else None}
    return res


def main():
    os.makedirs(SALIDAS_DIR, exist_ok=True)

    # Load consolidated
    lab = pd.read_csv(LAB_FILE)
    pilot = pd.read_csv(PILOT_FILE)

    # Keep needed cols only
    lab = lab[['exper_id', 'variable', 'n_points']].copy()
    pilot = pilot[['exper_id', 'variable', 'n_points']].copy()

    lab_counts = _agg_counts(lab, LAB_EXPERS)
    pilot_counts = _agg_counts(pilot, PILOT_EXPERS)

    # Build counts table
    rows = []
    for var in VARS:
        lab_e6 = lab_counts.get(var, {}).get('E6')
        lab_e7 = lab_counts.get(var, {}).get('E7')
        lab_total = lab_counts.get(var, {}).get('total')
        pil_e5 = pilot_counts.get(var, {}).get('E5')
        pil_e6 = pilot_counts.get(var, {}).get('E6')
        pil_total = pilot_counts.get(var, {}).get('total')
        rows.append({
            'variable': var,
            'lab_E6': lab_e6,
            'lab_E7': lab_e7,
            'lab_total': lab_total,
            'pilot_E5': pil_e5,
            'pilot_E6': pil_e6,
            'pilot_total': pil_total,
        })

    out_df = pd.DataFrame(rows)
    out_df.to_csv(OUT_COUNTS, index=False)

    # Compose footnote text, e.g. "Lab n (E6/E7): Glucose 10/14; ... Pilot n (E5/E6): Glucose 9/7; ..."
    def fmt_pair(a, b):
        a = '-' if pd.isna(a) else int(a)
        b = '-' if pd.isna(b) else int(b)
        return f"{a}/{b}"

    lab_parts = []
    pil_parts = []
    for var in VARS:
        r = out_df.loc[out_df['variable'] == var].iloc[0]
        lab_parts.append(f"{var} {fmt_pair(r['lab_E6'], r['lab_E7'])}")
        pil_parts.append(f"{var} {fmt_pair(r['pilot_E5'], r['pilot_E6'])}")

    foot = (
           "Lab n (E6/E7): " + "; ".join(lab_parts) + ". "
           + "Pilot n (E5/E6): " + "; ".join(pil_parts) + "."
    )

    with open(OUT_TEXT, 'w', encoding='utf-8') as f:
        f.write(foot)

    print(f"✔ Footnote counts: {OUT_COUNTS}")
    print(out_df.to_string(index=False))
    print(f"✔ Footnote text: {OUT_TEXT}")
    print(foot)


if __name__ == '__main__':
    main()

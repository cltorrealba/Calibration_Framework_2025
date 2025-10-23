import os
import re
import sys
from typing import List

import pandas as pd


TRANSFER_FILES: List[str] = [
    'transfer_deltas.csv',
    'transfer_fidelity.csv',
    'transfer_effort_stats.csv',
    'transfer_yan_late_summary.csv',
    'transfer_robustness_noise.csv',
    'transfer_stratified_temp.csv',
    'transfer_calibration.csv',
    'transfer_param_tests.csv',
    'transfer_go_nogo.csv',
    'pilot_lab_raw.csv',
    'pilot_pilot_raw.csv',
    'pilot_meta.csv',
]


def parse_model_id_from_dir(name: str) -> int:
    m = re.match(r"^M(\d+)$", name, re.IGNORECASE)
    if m:
        return int(m.group(1))
    raise ValueError(f"Nombre de carpeta no corresponde a M<ID>: {name}")


def merge_one_file(base_dir: str, file_name: str) -> pd.DataFrame:
    rows = []
    models_root = os.path.join(base_dir)
    for child in sorted(os.listdir(models_root)):
        child_path = os.path.join(models_root, child)
        if not os.path.isdir(child_path):
            continue
        if not child.lower().startswith('m'):
            continue
        try:
            mid = parse_model_id_from_dir(child)
        except Exception:
            continue
        metrics_dir = os.path.join(child_path, 'metrics')
        src = os.path.join(metrics_dir, file_name)
        if not os.path.exists(src):
            continue
        try:
            df = pd.read_csv(src)
            # Ensure model_id present
            if 'model_id' not in df.columns:
                df.insert(0, 'model_id', mid)
            rows.append(df)
        except Exception as e:
            print(f"[WARN] No se pudo leer {src}: {e}")
            continue
    if rows:
        merged = pd.concat(rows, ignore_index=True)
    else:
        merged = pd.DataFrame()
    return merged


def main():
    # Base folder with M<id> subfolders and a top-level metrics target
    if len(sys.argv) > 1:
        base = sys.argv[1]
    else:
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), 'salidas_models'))
    out_metrics = os.path.join(base, 'metrics')
    os.makedirs(out_metrics, exist_ok=True)
    print(f"Fusionando transfer outputs desde {base} → {out_metrics}")

    for fname in TRANSFER_FILES:
        merged = merge_one_file(base, fname)
        if not merged.empty:
            dst = os.path.join(out_metrics, fname)
            merged.to_csv(dst, index=False)
            print(f"  ✔ {fname}: {len(merged)} filas")
        else:
            print(f"  • {fname}: sin datos (se omitió)")


if __name__ == '__main__':
    main()

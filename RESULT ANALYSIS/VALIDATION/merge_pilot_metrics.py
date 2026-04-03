import os
import sys
import glob
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SALIDAS_DIR = os.path.join(BASE_DIR, 'salidas_models')
OUTPUT_DIR = os.path.join(SALIDAS_DIR, 'metrics')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'pilot_metrics_consolidated.csv')


def find_pilot_metric_files(root: str):
    pattern = os.path.join(root, 'M*', 'metrics', 'pilot_pilot_raw.csv')
    return sorted(glob.glob(pattern))


def load_and_tag(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if 'model_id' not in df.columns:
        model_folder = os.path.basename(os.path.dirname(os.path.dirname(path)))
        try:
            model_id = int(model_folder.lstrip('M'))
        except Exception:
            model_id = model_folder
        df.insert(0, 'model_id', model_id)
    return df


def main():
    files = find_pilot_metric_files(SALIDAS_DIR)
    if not files:
        print('No se encontraron pilot_pilot_raw.csv en salidas_models/**/metrics')
        sys.exit(1)

    frames = []
    for f in files:
        try:
            frames.append(load_and_tag(f))
        except Exception as e:
            print(f"[WARN] No se pudo leer {f}: {e}")

    if not frames:
        print('No se pudo cargar ningún archivo pilot_pilot_raw.csv')
        sys.exit(2)

    out = pd.concat(frames, axis=0, ignore_index=True, sort=True)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out.to_csv(OUTPUT_FILE, index=False)

    models = sorted(out['model_id'].unique().tolist()) if 'model_id' in out.columns else []
    exps = sorted(out['exper_id'].unique().tolist()) if 'exper_id' in out.columns else []
    vars_ = sorted(out['variable'].unique().tolist()) if 'variable' in out.columns else []

    print(f"✔ Consolidado: {OUTPUT_FILE}")
    print(f"  Filas: {len(out):,}")
    print(f"  Modelos: {models}")
    print(f"  Experimentos (pilot): {exps}")
    print(f"  Variables: {vars_}")


if __name__ == '__main__':
    main()

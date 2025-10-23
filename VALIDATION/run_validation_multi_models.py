import os
import numpy as np
from validation_pipeline import run_full_pipeline


def main():
    # Quiet logs
    os.environ.setdefault('PIPELINE_QUIET', '1')

    # Baseline vector and model set
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

    # Models to run: winner, near-surrogate, specialist, and baseline (id 1)
    models = [1750, 1860, 2264, 1]
    lab_expers = [6, 7]
    pilot_expers = [5, 6]

    base_out = "salidas_models"
    os.makedirs(base_out, exist_ok=True)
    for mid in models:
        out_dir = os.path.join(base_out, f"M{mid}")
        try:
            run_full_pipeline([mid], lab_expers, pilot_expers, [1, 2], kfixed_0,
                              n_runs=10, seed=42, out_dir=out_dir)
        except Exception as e:
            # Log and continue with next model
            print(f"[WARN] Modelo {mid} falló: {e}")


if __name__ == "__main__":
    main()

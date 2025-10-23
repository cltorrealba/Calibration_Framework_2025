import os
import numpy as np
from validation_pipeline import run_full_pipeline


# K fija para modelo 1 (13 parámetros fijos; sin reparametrización)
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

# Configuración (según Main_Validacion.py)
models = [1750]         # estructura representativa
lab_expers = [6, 7]     # validación laboratorio
pilot_expers = [5, 6]   # validación piloto

if __name__ == "__main__":
    # Quiet mode for cleaner logs
    os.environ.setdefault('PIPELINE_QUIET', '1')
    # Full run size
    run_full_pipeline(models, lab_expers, pilot_expers, [1, 2], kfixed_0,
                      n_runs=120, seed=42, out_dir="salidas")

import numpy as np
from validation_pipeline import run_fixation_elasticnet_success

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

if __name__ == "__main__":
    out_base = 'salidas'
    run_fixation_elasticnet_success(models=[1750,1860,2264], lab_expers=[6,7], kfixed_0=kfixed_0, seed=42, out_base=out_base)
    print("DONE")

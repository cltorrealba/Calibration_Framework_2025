import numpy as np
from validation_pipeline import run_lab_validation, run_fixation_elasticnet_success

# Initial parameter vector from __main__
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
    models = [1750, 1860, 2264]
    lab_expers = [6, 7]
    out_base = 'salidas'
    # Run a lighter lab validation pass (n_runs=30) to populate lab_metrics.csv
    run_lab_validation(models, lab_expers, kfixed_0, n_runs=30, seed=42, out_base=out_base)
    # Compute ElasticNet coefficients and AUROC
    run_fixation_elasticnet_success(models, lab_expers, kfixed_0, seed=42, out_base=out_base)
    print("DONE")

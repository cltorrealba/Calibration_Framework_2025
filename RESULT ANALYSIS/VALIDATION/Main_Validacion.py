# -*- coding: utf-8 -*-
"""
Created on Tue May 13 17:37:51 2025

@author: ctorrealba
"""
import numpy as np
from monte_carlo_module import run_monte_carlo
from monte_carlo_module import plot_simulation_ensemble
import matplotlib.pyplot as plt
from monte_carlo_module import overlay_models_experiments

# %%
# lista de modelos y experimentos que quieres superponer

# K fija que ya tenías
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

models   = [1750] # Model a utilizar es el 1750
expers   = [6, 7]
scale_id = 1

overlay_models_experiments(models, expers, scale_id, kfixed_0,
                           n_runs=100, random_seed=42)

# %%
# df_metrics = run_diagnostics(
#     model_id,
#     scale_id,
#     exper_id,
#     kfixed_0,
#     n_runs=100,
#     random_seed=42
# )
# print(df_metrics)

# plot_diagnostics(df_metrics)

# # 1) Simulación base (o tras Monte Carlo, pero con una sola trayectoria basta para diagnosticar)
# T, Xf, ctx = simulate_kfixed_model(model_id, scale_id, exper_id, kfixed_0)

# # 2) Comparar diagnósticos con distintas transformaciones
# df_cmp = compare_transforms(T, Xf, ctx, transforms=['none','log','boxcox'])
# print(df_cmp)

# # 3) Visualizar
# plot_metrics_by_transform(df_cmp)

# %%

# K fija que ya tenías
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

models   = [1750, 1]
expers   = [5, 6]
scale_id = 2

overlay_models_experiments(models, expers, scale_id, kfixed_0,
                           n_runs=100, random_seed=42)
# %%

# df_metrics = run_diagnostics(
#     model_id,
#     scale_id,
#     exper_id,
#     kfixed_0,
#     n_runs=100,
#     random_seed=42
# )
# print(df_metrics)

# plot_diagnostics(df_metrics)

# # 1) Simulación base (o tras Monte Carlo, pero con una sola trayectoria basta para diagnosticar)
# T, Xf, ctx = simulate_kfixed_model(model_id, scale_id, exper_id, kfixed_0)

# # 2) Comparar diagnósticos con distintas transformaciones
# df_cmp = compare_transforms(T, Xf, ctx, transforms=['none','log','boxcox'])
# print(df_cmp)

# # 3) Visualizar
# plot_metrics_by_transform(df_cmp)


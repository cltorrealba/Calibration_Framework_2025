import os
from typing import List

import numpy as np
import matplotlib.pyplot as plt

from monte_carlo_module import run_monte_carlo, plot_simulation_ensemble, COLORBLIND_PALETTE
from model_ci_loader import load_kfixed_vector


# Mapeo consistente de modelo_id a color (Dark palette - profesional)
# Garantiza que cada modelo tenga el mismo color en todos los gráficos
MODEL_COLOR_MAP = {
    1750: '#1b9e77',  # Verde oscuro
    1860: '#d95f02',  # Naranja oscuro
    2264: '#7570b3',  # Púrpura oscuro
    1:    '#e7298a',  # Rojo/magenta (baseline)
}


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def save_overlay_for_experiment(models: List[int], exper_id: int, scale_id: int,
                                kfixed_0: np.ndarray, n_runs: int, seed: int,
                                out_dir: str) -> str:
    fig_ax = None
    markers = ['o', 's', '^', 'D']
    variables = ['YAN', 'Glucose', 'Fructose', 'Temperature']

    for i, model_id in enumerate(models):
        color = MODEL_COLOR_MAP.get(model_id, COLORBLIND_PALETTE[i % len(COLORBLIND_PALETTE)])
        marker = markers[i % len(markers)]
        T, X, ctx = run_monte_carlo(model_id, scale_id, exper_id, kfixed_0,
                                     n_runs=n_runs, random_seed=seed)
        fig_ax = plot_simulation_ensemble(
            T, X, ctx,
            fig_ax=fig_ax,
            label_prefix=f"M{model_id}",
            exper_id=exper_id,
            is_primary=True if i == 0 else False,
            exp_marker=marker,
            color=color,
            variables=variables,
        )

    # deduplicate legends
    fig, axes = fig_ax
    for ax in axes:
        handles, labels = ax.get_legend_handles_labels()
        seen = set()
        uniq_h, uniq_l = [], []
        for h, l in zip(handles, labels):
            if l not in seen:
                seen.add(l)
                uniq_h.append(h)
                uniq_l.append(l)
        if uniq_h:
            ax.legend(uniq_h, uniq_l, loc='best')

    fig.suptitle(f"Experimento {exper_id} – Scale {scale_id}: Modelos ganadores y baseline")
    fig.tight_layout()
    ensure_dir(out_dir)
    out_path = os.path.join(out_dir, f"ensemble_winners_E{exper_id}_S{scale_id}.pdf")
    fig.savefig(out_path, dpi=300, format='pdf')
    plt.close(fig)
    return out_path


def main():
    # Modelos ganadores por escenario + baseline
    models = [1750, 1860, 2264, 1]
    # Experimentos de validación (lab)
    exper_ids = [6, 7]
    # Generar para Lab (scale 1) y Pilot (scale 2)
    lab_scale_id = 1
    pil_scale_id = 2
    # Vector k_fixed_0 canónico
    kfixed_0 = load_kfixed_vector()
    n_runs = 10
    seed = 42
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), 'salidas_models'))
    out_dir = os.path.join(base, 'figs')

    print("Generando figuras de ensemble por experimento (modelos ganadores + baseline)...")
    # Lab (E6, E7)
    for exp_id in exper_ids:
        out_path = save_overlay_for_experiment(models, exp_id, lab_scale_id, kfixed_0,
                                               n_runs=n_runs, seed=seed, out_dir=out_dir)
        print(f"  ✔ Lab E{exp_id}: {out_path}")
    # Pilot (E5, E6)
    for exp_id in [5, 6]:
        out_path = save_overlay_for_experiment(models, exp_id, pil_scale_id, kfixed_0,
                                               n_runs=n_runs, seed=seed, out_dir=out_dir)
        print(f"  ✔ Pilot E{exp_id}: {out_path}")


if __name__ == '__main__':
    main()

# monte_carlo_module.py
"""
Module for Monte Carlo–CV simulation and visualization
"""
import numpy as np
import matplotlib.pyplot as plt
from simulation_wrapper import simulate_kfixed_model
from Simulador_kfixed import resimulate_optimal


# Paleta colorblind (Paul Tol)
COLORBLIND_PALETTE = [
    '#332288', '#88CCEE', '#44AA99', '#DDCC77',
    '#CC6677', '#AA4499', '#117733', '#999933',
    '#882255', '#661100'
]

PARAM_COLS = ['mu0','betaG0','betaF0','Kn0','Kg0','Kf0','Kig0',
              'Kie0','Yxn','Yxg','Yxf','Yeg','Yef']

def sample_params(p_opt, CI_95, flags):
    """
    Sample free parameters uniformly within 95% CI bounds.
    """
    free_idx = np.where(flags == 0)[0]
    lower, upper = CI_95
    return np.random.uniform(lower[free_idx], upper[free_idx])


def run_monte_carlo(model_id, scale_id, exper_id, kfixed_0,
                    n_runs=100, random_seed=None):
    """
    Perform Monte Carlo–CV simulations.

    Returns:
        T: time vector (h)
        X_ensemble: shape (n_runs, len(T), 5)
        ctx: context dict including 'Km','Tpair','Measure_idx','fda_pair',
             'flags','p_opt','CI_95','FDA_add_idx'
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    # 1) Base simulation to obtain T, Xf and context
    T, Xf, ctx = simulate_kfixed_model(model_id, scale_id, exper_id, kfixed_0)
    n_t = len(T)
    X_ensemble = np.zeros((n_runs, n_t, Xf.shape[1]))
    X_ensemble[0] = Xf

    # 2) Extract context elements
    flags        = ctx['flags']
    p_opt        = ctx['p_opt']
    CI_95        = ctx['CI_95']
    rho, time_dap= ctx['fda_pair']
    FDA_add_idx  = ctx['FDA_add_idx']
    Km           = ctx['Km']
    orig_time    = ctx['Tpair'][:,0]
    orig_temp    = ctx['Tpair'][:,1]

    # 3) Reconstruct initial condition x0
    x0 = np.array([
        0.2,
        Km[0,3] / 1000.0,
        Km[0,0],
        Km[0,1],
        0.0
    ])

    # 4) Monte Carlo loop: simulate on original operational grid
    for i in range(1, n_runs):
        k_free = sample_params(p_opt, CI_95, flags)
        kfixed = np.where(flags == 1, kfixed_0, np.nan)

        _, Xf_i = resimulate_optimal(
            k_free         = k_free,
            x0             = x0,
            time_dap       = time_dap,
            int_time       = orig_time,
            exp_temp       = orig_temp,
            Kinetic_Matrix = Km,
            kfixed         = kfixed,
            FDA_add_idx    = FDA_add_idx
        )

        # pad/trim if necessary
        if Xf_i.shape[0] != n_t:
            diff = n_t - Xf_i.shape[0]
            if diff > 0:
                Xf_i = np.vstack([Xf_i, np.tile(Xf_i[-1], (diff, 1))])
            else:
                Xf_i = Xf_i[:n_t]
        X_ensemble[i] = Xf_i

    return T, X_ensemble, ctx



def plot_simulation_ensemble(T, X_ensemble, ctx,
                             percentiles=(2.5, 50, 97.5),
                             fig_ax=None,
                             label_prefix='Modelo',
                             exper_id=None,
                             is_primary=True,
                             exp_marker='o',
                             color=None):
    """
    Plots:
      - Median curve (with R² in legend when experimental data exist)
      - 95% CI (no legend entry)
      - Experimental points (per exper_id)
      - Temperature profile (with R²)
    Returns (fig, axes).
    """
    # calc percentiles
    lower  = np.percentile(X_ensemble, percentiles[0], axis=0)
    median = np.percentile(X_ensemble, percentiles[1], axis=0)
    upper  = np.percentile(X_ensemble, percentiles[2], axis=0)

    labels    = ['Biomass', 'YAN', 'Glucose', 'Fructose', 'Ethanol', 'Temperature']
    t_full    = ctx['Tpair'][:, 0]
    t_samples = ctx['Tpair'][ctx['Measure_idx'], 0]
    Km        = ctx['Km']
    T_f       = ctx['Tpair'][:, 1]

    if fig_ax is None:
        fig, axes = plt.subplots(2, 3, figsize=(15, 8))
        ax_array  = axes.flatten()
    else:
        fig, ax_array = fig_ax

    for j, label in enumerate(labels):
        ax = ax_array[j]

        if label == 'Temperature':
            # experimental vs full profile
            t_s = t_samples
            T_s = ctx['Tpair'][ctx['Measure_idx'], 1]

            # R² for temperature
            y_pred = np.interp(t_s, t_full, T_f)
            y_true = T_s
            ss_res = np.sum((y_true - y_pred)**2)
            ss_tot = np.sum((y_true - y_true.mean())**2)
            r2_temp = 1 - ss_res/ss_tot

            # plot profile with R² in legend
            ax.plot(t_full, T_f,
                    color=color,
                    label=f'{label_prefix} perfil (R²={r2_temp:.2f})',
                    lw=2)
            # experimental points
            if is_primary:
                ax.plot(t_s, T_s,
                        linestyle='',
                        marker=exp_marker,
                        color=color,
                        label=f'Temp exp E{exper_id}')

        else:
            # compute R² only for variables with data
            if label == 'YAN':
                y_true = Km[:, 3] / 1000.0
            elif label == 'Glucose':
                y_true = Km[:, 0]
            elif label == 'Fructose':
                y_true = Km[:, 1]
            else:
                y_true = None

            r2_val = None
            if y_true is not None:
                y_pred = np.interp(t_samples, t_full, median[:, j])
                ss_res = np.sum((y_true - y_pred)**2)
                ss_tot = np.sum((y_true - y_true.mean())**2)
                r2_val = 1 - ss_res/ss_tot

            # plot median with or without R²
            if r2_val is not None:
                median_label = f'{label_prefix} median (R²={r2_val:.2f})'
            else:
                median_label = f'{label_prefix} median'

            ax.plot(t_full, median[:, j],
                    color=color,
                    label=median_label,
                    lw=2)
            # fill CI without legend
            ax.fill_between(t_full,
                            lower[:, j],
                            upper[:, j],
                            color=color,
                            alpha=0.3)

            # experimental points
            if is_primary and y_true is not None:
                ax.scatter(t_samples, y_true,
                           marker=exp_marker,
                           edgecolor=color,
                           facecolor='white',
                           s=50,
                           label=f'{label} exp E{exper_id}')

        ax.set_title(label)
        ax.set_xlabel('Time [h]')
        ax.set_ylabel(label)

    return fig, ax_array


def overlay_models_experiments(model_ids, exper_ids,
                               scale_id, kfixed_0,
                               n_runs=100, random_seed=42):
    """
    Superpone en un mismo lienzo todas las combinaciones de modelos y experimentos,
    usando paleta colorblind y marcadores distintos por exper_id.
    """
    markers  = ['o', 's', '^', 'D', 'v', 'P', 'X']
    fig_ax    = None
    idx_color = 0

    for i_exp, exper_id in enumerate(exper_ids):
        for model_id in model_ids:
            color = COLORBLIND_PALETTE[idx_color % len(COLORBLIND_PALETTE)]
            idx_color += 1

            T, X, ctx = run_monte_carlo(
                model_id, scale_id, exper_id,
                kfixed_0, n_runs=n_runs, random_seed=random_seed
            )

            label       = f"M{model_id}_E{exper_id}"
            is_primary  = (model_id == model_ids[0])
            exp_marker  = markers[i_exp % len(markers)]

            fig_ax = plot_simulation_ensemble(
                T, X, ctx,
                fig_ax=fig_ax,
                label_prefix=label,
                exper_id=exper_id,
                is_primary=is_primary,
                exp_marker=exp_marker,
                color=color
            )

    # reconstruir la leyenda completa sin duplicados
    fig, axes = fig_ax
    for ax in axes:
        handles, labels = ax.get_legend_handles_labels()
        seen   = set()
        unique = []
        for h, l in zip(handles, labels):
            if l not in seen:
                seen.add(l)
                unique.append((h, l))
        if unique:
            hs, ls = zip(*unique)
            ax.legend(hs, ls, loc='best')

    fig.tight_layout()
    plt.show()
    return fig, axes
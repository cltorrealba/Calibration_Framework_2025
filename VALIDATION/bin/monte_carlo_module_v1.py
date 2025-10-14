import numpy as np
import matplotlib.pyplot as plt
from simulation_wrapper import simulate_kfixed_model
from Simulador_kfixed import resimulate_optimal

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

    # 1) simulación base
    T, Xf, ctx = simulate_kfixed_model(model_id, scale_id, exper_id, kfixed_0)

    # 2) extraer __únicamente__:
    FDA_add_idx = ctx['FDA_add_idx']   # <-- ya viene correcto del wrapper
    flags       = ctx['flags']
    p_opt       = ctx['p_opt']
    CI_95       = ctx['CI_95']
    time_dap    = ctx['fda_pair'][1]
    Km          = ctx['Km']
    int_time    = ctx['Tpair'][:,0]
    exp_temp    = ctx['Tpair'][:,1]
    x0 = np.array([
        0.2,
        Km[0,3] / 1000.0,
        Km[0,0],
        Km[0,1],
        0.0
    ])

    X_ensemble = np.zeros((n_runs, len(T), Xf.shape[1]))
    X_ensemble[0] = Xf

    for i in range(1, n_runs):
        k_free = sample_params(p_opt, CI_95, flags)
        kfixed = np.where(flags==1, kfixed_0, np.nan)
        _, Xf_i = resimulate_optimal(
            k_free         = k_free,
            x0             = x0,
            time_dap       = time_dap,
            int_time       = int_time,
            exp_temp       = exp_temp,
            Kinetic_Matrix = Km,
            kfixed         = kfixed,
            FDA_add_idx    = FDA_add_idx
        )
        X_ensemble[i] = Xf_i

    return T, X_ensemble, ctx


def plot_simulation_ensemble(T, X_ensemble, ctx,
                             percentiles=(2.5, 50, 97.5)):
    """
    Plots ensemble with median, 95% CI, and experimental points.
    """
    lower  = np.percentile(X_ensemble, percentiles[0], axis=0)
    median = np.percentile(X_ensemble, percentiles[1], axis=0)
    upper  = np.percentile(X_ensemble, percentiles[2], axis=0)

    labels    = ['Biomass', 'YAN', 'Glucose', 'Fructose', 'Ethanol']
    t_samples = ctx['Tpair'][ctx['Measure_idx'], 0]
    Km        = ctx['Km']
    n_meas    = Km.shape[0]   # número de puntos medidos = len(Measure_idx)

    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    axes = axes.flatten()
    for j, label in enumerate(labels):
        ax = axes[j]
        ax.plot(T, median[:, j], label='Median', lw=2)
        ax.fill_between(T, lower[:, j], upper[:, j], alpha=0.3, label='95% CI')
        # overlay data
        if label == 'YAN':
            ax.scatter(t_samples, Km[:,3]/1000.0,
                       color='k', label='Data')
        elif label == 'Glucose':
            ax.scatter(t_samples, Km[:,0],
                       color='k', label='Data')
        elif label == 'Fructose':
            ax.scatter(t_samples, Km[:,1],
                       color='k', label='Data')
        ax.set_title(label)
        ax.set_xlabel('Time [h]')
        ax.set_ylabel(label)
        ax.legend()
    axes[-1].axis('off')
    plt.tight_layout()
    plt.show()

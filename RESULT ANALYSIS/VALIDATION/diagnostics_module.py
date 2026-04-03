import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import boxcox, anderson
from statsmodels.stats.stattools import durbin_watson
import matplotlib.pyplot as plt

PARAM_COLS = ['mu0','betaG0','betaF0','Kn0','Kg0','Kf0','Kig0',
              'Kie0','Yxn','Yxg','Yxf','Yeg','Yef']


def compute_run_diagnostics(y_obs, y_pred):
    """
    Compute adjusted R^2, Anderson-Darling statistic, and Durbin-Watson statistic
    for observed vs predicted series.
    """
    resid = y_obs - y_pred
    n = len(y_obs)
    p = 1  # one predictor
    # R^2 and adjusted R^2
    ssr = np.sum(resid**2)
    sst = np.sum((y_obs - np.mean(y_obs))**2)
    r2 = 1 - ssr/sst if sst > 0 else np.nan
    r2_adj = 1 - (1 - r2)*(n-1)/(n-p-1) if n - p - 1 > 0 else np.nan
    # Anderson-Darling on residuals (normality)
    ad_stat = anderson(resid, dist='norm').statistic
    # Durbin-Watson
    dw_stat = np.sum(np.diff(resid)**2) / np.sum(resid**2) if ssr > 0 else np.nan
    return r2_adj, ad_stat, dw_stat


def run_diagnostics(model_id, scale_id, exper_id, kfixed_0,
                    n_runs=100, random_seed=None):
    """
    Run Monte Carlo–CV simulations and compute diagnostics (R2_adj, AD, DW)
    for YAN, Glucose, and Fructose over all realizations.

    Returns a pandas.DataFrame with shape (n_runs, 9) and MultiIndex columns
    [('YAN','r2_adj'),('YAN','AD_stat'),...].
    """
    from monte_carlo_module import run_monte_carlo
    # get ensemble
    T, X_ensemble, ctx = run_monte_carlo(
        model_id=model_id,
        scale_id=scale_id,
        exper_id=exper_id,
        kfixed_0=kfixed_0,
        n_runs=n_runs,
        random_seed=random_seed
    )
    # ───── DEBUG ────────────────────────────────────────────────────────────────
    print(f"[DEBUG diagnostics] model={model_id}, scale={scale_id}, exp={exper_id}")
    print("  T:", type(T), "shape=", getattr(T, 'shape', None))
    print("  X_ensemble:", type(X_ensemble), "shape=", getattr(X_ensemble, 'shape', None))
    print("  ctx keys:", ctx.keys())
    # ctx['Measure_idx'] should be integer indices
    mi = ctx.get('Measure_idx', None)
    print("  Measure_idx:", mi, type(mi), getattr(mi, 'dtype', None))
    
    # extract measurement times and observed values
    Km = ctx['Km']
    Tpair = ctx['Tpair']
    Measure_idx = ctx['Measure_idx']
    t_samples = Tpair[Measure_idx, 0]
    # Observations: Km rows align with Measure_idx
    y_obs = {
        'YAN':     Km[:, 3] / 1000.0,
        'Glucose': Km[:, 0],
        'Fructose':Km[:, 1]
    }
    # find indices in T nearest to each t_sample
    pred_idx = [np.argmin(np.abs(T - t)) for t in t_samples]

    # prepare storage
    metrics = {var: {'r2_adj': [], 'AD_stat': [], 'DW_stat': []}
               for var in y_obs}

    # state indices mapping
    state_map = {'YAN': 1, 'Glucose': 2, 'Fructose': 3}

    # loop over simulations
    for i in range(n_runs):
        sim = X_ensemble[i]
        for var, arr_obs in y_obs.items():
            y_pred = sim[pred_idx, state_map[var]]
            r2_adj, ad_stat, dw_stat = compute_run_diagnostics(arr_obs, y_pred)
            metrics[var]['r2_adj'].append(r2_adj)
            metrics[var]['AD_stat'].append(ad_stat)
            metrics[var]['DW_stat'].append(dw_stat)

    # build DataFrame
    import pandas as pd
    data = {}
    # ───── DEBUG BEFORE CREATE DF ───────────────────────────────────────────────
    print("  metrics dict keys and sample lengths:")
    for var, mets in metrics.items():
        for met, vals in mets.items():
            print(f"    {var},{met}: len={len(vals)}, type(vals[0])={type(vals[0])}")
            data[(var, met)] = vals
    df = pd.DataFrame(data)
    df.columns = pd.MultiIndex.from_tuples(df.columns)
    return df


def plot_diagnostics(df_metrics):
    """
    df_metrics: DataFrame con MultiIndex en columnas
                nivel0 = nombre de la variable (e.g. 'Biomass','YAN',…)
                nivel1 = métricas ('r2_adj','AD_stat','DW_stat')
    """
    vars_ = df_metrics.columns.get_level_values(0).unique()
    mets  = df_metrics.columns.get_level_values(1).unique()

    # 1) Grid de histogramas
    fig, axes = plt.subplots(len(mets), len(vars_), figsize=(4*len(vars_),3*len(mets)), sharex='col')
    for i, met in enumerate(mets):
        for j, var in enumerate(vars_):
            ax = axes[i,j] if len(mets)>1 else axes[j]
            data = df_metrics[(var, met)]
            ax.hist(data, bins=20, alpha=0.7)
            if i==0: ax.set_title(var)
            if j==0: ax.set_ylabel(met)
    plt.tight_layout()
    plt.show()

    # 2) Scatter AD_stat vs DW_stat por variable
    for var in vars_:
        x = df_metrics[(var, 'AD_stat')]
        y = df_metrics[(var, 'DW_stat')]
        plt.figure(figsize=(4,4))
        plt.scatter(x, y, alpha=0.6)
        plt.xlabel('Anderson–Darling')
        plt.ylabel('Durbin–Watson')
        plt.title(f'{var}: AD vs DW')
        plt.tight_layout()
        plt.show()

    # 3) Boxplots comparativos de las métricas
    fig, axes = plt.subplots(1, len(mets), figsize=(4*len(mets),4))
    for i, met in enumerate(mets):
        # recolectamos un array (n_runs × n_vars)
        arr = [df_metrics[(var, met)] for var in vars_]
        axes[i].boxplot(arr, labels=vars_, showfliers=False)
        axes[i].set_title(met)
        axes[i].tick_params(axis='x', rotation=45)
    plt.tight_layout()
    plt.show()
    

def apply_transform(y, method='none'):
    if method == 'log':
        return np.log1p(y), None
    elif method == 'boxcox':
        y_pos = y + 1e-6
        y_bc, lam = boxcox(y_pos)
        return y_bc, lam
    else:
        return y.copy(), None

def rerun_diagnostics(T, X_sim, ctx, transform='none'):
    """
    Recalcula R2_adj, AD_stat, DW_stat para cada variable medida
    (YAN, Glucose, Fructose, Ethanol) usando las filas de Km, no los índices
    de Tpair.
    """
    # extraer tiempos y datos medidos
    idx    = ctx['Measure_idx']
    t_smpl = ctx['Tpair'][idx, 0]
    meas   = ctx['Km']        # shape (n_meas, 5)
    exp_data = {
        'YAN':      meas[:, 3] / 1000.0,
        'Glucose':  meas[:, 0],
        'Fructose': meas[:, 1],
        'Ethanol':  meas[:, 4]
    }

    records = []
    for j, var in enumerate(['YAN','Glucose','Fructose','Ethanol']):
        y_exp = exp_data[var]
        # simulación evaluada en los mismos tiempos de medida
        i_t = np.searchsorted(T, t_smpl)
        y_sim = X_sim[i_t, j+1] if var=='YAN' else X_sim[i_t, ['Glucose','Fructose','Ethanol'].index(var)+2]
        # transformación
        y_sim_t, lam = apply_transform(y_sim, method=transform)
        y_exp_t, _   = apply_transform(y_exp, method=transform)

        # ajuste lineal y métricas
        X = sm.add_constant(y_exp_t)
        res = sm.OLS(y_sim_t, X).fit()
        resid  = y_sim_t - res.fittedvalues

        records.append({
            'variable': var,
            'r2_adj':   res.rsquared_adj,
            'AD_stat':  anderson(resid).statistic,
            'DW_stat':  durbin_watson(resid),
            'transform': transform,
            'lambda':    lam
        })

    return pd.DataFrame.from_records(records)

def compare_transforms(T, X_sim, ctx, transforms=('none','log','boxcox')):
    dfs = [rerun_diagnostics(T, X_sim, ctx, transform=t) for t in transforms]
    return pd.concat(dfs, ignore_index=True)

def plot_metrics_by_transform(df_metrics):
    import matplotlib.pyplot as plt
    for metric in ['r2_adj','AD_stat','DW_stat']:
        plt.figure(figsize=(6,4))
        for method, grp in df_metrics.groupby('transform'):
            plt.hist(grp[metric], bins=20, alpha=0.5, label=method)
        plt.title(f'Distribution of {metric}')
        plt.xlabel(metric); plt.legend(title='transform')
        plt.tight_layout()
        plt.show()
"""
validation_pipeline.py

New, self-contained pipeline to compute validation and transfer indicators
using the existing simulation modules (simulation_wrapper, monte_carlo_module,
Simulador_kfixed, Carga_datos). Outputs are written to VALIDATION/salidas.

Notes:
- This pipeline does NOT depend on the previous 'Analisis Validation.py'.
- Focuses on indicators that can be computed from available data/functions.
- Some resource-heavy indicators are marked TODO and logged for future work.
"""
from __future__ import annotations

import os
import warnings
import time
import math
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import anderson

# Local imports from this VALIDATION package
from monte_carlo_module import run_monte_carlo, plot_simulation_ensemble
from monte_carlo_module import PARAM_COLS
from Simulador_kfixed import resimulate_optimal
from simulation_wrapper import simulate_kfixed_model
from scipy.stats import mannwhitneyu


# ---------------------------
# Utility and data structures
# ---------------------------

VAR_LABELS = ["Biomass", "YAN", "Glucose", "Fructose", "Ethanol"]
# Mapping from simulation index to experimental series in Km
# 0: Biomass (no measurements), 1: YAN (uses Km[:,3] mg/L -> g/L),
# 2: Glucose (Km[:,0]), 3: Fructose (Km[:,1]), 4: Ethanol (no measurements)
SIM_TO_KM_COL = {1: 3, 2: 0, 3: 1}


def ensure_dirs(base_dir: str) -> Dict[str, str]:
    figs = os.path.join(base_dir, "figs")
    metrics = os.path.join(base_dir, "metrics")
    os.makedirs(figs, exist_ok=True)
    os.makedirs(metrics, exist_ok=True)
    return {"base": base_dir, "figs": figs, "metrics": metrics}


def durbin_watson(residuals: np.ndarray) -> float:
    if residuals.size < 2:
        return np.nan
    diff = np.diff(residuals)
    num = np.sum(diff**2)
    den = np.sum(residuals**2)
    if den == 0:
        return np.nan
    return float(num / den)


def r2_and_adj_r2(y_true: np.ndarray, y_pred: np.ndarray, p: int) -> Tuple[float, float]:
    n = len(y_true)
    if n < 2 or np.allclose(y_true.var(), 0):
        return (np.nan, np.nan)
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - y_true.mean()) ** 2))
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else np.nan
    # adjusted R2
    if n - p - 1 <= 0:
        r2_adj = np.nan
    else:
        r2_adj = 1.0 - (1.0 - r2) * (n - 1) / (n - p - 1)
    return r2, r2_adj


def rmsd(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if len(y_true) == 0:
        return np.nan
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mae_percent(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    # Relative to dynamic range to avoid division by small values
    if len(y_true) == 0:
        return np.nan
    denom = max(1e-9, float(np.nanmax(y_true) - np.nanmin(y_true)))
    return float(np.mean(np.abs(y_true - y_pred)) / denom * 100.0)


def percentile95_abs_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if len(y_true) == 0:
        return np.nan
    return float(np.percentile(np.abs(y_true - y_pred), 95))


def coverage_within_bounds(y_true: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> float:
    if len(y_true) == 0:
        return np.nan
    inside = (y_true >= lower) & (y_true <= upper)
    return float(np.mean(inside.astype(float)))


def band_width_normalized(lower: np.ndarray, upper: np.ndarray, y_true: np.ndarray) -> float:
    if len(y_true) == 0:
        return np.nan
    bw = np.mean(upper - lower)
    rng = max(1e-9, float(np.nanmax(y_true) - np.nanmin(y_true)))
    return float(bw / rng)


def iqr(arr: np.ndarray) -> float:
    return float(np.percentile(arr, 75) - np.percentile(arr, 25))


def segment_indices_by_time(t_samples: np.ndarray, t_split: float) -> Tuple[np.ndarray, np.ndarray]:
    pre_idx = np.where(t_samples < t_split)[0]
    post_idx = np.where(t_samples >= t_split)[0]
    return pre_idx, post_idx


@dataclass
class VariableMetrics:
    variable: str
    n_points: int
    r2_mean: float
    r2_std: float
    r2_adj_mean: float
    r2_adj_std: float
    rmsd_median: float
    rmsd_iqr: float
    n_rmsd_median: float
    n_rmsd_iqr: float
    ad_pass_rate: float
    ad_stat_mean: float
    dw_pass_rate: float
    dw_mean: float
    rmsd_pre: float
    rmsd_post: float
    delta_rmsd: float
    yan_late_bias: float
    ecp_10_90: float
    band_width_norm: float
    rsq_cv_mean: float
    rsq_cv_std: float
    rsq_cv_perc: float
    rmsd_cv_mean: float
    rmsd_cv_std: float
    mae_percent_median: float
    p95_abs_error: float


@dataclass
class ComboMetadata:
    model_id: int
    exper_id: int
    scale_id: int
    n_runs: int
    n_free: int
    duration_h: float
    samples_per_day: float
    n_obs_total: int
    edof: float
    p_over_n: float
    fim_cond: Optional[float]
    wall_time_s: float
    pct_at_ci_limit: Optional[float]


def _extract_series(ctx: dict, X_ensemble: np.ndarray) -> Dict[int, Dict[str, np.ndarray]]:
    """
    Build per-variable series evaluated at kinetic measurement times.
    Returns dict keyed by var index j -> {'t': t_samples, 'y_true': y_true (if avail),
    'lower': p2.5, 'median': p50, 'upper': p97.5, 'runs': per-run predictions [n_runs x n_points]}
    """
    t_full = ctx['Tpair'][:, 0]
    t_samples = ctx['Tpair'][ctx['Measure_idx'], 0]
    Km = ctx['Km']

    lower = np.percentile(X_ensemble, 2.5, axis=0)
    median = np.percentile(X_ensemble, 50, axis=0)
    upper = np.percentile(X_ensemble, 97.5, axis=0)

    series = {}
    for j in range(X_ensemble.shape[2]):
        y_med = np.interp(t_samples, t_full, median[:, j])
        y_low = np.interp(t_samples, t_full, lower[:, j])
        y_up = np.interp(t_samples, t_full, upper[:, j])

        if j in SIM_TO_KM_COL:
            col = SIM_TO_KM_COL[j]
            if j == 1:  # YAN mg/L -> g/L
                y_true = Km[:, col] / 1000.0
            else:
                y_true = Km[:, col]
        else:
            y_true = np.full_like(y_med, np.nan)

        # Per-run predictions at sample times
        runs = np.zeros((X_ensemble.shape[0], len(t_samples)))
        for r in range(X_ensemble.shape[0]):
            runs[r, :] = np.interp(t_samples, t_full, X_ensemble[r, :, j])

        series[j] = {
            't': t_samples,
            'y_true': y_true,
            'lower': y_low,
            'median': y_med,
            'upper': y_up,
            'runs': runs,
        }
    return series


def _compute_variable_metrics(j: int, s: Dict[str, np.ndarray], n_free: int, t_split: float) -> VariableMetrics:
    y_true = s['y_true']
    y_med = s['median']
    y_low = s['lower']
    y_up = s['upper']
    runs = s['runs']

    valid = ~np.isnan(y_true)
    y_true_v = y_true[valid]
    y_med_v = y_med[valid]
    y_low_v = y_low[valid]
    y_up_v = y_up[valid]
    runs_v = runs[:, valid]
    t_v = s['t'][valid]

    n_points = int(np.sum(valid))

    r2_list, r2adj_list, rmsd_list, dw_list, ad_stat_list, ad_pass_list, dw_pass_list = [], [], [], [], [], [], []
    for r in range(runs_v.shape[0]):
        y_pred = runs_v[r]
        r2, r2_adj = r2_and_adj_r2(y_true_v, y_pred, n_free)
        r2_list.append(r2)
        r2adj_list.append(r2_adj)
        rmsd_list.append(rmsd(y_true_v, y_pred))
        res = y_true_v - y_pred
        # AD test at alpha=0.05
        try:
            ad_res = anderson(res, dist='norm')
            # pick closest significance level to 5%
            sl = np.asarray(getattr(ad_res, 'significance_level', [15.0, 10.0, 5.0, 2.5, 1.0]), dtype=float)
            cv = np.asarray(getattr(ad_res, 'critical_values', [np.nan]*5), dtype=float)
            ad_stat = float(getattr(ad_res, 'statistic', np.nan))
            idx = int((np.abs(sl - 5.0)).argmin()) if sl.size > 0 else 0
            crit = float(cv[idx]) if cv.size > idx else np.nan
            ad_pass = float(ad_stat < crit) if np.isfinite(crit) else np.nan
        except Exception:
            ad_stat = np.nan
            ad_pass = np.nan
        ad_stat_list.append(ad_stat)
        ad_pass_list.append(ad_pass)
        # Durbin–Watson
        dw = durbin_watson(res)
        dw_list.append(dw)
        dw_pass_list.append(float(1.0 <= dw <= 3.0))

    r2_mean = float(np.nanmean(r2_list)) if n_points > 0 else np.nan
    r2_std = float(np.nanstd(r2_list)) if n_points > 0 else np.nan
    r2_adj_mean = float(np.nanmean(r2adj_list)) if n_points > 0 else np.nan
    r2_adj_std = float(np.nanstd(r2adj_list)) if n_points > 0 else np.nan
    rmsd_arr = np.asarray(rmsd_list)
    y_rng = max(1e-9, float(np.nanmax(y_true_v) - np.nanmin(y_true_v))) if n_points > 0 else 1.0
    n_rmsd_arr = rmsd_arr / y_rng
    rmsd_median = float(np.nanmedian(rmsd_arr)) if n_points > 0 else np.nan
    rmsd_iqr_v = iqr(rmsd_arr) if n_points > 0 else np.nan
    n_rmsd_median = float(np.nanmedian(n_rmsd_arr)) if n_points > 0 else np.nan
    n_rmsd_iqr_v = iqr(n_rmsd_arr) if n_points > 0 else np.nan

    ad_pass_rate = float(np.nanmean(ad_pass_list)) if n_points > 0 else np.nan
    ad_stat_mean = float(np.nanmean(ad_stat_list)) if n_points > 0 else np.nan
    dw_pass_rate = float(np.nanmean(dw_pass_list)) if n_points > 0 else np.nan
    dw_mean = float(np.nanmean(dw_list)) if n_points > 0 else np.nan

    # pre/post DAP
    pre_idx, post_idx = segment_indices_by_time(t_v, t_split)
    if pre_idx.size > 0:
        rmsd_pre = rmsd(y_true_v[pre_idx], y_med_v[pre_idx])
    else:
        rmsd_pre = np.nan
    if post_idx.size > 0:
        rmsd_post = rmsd(y_true_v[post_idx], y_med_v[post_idx])
    else:
        rmsd_post = np.nan
    delta_rmsd = (rmsd_pre - rmsd_post) if (not math.isnan(rmsd_pre) and not math.isnan(rmsd_post)) else np.nan

    # YAN late bias (last 20% of time)
    if t_v.size > 0:
        t_thr = t_v.min() + 0.8 * (t_v.max() - t_v.min())
        late = np.where(t_v >= t_thr)[0]
        if late.size > 0:
            yan_late_bias = float(np.mean(y_true_v[late] - y_med_v[late]))
        else:
            yan_late_bias = np.nan
    else:
        yan_late_bias = np.nan

    # Coverage and band width
    ecp_10_90 = coverage_within_bounds(y_true_v, y_low_v, y_up_v) if n_points > 0 else np.nan
    bw_norm = band_width_normalized(y_low_v, y_up_v, y_true_v) if n_points > 0 else np.nan

    # Stability across runs: RSQ and RMSD variability
    rsq_cv_mean = float(np.nanmean(r2_list)) if n_points > 0 else np.nan
    rsq_cv_std = float(np.nanstd(r2_list)) if n_points > 0 else np.nan
    rsq_cv_perc = float(100.0 * rsq_cv_std / max(1e-12, abs(rsq_cv_mean))) if n_points > 0 and not math.isclose(rsq_cv_mean, 0.0) else np.nan
    rmsd_cv_mean = float(np.nanmean(rmsd_arr)) if n_points > 0 else np.nan
    rmsd_cv_std = float(np.nanstd(rmsd_arr)) if n_points > 0 else np.nan

    # Error distribution (median MAE% and p95)
    mae_pct = mae_percent(y_true_v, y_med_v) if n_points > 0 else np.nan
    p95_abs = percentile95_abs_error(y_true_v, y_med_v) if n_points > 0 else np.nan

    return VariableMetrics(
        variable=VAR_LABELS[j],
        n_points=n_points,
        r2_mean=r2_mean,
        r2_std=r2_std,
        r2_adj_mean=r2_adj_mean,
        r2_adj_std=r2_adj_std,
        rmsd_median=rmsd_median,
        rmsd_iqr=rmsd_iqr_v,
        n_rmsd_median=n_rmsd_median,
        n_rmsd_iqr=n_rmsd_iqr_v,
        ad_pass_rate=ad_pass_rate,
        ad_stat_mean=ad_stat_mean,
        dw_pass_rate=dw_pass_rate,
        dw_mean=dw_mean,
        rmsd_pre=rmsd_pre,
        rmsd_post=rmsd_post,
        delta_rmsd=delta_rmsd,
        yan_late_bias=yan_late_bias,
        ecp_10_90=ecp_10_90,
        band_width_norm=bw_norm,
        rsq_cv_mean=rsq_cv_mean,
        rsq_cv_std=rsq_cv_std,
        rsq_cv_perc=rsq_cv_perc,
        rmsd_cv_mean=rmsd_cv_mean,
        rmsd_cv_std=rmsd_cv_std,
        mae_percent_median=mae_pct,
        p95_abs_error=p95_abs,
    )


def _compute_fim_condition(ctx: dict, kfixed_0: np.ndarray) -> Optional[float]:
    """
    Approximate condition number of sensitivity Jacobian at p_opt via finite differences.
    Returns cond(J) as a proxy for identifiability (smaller is better).
    """
    try:
        flags = ctx['flags']
        p_opt = ctx['p_opt']
        Km = ctx['Km']
        Tpair = ctx['Tpair']
        int_time = Tpair[:, 0]
        exp_temp = Tpair[:, 1]
        t_samples = Tpair[ctx['Measure_idx'], 0]
        time_dap = float(ctx['fda_pair'][1])
        FDA_add_idx = int(ctx['FDA_add_idx'])

        # initial state from run_monte_carlo convention
        x0 = np.array([
            0.2,
            Km[0, 3] / 1000.0,
            Km[0, 0],
            Km[0, 1],
            0.0,
        ])

        kfixed = np.where(flags == 1, kfixed_0, np.nan)
        free_idx = np.where(flags == 0)[0]
        k_free_base = p_opt[free_idx].astype(float)

        # baseline prediction at sample times (use median approach)
        T0, X0 = resimulate_optimal(
            k_free=k_free_base,
            x0=x0,
            time_dap=time_dap,
            int_time=int_time,
            exp_temp=exp_temp,
            Kinetic_Matrix=Km,
            kfixed=kfixed,
            FDA_add_idx=FDA_add_idx,
        )

        # build y vector stacking measured variables (YAN, G, F) at sample times
        y0_list = []
        for j in [1, 2, 3]:
            yj = np.interp(t_samples, T0, X0[:, j])
            y0_list.append(yj)
        y0 = np.concatenate(y0_list)

        # finite difference Jacobian columns
        n_free = len(k_free_base)
        J = np.zeros((y0.size, n_free))
        for c in range(n_free):
            val = k_free_base[c]
            eps = 1e-6 if val == 0 else 1e-3 * abs(val)
            k_pert = k_free_base.copy()
            k_pert[c] = val + eps
            T1, X1 = resimulate_optimal(
                k_free=k_pert,
                x0=x0,
                time_dap=time_dap,
                int_time=int_time,
                exp_temp=exp_temp,
                Kinetic_Matrix=Km,
                kfixed=kfixed,
                FDA_add_idx=FDA_add_idx,
            )
            y1_list = []
            for j in [1, 2, 3]:
                yj1 = np.interp(t_samples, T1, X1[:, j])
                y1_list.append(yj1)
            y1 = np.concatenate(y1_list)
            J[:, c] = (y1 - y0) / eps

        cond = float(np.linalg.cond(J))
        return cond
    except Exception:
        return None


def _percent_at_ci_limits(ctx: dict, tol_frac: float = 0.05) -> Optional[float]:
    """Proxy for '% en límites': percent of free parameters whose p_opt lies within
    tol_frac of their 95% CI bound (edge). Uses only finite CI bounds.
    """
    try:
        flags = ctx['flags']
        p_opt = ctx['p_opt']
        CI_95 = ctx['CI_95']
        free_idx = np.where(flags == 0)[0]
        if free_idx.size == 0:
            return None
        hits = []
        for idx in free_idx:
            lo = CI_95[0, idx]
            hi = CI_95[1, idx]
            v = p_opt[idx]
            if not (np.isfinite(lo) and np.isfinite(hi)):
                continue
            width = hi - lo
            if width <= 0:
                continue
            d_edge = min(abs(v - lo), abs(hi - v))
            hits.append(float(d_edge <= tol_frac * width))
        return float(np.mean(hits)) if hits else None
    except Exception:
        return None


def _compute_global_scores(ctx: dict, series: Dict[int, Dict[str, np.ndarray]], n_free: int) -> Dict[str, float]:
    """Compute proxy AICc, MNCI (normalized CI width avg), and global R2 from median curves."""
    # Stack residuals across measured variables (YAN, G, F)
    RSS = 0.0
    SS_tot = 0.0
    n_total = 0
    for j in [1, 2, 3]:
        s = series[j]
        y_true = s['y_true']
        y_med = s['median']
        valid = ~np.isnan(y_true)
        y_true_v = y_true[valid]
        y_med_v = y_med[valid]
        if y_true_v.size == 0:
            continue
        RSS += float(np.sum((y_true_v - y_med_v) ** 2))
        SS_tot += float(np.sum((y_true_v - y_true_v.mean()) ** 2))
        n_total += int(y_true_v.size)

    # Global R2
    R2 = np.nan
    if n_total > 1 and SS_tot > 0:
        R2 = 1.0 - (RSS / SS_tot)

    # AICc proxy under Gaussian errors
    if n_total > (n_free + 1) and n_total > 0 and RSS > 0:
        k = n_free
        AIC = n_total * np.log(RSS / n_total) + 2 * k
        AICc = AIC + (2 * k * (k + 1)) / (n_total - k - 1)
    else:
        AICc = np.nan

    # MNCI proxy: normalized CI width across free parameters
    try:
        flags = ctx['flags']
        p_opt = ctx['p_opt']
        CI_95 = ctx['CI_95']
        free_idx = np.where(flags == 0)[0]
        widths = []
        for idx in free_idx:
            lo = CI_95[0, idx]
            hi = CI_95[1, idx]
            v = p_opt[idx]
            if np.isfinite(lo) and np.isfinite(hi) and np.isfinite(v) and v != 0:
                widths.append((hi - lo) / abs(v))
        MNCI = float(np.nanmean(widths)) if widths else np.nan
    except Exception:
        MNCI = np.nan

    return {"AICc": float(AICc) if not np.isnan(AICc) else np.nan,
            "MNCI": MNCI,
            "RSQ": float(R2) if not np.isnan(R2) else np.nan,
            "n_total": int(n_total),
            "RSS": float(RSS)}


def _run_monte_carlo_with_flags(model_id: int, scale_id: int, exper_id: int,
                                kfixed_0: np.ndarray, flags_override: np.ndarray,
                                n_runs: int = 50, random_seed: Optional[int] = 42) -> Tuple[np.ndarray, np.ndarray, dict]:
    """Variant of run_monte_carlo that allows overriding the flags (fix/free mask)."""
    if random_seed is not None:
        np.random.seed(random_seed)

    # Base context
    T, Xf, ctx = simulate_kfixed_model(model_id, scale_id, exper_id, kfixed_0)
    n_t = len(T)
    X_ensemble = np.zeros((n_runs, n_t, Xf.shape[1]))
    X_ensemble[0] = Xf

    # Context elements
    p_opt = ctx['p_opt']
    CI_95 = ctx['CI_95']
    rho, time_dap = ctx['fda_pair']
    FDA_add_idx = ctx['FDA_add_idx']
    Km = ctx['Km']
    orig_time = ctx['Tpair'][:, 0]
    orig_temp = ctx['Tpair'][:, 1]

    # x0 (como en monte_carlo_module)
    x0 = np.array([0.2, Km[0, 3] / 1000.0, Km[0, 0], Km[0, 1], 0.0])

    mask_free = (flags_override == 0)
    kfixed = np.where(flags_override == 1, kfixed_0, np.nan)
    lower, upper = CI_95

    for i in range(1, n_runs):
        # sample only for free indices available in CI
        k_free = []
        for idx in np.where(mask_free)[0]:
            lo, hi = lower[idx], upper[idx]
            if np.isfinite(lo) and np.isfinite(hi):
                k_free.append(np.random.uniform(lo, hi))
            else:
                # fallback to p_opt if CI missing
                k_free.append(p_opt[idx])
        k_free = np.asarray(k_free, dtype=float)

        _, Xf_i = resimulate_optimal(
            k_free=k_free,
            x0=x0,
            time_dap=time_dap,
            int_time=orig_time,
            exp_temp=orig_temp,
            Kinetic_Matrix=Km,
            kfixed=kfixed,
            FDA_add_idx=FDA_add_idx,
        )

        if Xf_i.shape[0] != n_t:
            diff = n_t - Xf_i.shape[0]
            if diff > 0:
                Xf_i = np.vstack([Xf_i, np.tile(Xf_i[-1], (diff, 1))])
            else:
                Xf_i = Xf_i[:n_t]
        X_ensemble[i] = Xf_i

    # Update flags in ctx clone for downstream use
    ctx2 = dict(ctx)
    ctx2['flags'] = flags_override.copy()
    return T, X_ensemble, ctx2


def evaluate_combo(model_id: int, exper_id: int, scale_id: int, kfixed_0: np.ndarray,
                   n_runs: int = 100, random_seed: Optional[int] = 42,
                   out_dirs: Optional[Dict[str, str]] = None,
                   make_figure: bool = True) -> Tuple[pd.DataFrame, ComboMetadata]:
    """
    Run MC ensemble for a single (model, exper, scale) and compute indicators
    for variables with experimental data. Saves a figure if requested.
    Returns (metrics_df, metadata).
    """
    t0 = time.perf_counter()
    T, X_ens, ctx = run_monte_carlo(model_id, scale_id, exper_id, kfixed_0,
                                     n_runs=n_runs, random_seed=random_seed)
    wall = time.perf_counter() - t0

    # Prepare per-variable series at kinetic points
    series = _extract_series(ctx, X_ens)

    # Pre/post DAP split
    t_split = float(ctx['fda_pair'][1])

    # number of free params
    flags = ctx['flags']
    n_free = int(np.sum(flags == 0))

    # sampling adequacy
    t_samples_all = ctx['Tpair'][ctx['Measure_idx'], 0]
    duration_h = float(t_samples_all.max() - t_samples_all.min()) if t_samples_all.size > 0 else np.nan
    samples_per_day = float(len(t_samples_all) / max(1e-9, (duration_h / 24.0))) if not math.isnan(duration_h) else np.nan
    n_obs_total = int(np.sum(~np.isnan(series[1]['y_true'])) + np.sum(~np.isnan(series[2]['y_true'])) + np.sum(~np.isnan(series[3]['y_true'])))
    edof = float(n_obs_total - n_free) if n_obs_total > 0 else np.nan
    p_over_n = float(n_free / n_obs_total) if n_obs_total > 0 else np.nan

    fim_cond = _compute_fim_condition(ctx, kfixed_0)
    pct_at_ci_limit = _percent_at_ci_limits(ctx, tol_frac=0.05)

    # Compute metrics per variable (only those with data indices 1,2,3)
    vm_list: List[VariableMetrics] = []
    for j in [2, 3, 1]:  # Glucose, Fructose, YAN
        vm = _compute_variable_metrics(j, series[j], n_free=n_free, t_split=t_split)
        vm_list.append(vm)

    # Save figure
    if make_figure and out_dirs is not None:
        try:
            fig, axes = plot_simulation_ensemble(T, X_ens, ctx,
                                                 label_prefix=f"M{model_id}",
                                                 exper_id=exper_id,
                                                 is_primary=True,
                                                 exp_marker='o',
                                                 color='#332288')
            fig.suptitle(f"Model {model_id} – Exp {exper_id} – Scale {scale_id}")
            fig.tight_layout()
            fig_path = os.path.join(out_dirs['figs'], f"ensemble_M{model_id}_E{exper_id}_S{scale_id}.png")
            fig.savefig(fig_path, dpi=200)
            plt.close(fig)
        except Exception:
            pass

    # Assemble DataFrame
    rows = [asdict(vm) for vm in vm_list]
    df = pd.DataFrame(rows)
    df.insert(0, 'model_id', model_id)
    df.insert(1, 'exper_id', exper_id)
    df.insert(2, 'scale_id', scale_id)

    meta = ComboMetadata(
        model_id=model_id,
        exper_id=exper_id,
        scale_id=scale_id,
        n_runs=n_runs,
        n_free=n_free,
        duration_h=duration_h,
        samples_per_day=samples_per_day,
        n_obs_total=n_obs_total,
        edof=edof,
        p_over_n=p_over_n,
        fim_cond=fim_cond,
        wall_time_s=wall,
        pct_at_ci_limit=pct_at_ci_limit,
    )

    return df, meta


def run_lab_validation(models: List[int], expers: List[int], kfixed_0: np.ndarray,
                       n_runs: int, seed: Optional[int], out_base: str) -> None:
    dirs = ensure_dirs(out_base)
    all_rows = []
    meta_rows = []
    for model_id in models:
        for exper_id in expers:
            df, meta = evaluate_combo(model_id, exper_id, 1, kfixed_0, n_runs=n_runs,
                                      random_seed=seed, out_dirs=dirs, make_figure=True)
            all_rows.append(df)
            meta_rows.append(asdict(meta))

    metrics_df = pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()
    meta_df = pd.DataFrame(meta_rows)
    metrics_df.to_csv(os.path.join(dirs['metrics'], 'lab_metrics.csv'), index=False)
    meta_df.to_csv(os.path.join(dirs['metrics'], 'lab_meta.csv'), index=False)


def run_lab_ablation(models: List[int], expers: List[int], kfixed_0: np.ndarray,
                     n_runs: int, seed: Optional[int], out_base: str) -> None:
    """Indicator (vi): ΔAICc, ΔMNCI, ΔRSQ when fixing each currently-free parameter (one-at-a-time)."""
    dirs = ensure_dirs(out_base)
    per_exp_rows = []

    for model_id in models:
        for exper_id in expers:
            # Baseline
            T0, X0, ctx0 = run_monte_carlo(model_id, 1, exper_id, kfixed_0, n_runs=n_runs, random_seed=seed)
            series0 = _extract_series(ctx0, X0)
            n_free0 = int(np.sum(ctx0['flags'] == 0))
            base_scores = _compute_global_scores(ctx0, series0, n_free0)

            free_idx = np.where(ctx0['flags'] == 0)[0]
            for idx in free_idx:
                flags_alt = ctx0['flags'].copy()
                flags_alt[idx] = 1  # fix this parameter
                T1, X1, ctx1 = _run_monte_carlo_with_flags(model_id, 1, exper_id, kfixed_0,
                                                           flags_alt, n_runs=n_runs, random_seed=seed)
                series1 = _extract_series(ctx1, X1)
                n_free1 = int(np.sum(ctx1['flags'] == 0))
                alt_scores = _compute_global_scores(ctx1, series1, n_free1)

                per_exp_rows.append({
                    'model_id': model_id,
                    'exper_id': exper_id,
                    'param_idx': int(idx),
                    'param_name': PARAM_COLS[idx] if idx < len(PARAM_COLS) else f'p{idx}',
                    'AICc_base': base_scores['AICc'],
                    'MNCI_base': base_scores['MNCI'],
                    'RSQ_base': base_scores['RSQ'],
                    'AICc_alt': alt_scores['AICc'],
                    'MNCI_alt': alt_scores['MNCI'],
                    'RSQ_alt': alt_scores['RSQ'],
                    'delta_AICc': alt_scores['AICc'] - base_scores['AICc'] if np.all(np.isfinite([alt_scores['AICc'], base_scores['AICc']])) else np.nan,
                    'delta_MNCI': alt_scores['MNCI'] - base_scores['MNCI'] if np.all(np.isfinite([alt_scores['MNCI'], base_scores['MNCI']])) else np.nan,
                    'delta_RSQ': alt_scores['RSQ'] - base_scores['RSQ'] if np.all(np.isfinite([alt_scores['RSQ'], base_scores['RSQ']])) else np.nan,
                })

    if per_exp_rows:
        per_df = pd.DataFrame(per_exp_rows)
        per_df.to_csv(os.path.join(dirs['metrics'], 'lab_ablation_per_experiment.csv'), index=False)
        # Aggregate by model and param
        agg = (per_df.groupby(['model_id', 'param_idx', 'param_name'])[['delta_AICc', 'delta_MNCI', 'delta_RSQ']]
                    .mean().reset_index())
        agg.to_csv(os.path.join(dirs['metrics'], 'lab_ablation_summary.csv'), index=False)


def _cliffs_delta(x: np.ndarray, y: np.ndarray) -> float:
    """Compute Cliff's delta effect size for two independent samples (approx via ranks)."""
    # Efficient approximation using ranks
    xy = np.concatenate([x, y])
    ranks = pd.Series(xy).rank().to_numpy()
    rx = float(np.mean(ranks[:len(x)]))
    ry = float(np.mean(ranks[len(x):]))
    n1, n2 = len(x), len(y)
    delta = (2 * (rx - ry)) / (n1 + n2)
    return float(delta)


def run_transfer_param_tests(models: List[int], lab_expers: List[int], pilot_expers: List[int],
                             kfixed_0: np.ndarray, seed: Optional[int], out_base: str,
                             n_samples: int = 1000) -> None:
    """Indicator (transfer iii): Compare parameter distributions between scales via CI-based sampling.
    Uses uniform sampling within 95% CI as a proxy for the calibrated distribution.
    """
    dirs = ensure_dirs(out_base)
    rows = []
    for model_id in models:
        # Grab context for each scale using one cheap MC run
        _, _, ctx_lab = run_monte_carlo(model_id, 1, lab_expers[0], kfixed_0, n_runs=1, random_seed=seed)
        _, _, ctx_pil = run_monte_carlo(model_id, 2, pilot_expers[0], kfixed_0, n_runs=1, random_seed=seed)

        p_lab, ci_lab, flags_lab = ctx_lab['p_opt'], ctx_lab['CI_95'], ctx_lab['flags']
        p_pil, ci_pil, flags_pil = ctx_pil['p_opt'], ctx_pil['CI_95'], ctx_pil['flags']

        for idx in range(min(len(p_lab), len(p_pil))):
            # Only compare if both CI bounds exist and parameter is free in at least one scale
            lo1, hi1 = ci_lab[0, idx], ci_lab[1, idx]
            lo2, hi2 = ci_pil[0, idx], ci_pil[1, idx]
            if not (np.isfinite(lo1) and np.isfinite(hi1) and np.isfinite(lo2) and np.isfinite(hi2)):
                continue
            # Sample uniformly within CI (proxy)
            rng = np.random.default_rng(seed)
            s1 = rng.uniform(lo1, hi1, size=n_samples)
            s2 = rng.uniform(lo2, hi2, size=n_samples)
            # Mann–Whitney U nonparametric test
            try:
                stat, pval = mannwhitneyu(s1, s2, alternative='two-sided')
            except Exception:
                pval = np.nan
            # Cliff's delta
            try:
                delta = _cliffs_delta(s1, s2)
            except Exception:
                delta = np.nan
            # Significance coding (α=1%)
            if np.isfinite(pval):
                signif = '**' if pval <= 0.01 else ('*' if pval <= 0.05 else 'ns')
            else:
                signif = 'na'
            rows.append({
                'model_id': model_id,
                'param_idx': idx,
                'param_name': PARAM_COLS[idx] if idx < len(PARAM_COLS) else f'p{idx}',
                'lab_mean': float(np.mean(s1)),
                'pilot_mean': float(np.mean(s2)),
                'p_value': float(pval) if np.isfinite(pval) else np.nan,
                'significance': signif,
                'cliffs_delta': float(delta) if np.isfinite(delta) else np.nan,
                'lab_lo': float(lo1), 'lab_hi': float(hi1),
                'pilot_lo': float(lo2), 'pilot_hi': float(hi2),
            })

    if rows:
        df = pd.DataFrame(rows)
        df.to_csv(os.path.join(dirs['metrics'], 'transfer_param_tests.csv'), index=False)


def run_pilot_transfer(models: List[int], lab_expers: List[int], pilot_expers: List[int],
                       kfixed_0: np.ndarray, n_runs: int, seed: Optional[int], out_base: str) -> None:
    dirs = ensure_dirs(out_base)
    # Load lab baseline if already computed to avoid recomputation
    lab_metrics_path = os.path.join(dirs['metrics'], 'lab_metrics.csv')
    if os.path.exists(lab_metrics_path):
        lab_df = pd.read_csv(lab_metrics_path)
        lab_df['context'] = 'lab'
    else:
        lab_rows = []
        for model_id in models:
            for exper_id in lab_expers:
                df, _ = evaluate_combo(model_id, exper_id, 1, kfixed_0, n_runs=n_runs,
                                       random_seed=seed, out_dirs=dirs, make_figure=False)
                lab_rows.append(df.assign(context='lab'))
        lab_df = pd.concat(lab_rows, ignore_index=True) if lab_rows else pd.DataFrame()

    pilot_rows = []
    pilot_meta_rows = []
    for model_id in models:
        for exper_id in pilot_expers:
            df, meta = evaluate_combo(model_id, exper_id, 2, kfixed_0, n_runs=n_runs,
                                      random_seed=seed, out_dirs=dirs, make_figure=True)
            pilot_rows.append(df.assign(context='pilot'))
            pilot_meta_rows.append(asdict(meta))

    pilot_df = pd.concat(pilot_rows, ignore_index=True) if pilot_rows else pd.DataFrame()
    pilot_meta_df = pd.DataFrame(pilot_meta_rows) if pilot_meta_rows else pd.DataFrame()

    # Aggregate by model-variable taking mean across experiments (compute both R2 and R2_adj)
    agg_cols = ['r2_mean', 'r2_std', 'r2_adj_mean', 'r2_adj_std', 'rmsd_median']
    lab_agg = (lab_df.groupby(['model_id', 'variable'])[agg_cols]
                     .mean().reset_index().rename(columns={c: f"lab_{c}" for c in agg_cols}))
    pilot_agg = (pilot_df.groupby(['model_id', 'variable'])[agg_cols]
                       .mean().reset_index().rename(columns={c: f"pilot_{c}" for c in agg_cols}))

    merged = pd.merge(lab_agg, pilot_agg, on=['model_id', 'variable'], how='inner')
    # Deltas: pilot - lab (prefer unadjusted R2 for decisions, keep adjusted for reference)
    merged['delta_r2'] = merged['pilot_r2_mean'] - merged['lab_r2_mean']
    merged['delta_r2_adj'] = merged['pilot_r2_adj_mean'] - merged['lab_r2_adj_mean']
    merged['delta_rmsd'] = merged['pilot_rmsd_median'] - merged['lab_rmsd_median']

    merged.to_csv(os.path.join(dirs['metrics'], 'transfer_deltas.csv'), index=False)
    lab_df.to_csv(os.path.join(dirs['metrics'], 'pilot_lab_raw.csv'), index=False)
    pilot_df.to_csv(os.path.join(dirs['metrics'], 'pilot_pilot_raw.csv'), index=False)
    if not pilot_meta_df.empty:
        pilot_meta_df.to_csv(os.path.join(dirs['metrics'], 'pilot_meta.csv'), index=False)


def _forecast_lab_to_pilot_ensemble(model_id: int, lab_exper: int, pilot_exper: int,
                                    kfixed_0: np.ndarray, n_runs: int,
                                    seed: Optional[int]) -> Tuple[np.ndarray, np.ndarray, dict, dict]:
    """Build an ensemble of pilot predictions using lab CI sampling.
    Returns (T, X_ensemble, ctx_lab, ctx_pilot).
    """
    rng = np.random.default_rng(seed)
    # Get lab context (for CI and flags)
    _, _, ctx_lab = run_monte_carlo(model_id, 1, lab_exper, kfixed_0, n_runs=1, random_seed=seed)
    # Get pilot context (for time/temp/Km and y_true)
    Tpil, Xpil, ctx_pil = run_monte_carlo(model_id, 2, pilot_exper, kfixed_0, n_runs=1, random_seed=seed)

    # Sampling setup
    flags = ctx_lab['flags']
    p_opt = ctx_lab['p_opt']
    CI_95 = ctx_lab['CI_95']
    free_idx = np.where(flags == 0)[0]
    kfixed = np.where(flags == 1, kfixed_0, np.nan)
    lower, upper = CI_95

    int_time = ctx_pil['Tpair'][:, 0]
    exp_temp = ctx_pil['Tpair'][:, 1]
    Km = ctx_pil['Km']
    time_dap = float(ctx_pil['fda_pair'][1])
    FDA_add_idx = int(ctx_pil['FDA_add_idx'])

    # x0 for pilot
    x0 = np.array([0.2, Km[0, 3] / 1000.0, Km[0, 0], Km[0, 1], 0.0])

    n_t = len(int_time)
    # First member: use p_opt (projected to free indices from lab) to infer n_vars
    k_free0 = p_opt[free_idx].astype(float)
    _, X0 = resimulate_optimal(
        k_free=k_free0,
        x0=x0,
        time_dap=time_dap,
        int_time=int_time,
        exp_temp=exp_temp,
        Kinetic_Matrix=Km,
        kfixed=kfixed,
        FDA_add_idx=FDA_add_idx,
    )
    n_vars = X0.shape[1]
    X_ensemble = np.zeros((n_runs, n_t, n_vars))
    X_ensemble[0] = X0

    for i in range(1, n_runs):
        k_free_s = []
        for idx in free_idx:
            lo, hi = lower[idx], upper[idx]
            if np.isfinite(lo) and np.isfinite(hi):
                k_free_s.append(rng.uniform(lo, hi))
            else:
                k_free_s.append(p_opt[idx])
        k_free_s = np.asarray(k_free_s, dtype=float)
        _, Xi = resimulate_optimal(
            k_free=k_free_s,
            x0=x0,
            time_dap=time_dap,
            int_time=int_time,
            exp_temp=exp_temp,
            Kinetic_Matrix=Km,
            kfixed=kfixed,
            FDA_add_idx=FDA_add_idx,
        )
        if Xi.shape[0] != n_t:
            diff = n_t - Xi.shape[0]
            if diff > 0:
                Xi = np.vstack([Xi, np.tile(Xi[-1], (diff, 1))])
            else:
                Xi = Xi[:n_t]
        X_ensemble[i] = Xi

    return int_time, X_ensemble, ctx_lab, ctx_pil


def run_transfer_fidelity(models: List[int], lab_expers: List[int], pilot_expers: List[int],
                          kfixed_0: np.ndarray, n_runs: int, seed: Optional[int], out_base: str) -> None:
    """Indicator (transfer iv): Fidelity of lab-derived forecasts to pilot data.
    Computes coverage within lab 95% CI bands and within μ±1σ bands, plus normalized band width.
    """
    dirs = ensure_dirs(out_base)
    rows = []
    for model_id in models:
        donor_lab = lab_expers[0]
        for pilot_exper in pilot_expers:
            T, X_ens, ctx_lab, ctx_pil = _forecast_lab_to_pilot_ensemble(model_id, donor_lab, pilot_exper,
                                                                          kfixed_0, n_runs, seed)
            series = _extract_series(ctx_pil, X_ens)
            for j in [1, 2, 3]:
                s = series[j]
                y_true = s['y_true']
                if np.all(np.isnan(y_true)):
                    continue
                y_low = s['lower']
                y_med = s['median']
                y_up = s['upper']
                # 95% band coverage
                cov95 = coverage_within_bounds(y_true, y_low, y_up)
                bw95 = band_width_normalized(y_low, y_up, y_true)
                # μ ± 1σ band using per-time std across runs
                std_t = np.std(s['runs'], axis=0)
                mu_lo = y_med - std_t
                mu_up = y_med + std_t
                cov_mu = coverage_within_bounds(y_true, mu_lo, mu_up)
                bw_mu = band_width_normalized(mu_lo, mu_up, y_true)
                rows.append({
                    'model_id': model_id,
                    'lab_exper_donor': donor_lab,
                    'pilot_exper': pilot_exper,
                    'variable': VAR_LABELS[j],
                    'coverage_95': cov95,
                    'band_width_norm_95': bw95,
                    'coverage_mu_1sd': cov_mu,
                    'band_width_norm_mu_1sd': bw_mu,
                })
    if rows:
        df = pd.DataFrame(rows)
        df.to_csv(os.path.join(dirs['metrics'], 'transfer_fidelity.csv'), index=False)


def run_transfer_effort_stats(out_base: str) -> None:
    """Indicator (transfer v): Effort proxies from meta. Uses wall_time_s and grid size."""
    dirs = ensure_dirs(out_base)
    lab_meta_path = os.path.join(dirs['metrics'], 'lab_meta.csv')
    pilot_meta_path = os.path.join(dirs['metrics'], 'pilot_meta.csv')
    if not (os.path.exists(lab_meta_path) and os.path.exists(pilot_meta_path)):
        return
    lab = pd.read_csv(lab_meta_path)
    pil = pd.read_csv(pilot_meta_path)
    # Aggregate per model
    lab_g = lab.groupby('model_id')['wall_time_s'].mean().rename('lab_wall_time_s')
    pil_g = pil.groupby('model_id')['wall_time_s'].mean().rename('pilot_wall_time_s')
    merged = pd.concat([lab_g, pil_g], axis=1).reset_index()
    merged['effort_ratio_pilot_over_lab'] = merged['pilot_wall_time_s'] / merged['lab_wall_time_s']
    merged.to_csv(os.path.join(dirs['metrics'], 'transfer_effort_stats.csv'), index=False)


def run_transfer_yan_late_summary(out_base: str) -> None:
    """Indicator (transfer vi): Aggregate YAN late-phase bias and errors for pilot."""
    dirs = ensure_dirs(out_base)
    pilot_raw_path = os.path.join(dirs['metrics'], 'pilot_pilot_raw.csv')
    if not os.path.exists(pilot_raw_path):
        return
    df = pd.read_csv(pilot_raw_path)
    yan = df[df['variable'] == 'YAN']
    if yan.empty:
        return
    agg = (yan.groupby('model_id')[['yan_late_bias', 'mae_percent_median', 'ecp_10_90', 'band_width_norm']]
             .agg(['mean', 'std']).reset_index())
    agg.columns = ['model_id',
                   'yan_late_bias_mean', 'yan_late_bias_std',
                   'mae_percent_median_mean', 'mae_percent_median_std',
                   'ecp_10_90_mean', 'ecp_10_90_std',
                   'band_width_norm_mean', 'band_width_norm_std']
    agg.to_csv(os.path.join(dirs['metrics'], 'transfer_yan_late_summary.csv'), index=False)


def run_transfer_robustness_noise(models: List[int], pilot_expers: List[int],
                                  kfixed_0: np.ndarray, n_runs: int, seed: Optional[int],
                                  out_base: str) -> None:
    """Indicator (transfer vii): Robustness to noise via synthetic perturbation of y_true (5% range)."""
    dirs = ensure_dirs(out_base)
    rng = np.random.default_rng(seed)
    rows = []
    for model_id in models:
        for exper_id in pilot_expers:
            # Build pilot native ensemble
            T, X_ens, ctx = run_monte_carlo(model_id, 2, exper_id, kfixed_0, n_runs=n_runs, random_seed=seed)
            series = _extract_series(ctx, X_ens)
            for j in [1, 2, 3]:
                s = series[j]
                y_true = s['y_true']
                if np.all(np.isnan(y_true)):
                    continue
                y_med = s['median']
                rng_y = max(1e-9, float(np.nanmax(y_true) - np.nanmin(y_true)))
                sigma = 0.05 * rng_y
                y_noisy = y_true + rng.normal(0.0, sigma, size=y_true.shape)
                rmsd_orig = rmsd(y_true, y_med)
                rmsd_noisy = rmsd(y_noisy, y_med)
                rows.append({
                    'model_id': model_id,
                    'pilot_exper': exper_id,
                    'variable': VAR_LABELS[j],
                    'rmsd_orig': rmsd_orig,
                    'rmsd_noisy': rmsd_noisy,
                    'rmsd_delta': (rmsd_noisy - rmsd_orig) if (np.isfinite(rmsd_orig) and np.isfinite(rmsd_noisy)) else np.nan,
                })
    if rows:
        pd.DataFrame(rows).to_csv(os.path.join(dirs['metrics'], 'transfer_robustness_noise.csv'), index=False)


def run_transfer_stratified_temp(models: List[int], pilot_expers: List[int],
                                 kfixed_0: np.ndarray, n_runs: int, seed: Optional[int],
                                 out_base: str) -> None:
    """Indicator (transfer viii): Stratify pilot metrics by temperature terciles."""
    dirs = ensure_dirs(out_base)
    rows = []
    for model_id in models:
        for exper_id in pilot_expers:
            T, X_ens, ctx = run_monte_carlo(model_id, 2, exper_id, kfixed_0, n_runs=n_runs, random_seed=seed)
            series = _extract_series(ctx, X_ens)
            t_s = ctx['Tpair'][ctx['Measure_idx'], 1]  # temperatures at sample times
            if t_s.size == 0:
                continue
            terciles = np.quantile(t_s, [1/3, 2/3])
            groups = [t_s < terciles[0], (t_s >= terciles[0]) & (t_s < terciles[1]), t_s >= terciles[1]]
            for j in [1, 2, 3]:
                s = series[j]
                y_true = s['y_true']
                y_med = s['median']
                if np.all(np.isnan(y_true)):
                    continue
                for gi, mask in enumerate(groups):
                    idx = np.where(mask)[0]
                    if idx.size == 0:
                        continue
                    r = rmsd(y_true[idx], y_med[idx])
                    rows.append({
                        'model_id': model_id,
                        'pilot_exper': exper_id,
                        'variable': VAR_LABELS[j],
                        'temp_group': f'T{gi+1}',
                        'rmsd': r,
                        'n_points': int(idx.size),
                        't_min': float(np.min(t_s[idx])),
                        't_max': float(np.max(t_s[idx])),
                    })
    if rows:
        pd.DataFrame(rows).to_csv(os.path.join(dirs['metrics'], 'transfer_stratified_temp.csv'), index=False)


def run_transfer_calibration(models: List[int], pilot_expers: List[int],
                             kfixed_0: np.ndarray, n_runs: int, seed: Optional[int],
                             out_base: str) -> None:
    """Indicator (transfer ix): Calibration curves and interval scores for pilot native predictions."""
    dirs = ensure_dirs(out_base)
    alpha_grid = [0.1, 0.2, 0.3, 0.4]
    rows = []
    for model_id in models:
        for exper_id in pilot_expers:
            T, X_ens, ctx = run_monte_carlo(model_id, 2, exper_id, kfixed_0, n_runs=n_runs, random_seed=seed)
            series = _extract_series(ctx, X_ens)
            for j in [1, 2, 3]:
                s = series[j]
                y_true = s['y_true']
                if np.all(np.isnan(y_true)):
                    continue
                runs = s['runs']
                for alpha in alpha_grid:
                    qlow = 100.0 * (alpha / 2.0)
                    qhi = 100.0 * (1.0 - alpha / 2.0)
                    lo = np.percentile(runs, qlow, axis=0)
                    hi = np.percentile(runs, qhi, axis=0)
                    cov = coverage_within_bounds(y_true, lo, hi)
                    # Nominal coverage = 1 - alpha
                    nom = 1.0 - alpha
                    miscal = cov - nom
                    # Winkler interval score for central (1-alpha) interval
                    width = hi - lo
                    below = (lo - y_true).clip(min=0.0)
                    above = (y_true - hi).clip(min=0.0)
                    score = np.mean(width + (2.0 / alpha) * below + (2.0 / alpha) * above)
                    rows.append({
                        'model_id': model_id,
                        'pilot_exper': exper_id,
                        'variable': VAR_LABELS[j],
                        'alpha': alpha,
                        'coverage': cov,
                        'nominal': nom,
                        'miscalibration': miscal,
                        'interval_score': float(score),
                    })
    if rows:
        pd.DataFrame(rows).to_csv(os.path.join(dirs['metrics'], 'transfer_calibration.csv'), index=False)


def run_transfer_go_nogo(out_base: str) -> None:
    """Indicator (transfer x): Simple go/no-go decision table based on thresholds."""
    dirs = ensure_dirs(out_base)
    deltas_path = os.path.join(dirs['metrics'], 'transfer_deltas.csv')
    fidel_path = os.path.join(dirs['metrics'], 'transfer_fidelity.csv')
    if not (os.path.exists(deltas_path) and os.path.exists(fidel_path)):
        return
    deltas = pd.read_csv(deltas_path)
    fidel = pd.read_csv(fidel_path)
    # Criteria per variable: coverage_95 >= 0.7 and delta_r2 >= -0.10 (use unadjusted R2)
    rows = []
    for model_id in deltas['model_id'].unique():
        ok_vars = 0
        total_vars = 0
        for var in ['Glucose', 'Fructose', 'YAN']:
            d = deltas[(deltas['model_id'] == model_id) & (deltas['variable'] == var)]
            f = fidel[(fidel['model_id'] == model_id) & (fidel['variable'] == var)]
            if d.empty or f.empty:
                continue
            total_vars += 1
            cov_ok = f['coverage_95'].mean() >= 0.7
            # Prefer unadjusted R2 for decision
            if 'delta_r2' in d.columns:
                r2_ok = d['delta_r2'].mean() >= -0.10
            else:
                r2_ok = d['delta_r2_adj'].mean() >= -0.10
            ok_vars += int(cov_ok and r2_ok)
        decision = 'GO' if (total_vars > 0 and ok_vars >= max(1, math.ceil(0.67 * total_vars))) else 'NO-GO'
        rows.append({'model_id': model_id, 'ok_vars': ok_vars, 'total_vars': total_vars, 'decision': decision})
    if rows:
        pd.DataFrame(rows).to_csv(os.path.join(dirs['metrics'], 'transfer_go_nogo.csv'), index=False)


def write_notes(out_base: str) -> None:
    notes = f"""
This folder contains outputs from the new validation pipeline (validation_pipeline.py).

Key files:
- metrics/lab_metrics.csv: Per-variable indicators for lab validation runs.
- metrics/lab_meta.csv: Combo-level metadata (n_free, EDoF, FIM condition, timing, % at CI limits).
- metrics/pilot_lab_raw.csv and metrics/pilot_pilot_raw.csv: Raw per-variable metrics for lab and pilot contexts.
- metrics/pilot_meta.csv: Pilot combo-level metadata analogous to lab_meta.
- metrics/transfer_deltas.csv: Pilot minus Lab deltas in R2_adj and RMSD.
- metrics/transfer_param_tests.csv: Cross-scale parameter distribution comparisons (Mann–Whitney, Cliff's delta).
- metrics/transfer_fidelity.csv: Coverage and band widths for lab-forecasted pilot ensembles (95% and μ±1σ).
- metrics/transfer_effort_stats.csv: Effort proxies (pilot vs lab wall time ratios).
- metrics/transfer_yan_late_summary.csv: Pilot YAN late-phase bias and error aggregation.
- metrics/transfer_robustness_noise.csv: RMSD sensitivity to 5% synthetic noise in observations.
- metrics/transfer_stratified_temp.csv: RMSD stratified by temperature terciles.
- metrics/transfer_calibration.csv: Calibration curves and interval scores across alpha levels.
- metrics/transfer_go_nogo.csv: Simple go/no-go decision table by model.
- figs/ensemble_*.png: Simulation vs experimental panels with 10–90% bands.

Notes:
- Lab indicators implemented: (i)-(v), (vi) ablation, (vii), (viii), (ix via FIM cond proxy and % at CI limits), (x via wall time).
- Transfer indicators implemented: (i) deltas, (ii) raw metrics, (iii) parameter tests, (iv) fidelity (band coverage), (v) effort stats, (vi) YAN late summary, (vii) robustness to noise, (viii) stratification by disturbances (temperature), (ix) calibration curves/interval scores, (x) go/no-go table.
"""
    with open(os.path.join(out_base, "README_salidas.txt"), "w", encoding="utf-8") as f:
        f.write(notes)


def run_full_pipeline(models: List[int], lab_expers: List[int], pilot_expers: List[int],
                      scale_ids: List[int], kfixed_0: np.ndarray,
                      n_runs: int = 100, seed: Optional[int] = 42,
                      out_dir: str = "salidas") -> None:
    # Enable quiet mode and silence common runtime warnings
    os.environ['PIPELINE_QUIET'] = os.environ.get('PIPELINE_QUIET', '1')
    warnings.filterwarnings('ignore', category=RuntimeWarning)
    warnings.filterwarnings('ignore', category=UserWarning)
    warnings.filterwarnings('ignore', message='Mean of empty slice')
    warnings.filterwarnings('ignore', message='Degrees of freedom <= 0')

    base = os.path.abspath(out_dir)
    os.makedirs(base, exist_ok=True)
    # Lab
    run_lab_validation(models, lab_expers, kfixed_0, n_runs=n_runs, seed=seed, out_base=base)
    # Lab ablation (single-parameter fix toggles)
    run_lab_ablation(models, lab_expers, kfixed_0, n_runs=min(n_runs, 50), seed=seed, out_base=base)
    # Pilot transfer
    run_pilot_transfer(models, lab_expers, pilot_expers, kfixed_0, n_runs=n_runs, seed=seed, out_base=base)
    # Parameter distribution comparisons across scales (ANOVA proxy)
    run_transfer_param_tests(models, lab_expers, pilot_expers, kfixed_0, seed=seed, out_base=base, n_samples=1000)
    # Transfer fidelity using lab->pilot ensembles
    run_transfer_fidelity(models, lab_expers, pilot_expers, kfixed_0, n_runs=n_runs, seed=seed, out_base=base)
    # Effort stats and YAN late summary
    run_transfer_effort_stats(base)
    run_transfer_yan_late_summary(base)
    # Robustness, stratification, calibration and go/no-go
    run_transfer_robustness_noise(models, pilot_expers, kfixed_0, n_runs=min(n_runs, 60), seed=seed, out_base=base)
    run_transfer_stratified_temp(models, pilot_expers, kfixed_0, n_runs=n_runs, seed=seed, out_base=base)
    run_transfer_calibration(models, pilot_expers, kfixed_0, n_runs=n_runs, seed=seed, out_base=base)
    run_transfer_go_nogo(base)
    # Notes
    write_notes(base)


if __name__ == "__main__":
    # Example defaults (can be used for quick manual run)
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
    models = [1750]
    lab_expers = [6, 7]
    pilot_expers = [5, 6]
    run_full_pipeline(models, lab_expers, pilot_expers, [1, 2], kfixed_0, n_runs=50, seed=42, out_dir="salidas")

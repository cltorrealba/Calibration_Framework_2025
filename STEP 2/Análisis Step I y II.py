# -*- coding: utf-8 -*-
"""
Created on Thu May  8 09:58:24 2025

@author: ctorrealba
"""

# ========================================================================== #
# 0. LIBRARIES & PALETTES                                                    #
# ========================================================================== #
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import os
import json
from datetime import datetime
from scipy.stats import spearmanr, ttest_ind
import warnings
warnings.filterwarnings('ignore', category=UserWarning)

sns.set_theme(style='whitegrid')
PAL_GRAY = sns.color_palette('colorblind')[7]
PAL_BLUE = sns.color_palette('colorblind')[0]
PAL_3    = sns.color_palette('colorblind')[5]

# ========================================================================== #
# 1. LOAD DATA & MARK STAGES                                                 #
# ========================================================================== #
df = pd.read_excel('C:/Users/ctorrealba/OneDrive - Viña Concha y Toro S.A/Documentos/MATLAB/Artículo Estimación - Notebook/Tesis 2020/Zenteno Files/2023_CrossValidation/Step 2 - Viable structure selection/HIPPO_result.xlsx', sheet_name='Sheet1')

PARAM_COLS = [
    'mu0','betaG0','betaF0','Kn0','Kg0','Kf0','Kig0',
    'Kie0','Yxn','Yxg','Yxf','Yeg','Yef'
]
param_labels = {
    'mu0':    r'$\mu_0$',
    'betaG0': r'$\beta_{G0}$',
    'betaF0': r'$\beta_{F0}$',
    'Kn0':    r'$K_{n0}$',
    'Kg0':    r'$K_{g0}$',
    'Kf0':    r'$K_{f0}$',
    'Kig0':   r'$K_{ig0}$',
    'Kie0':   r'$K_{ie0}$',
    'Yxn':    r'$Y_{xn}$',
    'Yxg':    r'$Y_{xg}$',
    'Yxf':    r'$Y_{xf}$',
    'Yeg':    r'$Y_{eg}$',
    'Yef':    r'$Y_{ef}$',
}
TOTAL_PARAMS = len(PARAM_COLS)
INDICES_PCA  = ['Akaike','MeanCC','Fobj']       # BIC excluded for PCA
INDICES_HEAT = ['Akaike','MeanCC','Fobj']       # for heat-maps

# viability mask
mask_viable = (df['CCc']==0) & (df['I955']==0)
df_all = df.copy()
df_all['stage']   = np.where(mask_viable, 'II', 'I')
df_all['n_fixed'] = TOTAL_PARAMS - df_all['estim_params']
stage2 = df_all[df_all['stage']=='II']

# ========================================================================== #
# 2. FIGURE 1 – Panel A (histogram with counts)                              #
# ========================================================================== #
fig1, axA = plt.subplots(figsize=(7,4))
bins = np.arange(df_all['n_fixed'].min() - 0.5,
                 df_all['n_fixed'].max() + 1.5, 1)
width = bins[1] - bins[0]

# full pool
counts_all, edges_all, _ = axA.hist(
    df_all['n_fixed'], bins=bins,
    color=PAL_GRAY, alpha=0.4, width=0.45, label='Stage I models'
)
for count, left in zip(counts_all, edges_all[:-1]):
    c = float(count)
    if c > 0:
        center = left + width/2
        axA.text(center, c + 0.3, f'{int(c)}',
                 ha='center', va='bottom', fontsize=8, color='black')

# filtered pool
bins2 = bins + 0.2
counts2, edges2, _ = axA.hist(
    stage2['n_fixed'], bins=bins2,
    color=PAL_BLUE, alpha=0.85, width=0.45, label='Stage II models'
)
for count, left in zip(counts2, edges2[:-1]):
    c = float(count)
    if c > 0:
        center = left + width/2
        axA.text(center, c + 0.6, f'{int(c)}',
                 ha='center', va='bottom', fontsize=8, color=PAL_BLUE)

axA.set_xlabel('Number of Fixed Parameters')
axA.set_ylabel('Count')
axA.set_title('Fixed-parameter distribution')
axA.legend()
fig1.tight_layout()
fig1.savefig('figure1_histogram_fixed.png', dpi=350)


# ========================================================================== #
# 2bis. QUANTITATIVE METRICS FOR PAPER                                       #
# ========================================================================== #
# Prepare output folder
os.makedirs('salidas', exist_ok=True)

# Overall counts
total_models   = int(len(df_all))
retained_models = int(len(stage2))
retention_rate  = retained_models / total_models if total_models > 0 else np.nan
elimination_rate = 1 - retention_rate if np.isfinite(retention_rate) else np.nan

# Fixed-parameter stats (Stage I population vs Stage II retained)
nfixed_all = df_all['n_fixed']
nfixed_sel = stage2['n_fixed']

stats = {
    'total_models': total_models,
    'retained_models': retained_models,
    'retention_rate_pct': round(100*retention_rate, 2) if np.isfinite(retention_rate) else np.nan,
    'elimination_rate_pct': round(100*elimination_rate, 2) if np.isfinite(elimination_rate) else np.nan,
    'n_fixed_all_mean': round(float(nfixed_all.mean()), 3),
    'n_fixed_all_median': round(float(nfixed_all.median()), 3),
    'n_fixed_all_min': int(nfixed_all.min()),
    'n_fixed_all_max': int(nfixed_all.max()),
    'n_fixed_sel_mean': round(float(nfixed_sel.mean()), 3),
    'n_fixed_sel_median': round(float(nfixed_sel.median()), 3),
    'n_fixed_sel_min': int(nfixed_sel.min()) if not nfixed_sel.empty else np.nan,
    'n_fixed_sel_max': int(nfixed_sel.max()) if not nfixed_sel.empty else np.nan,
}

# Complexity (free params) stats
est_all = df_all['estim_params']
est_sel = stage2['estim_params']
avg_complexity_reduction = float(est_all.mean() - est_sel.mean()) if not est_sel.empty else np.nan
stats.update({
    'estim_params_all_mean': round(float(est_all.mean()), 3),
    'estim_params_all_min': int(est_all.min()),
    'estim_params_all_max': int(est_all.max()),
    'estim_params_sel_mean': round(float(est_sel.mean()), 3) if not est_sel.empty else np.nan,
    'estim_params_sel_min': int(est_sel.min()) if not est_sel.empty else np.nan,
    'estim_params_sel_max': int(est_sel.max()) if not est_sel.empty else np.nan,
    'avg_complexity_reduction_mean_pars': round(avg_complexity_reduction, 3) if np.isfinite(avg_complexity_reduction) else np.nan,
})

# Rightward shift magnitude (Cohen's d on n_fixed)
def cohens_d(x, y):
    x = np.asarray(x); y = np.asarray(y)
    nx, ny = len(x), len(y)
    if nx < 2 or ny < 2:
        return np.nan
    vx = x.var(ddof=1); vy = y.var(ddof=1)
    sp = np.sqrt(((nx-1)*vx + (ny-1)*vy) / (nx+ny-2))
    return (y.mean() - x.mean()) / sp if sp > 0 else np.nan

effect_shift_nfixed = cohens_d(nfixed_all, nfixed_sel) if not nfixed_sel.empty else np.nan
stats['effect_size_nfixed_cohens_d'] = round(float(effect_shift_nfixed), 3) if np.isfinite(effect_shift_nfixed) else np.nan

# Per-bin retention (using the same bin edges as Figure 1)
retention_df = None
try:
    # Reuse edges from the histogram above
    centers = edges_all[:-1] + (edges_all[1]-edges_all[0])/2
    c_all, _ = np.histogram(nfixed_all, bins=edges_all)
    c_sel, _ = np.histogram(nfixed_sel, bins=edges_all)
    with np.errstate(divide='ignore', invalid='ignore'):
        frac = np.where(c_all>0, c_sel/c_all, np.nan)
    retention_df = pd.DataFrame({
        'n_fixed': centers,
        'count_all': c_all,
        'count_retained': c_sel,
        'retention_rate': frac,
        'retention_rate_pct': np.round(frac*100, 2)
    })
    retention_df.to_csv(os.path.join('salidas','retention_by_nfixed.csv'), index=False)
except Exception as e:
    # Fallback: independent bins
    pass

# Complexity criterion threshold (N_p - 2)
Np_max = int(est_sel.max()) if not est_sel.empty else np.nan
complexity_threshold = (Np_max - 2) if np.isfinite(Np_max) else np.nan
below_thresh = int((est_sel < complexity_threshold).sum()) if np.isfinite(complexity_threshold) else np.nan
stats.update({
    'Np_max_stageII': int(Np_max) if np.isfinite(Np_max) else np.nan,
    'complexity_threshold_Np_minus_2': int(complexity_threshold) if np.isfinite(complexity_threshold) else np.nan,
    'models_below_threshold_in_stageII': below_thresh
})

# Index improvements (Akaike, MeanCC, Fobj) – means and relative deltas
index_summary_rows = []
for idx in INDICES_HEAT:
    m_all = float(df_all[idx].mean())
    m_sel = float(stage2[idx].mean()) if not stage2.empty else np.nan
    rel = (m_sel - m_all)/m_all*100 if m_all != 0 else np.nan
    index_summary_rows.append({'index': idx, 'mean_stageI_all': round(m_all,3), 'mean_stageII_sel': round(m_sel,3) if np.isfinite(m_sel) else np.nan, 'delta_pct_sel_vs_all': round(rel,2) if np.isfinite(rel) else np.nan})
index_summary = pd.DataFrame(index_summary_rows)
index_summary.to_csv(os.path.join('salidas','index_summary.csv'), index=False)

# Save global stats JSON and CSV
with open(os.path.join('salidas','metrics_summary.json'), 'w', encoding='utf-8') as f:
    json.dump(stats, f, ensure_ascii=False, indent=2)
pd.DataFrame([stats]).to_csv(os.path.join('salidas','metrics_summary.csv'), index=False)

# Optional: auto-generate a narrative paragraph for the paper
try:
    right_shift = stats['n_fixed_sel_mean'] - stats['n_fixed_all_mean']
    top_bin = None
    if retention_df is not None and not retention_df.empty:
        # Highest retention bin
        rr = np.asarray(retention_df['retention_rate'].to_numpy(dtype=float))
        top_idx = int(np.nanargmax(rr))
        top_bin = int(retention_df.iloc[top_idx]['n_fixed'])
        top_ret = float(retention_df.iloc[top_idx]['retention_rate_pct'])
    paragraph = (
        f"HIPPO generated a total of {total_models} candidate structures, of which {retained_models} "
        f"({stats['retention_rate_pct']}%) were retained after applying identifiability and significance criteria. "
        f"The distribution of fixed parameters shifted rightward by {right_shift:.2f} on average "
        f"(Cohen's d = {stats['effect_size_nfixed_cohens_d']}) when comparing the retained subset to the full population, "
        f"indicating a tendency towards simpler specifications. In terms of free parameters, the average complexity decreased from "
        f"{stats['estim_params_all_mean']} to {stats['estim_params_sel_mean']} (Δ = {stats['avg_complexity_reduction_mean_pars']}). "
    )
    if top_bin is not None:
        paragraph += (
            f"Retention peaked among structures with approximately {top_bin} fixed parameters "
            f"(retention ≈ {top_ret}%), supporting the interpretation that over-parameterized variants were penalized by the diagnostics. "
        )
    paragraph += (
        f"The maximum admissible free-parameter count among retained models was Np = {stats['Np_max_stageII']}, yielding a complexity "
        f"threshold of Np-2 = {stats['complexity_threshold_Np_minus_2']}; the retained set contained {stats['models_below_threshold_in_stageII']} "
        f"models below this threshold."
    )
    with open(os.path.join('salidas','figure2A_narrative.txt'), 'w', encoding='utf-8') as f:
        f.write(paragraph)
except Exception:
    pass

# Print concise console summary
print("\n=== Stage I/II quantitative summary ===")
print(f"Total models (Stage I population): {total_models}")
print(f"Retained after filtering (Stage II): {retained_models} ({stats['retention_rate_pct']}% retained; {stats['elimination_rate_pct']}% eliminated)")
print(f"n_fixed mean (all vs retained): {stats['n_fixed_all_mean']} -> {stats['n_fixed_sel_mean']} (Cohen's d = {stats['effect_size_nfixed_cohens_d']})")
print(f"estim_params mean (all vs retained): {stats['estim_params_all_mean']} -> {stats['estim_params_sel_mean']} (Δ = {stats['avg_complexity_reduction_mean_pars']})")
print(f"Complexity threshold (Np-2): {stats['complexity_threshold_Np_minus_2']} (Np_max in Stage II = {stats['Np_max_stageII']})")


# ========================================================================== #
# 2ter. EXTENDED INDICATORS FOR STAGE I AND II                               #
# ========================================================================== #
rng = np.random.default_rng(42)

# --- Stage I Population metrics ------------------------------------------- #
def iqr(x):
    return np.percentile(x, 75) - np.percentile(x, 25)

pop_metrics = {
    'total_models': total_models,
    'n_fixed_mean': float(nfixed_all.mean()),
    'n_fixed_median': float(nfixed_all.median()),
    'n_fixed_iqr': float(iqr(nfixed_all)),
    'n_fixed_min': int(nfixed_all.min()),
    'n_fixed_max': int(nfixed_all.max()),
    'n_est_mean': float(est_all.mean()),
    'n_est_median': float(est_all.median()),
    'n_est_iqr': float(iqr(est_all)),
    'n_est_min': int(est_all.min()),
    'n_est_max': int(est_all.max()),
}

# Histogram bin counts for gray layer (Stage I)
hist_stageI = pd.DataFrame({
    'n_fixed_bin_center': edges_all[:-1] + (edges_all[1]-edges_all[0])/2,
    'count_stageI_gray': counts_all.astype(int)
})
hist_stageI.to_csv(os.path.join('salidas','histogram_stageI_gray.csv'), index=False)

# Save population metrics
pd.DataFrame([pop_metrics]).round(3).to_csv(os.path.join('salidas','stageI_population_metrics.csv'), index=False)

# --- Diversity of structures (fixation patterns) -------------------------- #
patterns = df_all[PARAM_COLS].astype(int).astype(str).agg(''.join, axis=1)
pat_counts = patterns.value_counts()
pat_probs = (pat_counts / pat_counts.sum()).values
shannon_entropy = float(-np.sum(pat_probs * np.log2(pat_probs + 1e-12)))
gini = float(1.0 - np.sum(pat_probs**2))
top_patterns = pat_counts.head(5).rename_axis('pattern').reset_index(name='count')
top_patterns['percent'] = (top_patterns['count'] / total_models * 100).round(2)
top_patterns.to_csv(os.path.join('salidas','stageI_top5_patterns.csv'), index=False)
with open(os.path.join('salidas','stageI_diversity.json'), 'w', encoding='utf-8') as f:
    json.dump({'shannon_entropy_bits': shannon_entropy, 'gini': gini}, f, indent=2)

# --- Baseline index summary & outliers (Tukey) ---------------------------- #
def tukey_fences(x):
    q1, q3 = np.percentile(x, [25, 75])
    iqr_v = q3 - q1
    low = q1 - 1.5*iqr_v
    high = q3 + 1.5*iqr_v
    outliers = int(((x < low) | (x > high)).sum())
    return q1, q3, iqr_v, low, high, outliers

rows = []
for idx in INDICES_HEAT:
    x = df_all[idx].astype(float).values
    mean = float(np.mean(x)); sd = float(np.std(x, ddof=1))
    p5, p95 = np.percentile(x, [5,95])
    q1, q3, iqrv, lowf, highf, nout = tukey_fences(x)
    rows.append({'index': idx, 'mean': mean, 'sd': sd, 'p5': p5, 'p95': p95,
                 'q1': q1, 'q3': q3, 'iqr': iqrv, 'lower_fence': lowf, 'upper_fence': highf,
                 'outlier_count': nout})
baseline_index = pd.DataFrame(rows).round(4)
baseline_index.to_csv(os.path.join('salidas','stageI_index_baseline.csv'), index=False)

# --- Spearman correlations (Stage I): n_fixed vs indices ------------------ #
spearman_rows = []
for idx in INDICES_HEAT:
    rho, pval = spearmanr(df_all['n_fixed'], df_all[idx])
    spearman_rows.append({'index': idx, 'spearman_rho': float(rho), 'p_value': float(pval)})
pd.DataFrame(spearman_rows).to_csv(os.path.join('salidas','stageI_spearman_nfixed_vs_indices.csv'), index=False)

# Optional: per-bin means of AICc for scatter summary
perbin = df_all.groupby('n_fixed')[INDICES_HEAT].mean().reset_index()
perbin.to_csv(os.path.join('salidas','stageI_indices_by_nfixed.csv'), index=False)

# --- Reproducibility fields: sample sizes per tier and metadata ----------- #
tier_counts_I = df_all.groupby('estim_params').size().rename('count_stageI').reset_index()
tier_counts_II = stage2.groupby('estim_params').size().rename('count_stageII').reset_index()
tier_counts = pd.merge(tier_counts_I, tier_counts_II, on='estim_params', how='outer').fillna(0).astype({'count_stageI':int,'count_stageII':int})
tier_counts.to_csv(os.path.join('salidas','tier_counts_stageI_II.csv'), index=False)

meta = {
    'generated_at': datetime.now().isoformat(),
    'seed': 42,
    'script': 'STEP 2/Análisis Step I y II.py'
}
with open(os.path.join('salidas','reproducibility_meta.json'), 'w', encoding='utf-8') as f:
    json.dump(meta, f, indent=2)

# --- Stage II: retention contributions by criteria ------------------------ #
mask_cc_fail = df_all['CCc'] != 0
mask_i95_fail = df_all['I955'] != 0 if 'I955' in df_all.columns else (df_all['I95'] != 0 if 'I95' in df_all.columns else None)

crit_rows = []
if mask_i95_fail is not None:
    both_fail = (mask_cc_fail & mask_i95_fail).sum()
    only_cc = (mask_cc_fail & ~mask_i95_fail).sum()
    only_i95 = (~mask_cc_fail & mask_i95_fail).sum()
    any_fail = (mask_cc_fail | mask_i95_fail).sum()
    crit_rows.append({'criterion':'CCc_fail','count': int(mask_cc_fail.sum())})
    crit_rows.append({'criterion':'I95_fail','count': int(mask_i95_fail.sum())})
    crit_rows.append({'criterion':'both_fail','count': int(both_fail)})
    crit_rows.append({'criterion':'any_fail','count': int(any_fail)})
else:
    crit_rows.append({'criterion':'CCc_fail','count': int(mask_cc_fail.sum())})
pd.DataFrame(crit_rows).to_csv(os.path.join('salidas','stageII_pruning_contributions.csv'), index=False)

# --- Logistic retention model: P(retained) ~ n_fixed + mu0 + betaG0 + Kie0 -- #
try:
    import statsmodels.api as sm
    X = df_all[['n_fixed','mu0','betaG0','Kie0']].copy().astype(float)
    X = sm.add_constant(X, has_constant='add')
    y = (df_all['stage']=='II').astype(int)
    model = sm.Logit(y, X).fit(disp=False, maxiter=100)
    params = model.params; se = model.bse
    or_df = pd.DataFrame({
        'term': params.index,
        'coef': params.values,
        'OR': np.exp(params.values),
        'OR_CI_low': np.exp(params.values - 1.96*se.values),
        'OR_CI_high': np.exp(params.values + 1.96*se.values),
        'p_value': model.pvalues.values
    })
    or_df.to_csv(os.path.join('salidas','stageII_logistic_OR.csv'), index=False)
except Exception as e:
    with open(os.path.join('salidas','stageII_logistic_OR_ERROR.txt'), 'w') as f:
        f.write(str(e))

# --- Shift in complexity: effect sizes for n_fixed and n_estimated -------- #
def cohens_d_unpaired(x, y):
    x = np.asarray(x); y = np.asarray(y)
    nx, ny = len(x), len(y)
    if nx < 2 or ny < 2:
        return np.nan
    vx = x.var(ddof=1); vy = y.var(ddof=1)
    sp = np.sqrt(((nx-1)*vx + (ny-1)*vy) / (nx+ny-2))
    return (y.mean() - x.mean()) / sp if sp > 0 else np.nan

cd_nfixed = cohens_d_unpaired(nfixed_all, nfixed_sel) if not nfixed_sel.empty else np.nan
cd_nest = cohens_d_unpaired(est_all, est_sel) if not est_sel.empty else np.nan
pd.DataFrame([{'metric':'n_fixed','cohens_d': cd_nfixed},
              {'metric':'n_estimated','cohens_d': cd_nest}]).round(3)\
  .to_csv(os.path.join('salidas','effect_sizes_complexity.csv'), index=False)

# --- PCA diagnostics per tier: variance explained & centroid separation ---- #
pca_diag_rows = []
perm_p_rows = []
# Compute tiers locally to avoid ordering issues
tiers_local = sorted(stage2['estim_params'].unique()) if not stage2.empty else []
for n_par in tiers_local:
    subset_all = df_all[df_all['estim_params']==n_par]
    if len(subset_all) < 5:
        continue
    X = subset_all[INDICES_PCA].astype(float)
    Xs = StandardScaler().fit_transform(X)
    pca = PCA(n_components=2).fit(Xs)
    sc = pca.transform(Xs)
    expl = pca.explained_variance_ratio_*100
    mask_I = (subset_all['stage']=='I').values
    mask_II = (subset_all['stage']=='II').values
    if mask_I.sum()==0 or mask_II.sum()==0:
        continue
    cI = sc[mask_I].mean(axis=0)
    cII = sc[mask_II].mean(axis=0)
    dist = float(np.linalg.norm(cII - cI))
    pca_diag_rows.append({'estim_params': int(n_par), 'pc1_pct': float(expl[0]), 'pc2_pct': float(expl[1]), 'centroid_distance': dist, 'n_I': int(mask_I.sum()), 'n_II': int(mask_II.sum())})

    # permutation test for centroid separation
    n = len(sc); k = mask_II.sum()
    obs = dist
    perms = 500
    ge = 0
    for _ in range(perms):
        idx = rng.choice(n, size=k, replace=False)
        mask_perm = np.zeros(n, dtype=bool); mask_perm[idx] = True
        cA = sc[~mask_perm].mean(axis=0)
        cB = sc[mask_perm].mean(axis=0)
        d = np.linalg.norm(cB - cA)
        if d >= obs:
            ge += 1
    pval = (ge + 1) / (perms + 1)
    perm_p_rows.append({'estim_params': int(n_par), 'p_perm_centroid_separation': float(pval)})

pd.DataFrame(pca_diag_rows).round(3).to_csv(os.path.join('salidas','pca_diagnostics_by_tier.csv'), index=False)
pd.DataFrame(perm_p_rows).round(4).to_csv(os.path.join('salidas','pca_permutation_pvalues.csv'), index=False)

# --- Δ-index robustness (Stage II overall): bootstrap CI + FDR ------------ #
def bh_fdr(pvals):
    m = len(pvals)
    order = np.argsort(pvals)
    ranked_p = np.array(pvals)[order]
    q = np.empty(m)
    prev = 1.0
    for i in range(m-1, -1, -1):
        q_i = ranked_p[i] * m / (i+1)
        prev = min(prev, q_i)
        q[i] = prev
    q_full = np.empty(m)
    q_full[order] = np.clip(q, 0, 1)
    return q_full

delta_rows = []
pvals = []
keys = []
boot_ci_low = {}
boot_ci_high = {}

for p in PARAM_COLS:
    fixed = stage2[stage2[p]==1][INDICES_HEAT].astype(float)
    free  = stage2[stage2[p]==0][INDICES_HEAT].astype(float)
    for idx in INDICES_HEAT:
        if free.empty or fixed.empty:
            d = np.nan; pval = np.nan; ci_low = np.nan; ci_high = np.nan
        else:
            d = 100*(fixed[idx].mean() - free[idx].mean())/ (free[idx].mean() if free[idx].mean()!=0 else np.nan)
            # Welch t-test
            _, pval = ttest_ind(fixed[idx].values, free[idx].values, equal_var=False, nan_policy='omit')
            # bootstrap CI
            B = 1000
            diffs = []
            fx = fixed[idx].dropna().values; fr = free[idx].dropna().values
            nfx, nfr = len(fx), len(fr)
            if nfx>1 and nfr>1:
                for _ in range(B):
                    sfx = fx[rng.integers(0, nfx, nfx)]
                    sfr = fr[rng.integers(0, nfr, nfr)]
                    mfx = sfx.mean(); mfr = sfr.mean()
                    diffs.append(100*(mfx - mfr)/(mfr if mfr!=0 else np.nan))
                ci_low = float(np.nanpercentile(diffs, 2.5))
                ci_high = float(np.nanpercentile(diffs, 97.5))
            else:
                ci_low = np.nan; ci_high = np.nan
        delta_rows.append({'param': p, 'index': idx, 'delta_pct': float(d) if np.isfinite(d) else np.nan,
                           'ci_low': ci_low, 'ci_high': ci_high, 'p_value': float(pval) if np.isfinite(pval) else np.nan})
        pvals.append(np.nan if not np.isfinite(pval) else float(pval))
        keys.append((p, idx))

delta_df = pd.DataFrame(delta_rows)

# FDR adjustment
valid_mask = np.isfinite(delta_df['p_value'].values)
adj = np.full(len(delta_df), np.nan)
if valid_mask.any():
    adj_vals = bh_fdr(delta_df.loc[valid_mask, 'p_value'].values)
    adj[valid_mask] = adj_vals
delta_df['q_value'] = adj
delta_df.to_csv(os.path.join('salidas','delta_index_bootstrap_fdr.csv'), index=False)

# Top 5 beneficial/costly fixations per index (beneficial = delta<0 for Akaike/MeanCC/Fobj)
rank_rows = []
for idx in INDICES_HEAT:
    sub = delta_df[delta_df['index']==idx]
    top_benefit = sub.sort_values('delta_pct', ascending=True).head(5)
    top_costly  = sub.sort_values('delta_pct', ascending=False).head(5)
    for _, r in top_benefit.iterrows():
        rank_rows.append({'index': idx, 'type':'beneficial', 'param': r['param'], 'delta_pct': r['delta_pct'], 'q_value': r['q_value']})
    for _, r in top_costly.iterrows():
        rank_rows.append({'index': idx, 'type':'costly', 'param': r['param'], 'delta_pct': r['delta_pct'], 'q_value': r['q_value']})
pd.DataFrame(rank_rows).to_csv(os.path.join('salidas','delta_index_top5_rankings.csv'), index=False)

# --- Operational proxy: search-space reduction note ----------------------- #
with open(os.path.join('salidas','operational_proxy_note.txt'), 'w') as f:
    f.write('Proxy for search-space reduction: average reduction in free parameters (Stage I -> Stage II) = ')
    f.write(str(round(stats['avg_complexity_reduction_mean_pars'],3)))
    f.write('\nParameter bounds not provided in dataset; product-of-bounds proxy not computed.')

# ========================================================================== #
# 2quater. PERSISTENCE BY HIPPO DEPTH (ALLUVIAL + HEATMAP)                  #
# ========================================================================== #
# We use n_fixed as a proxy for HIPPO tree depth d. For each depth and parameter,
# compute the fraction of structures where the parameter remains free (not fixed).
depth_levels = sorted(df_all['n_fixed'].unique())
depth_counts = df_all.groupby('n_fixed').size().rename('N_depth').reset_index()
depth_counts.to_csv(os.path.join('salidas','depth_sample_sizes.csv'), index=False)

# Raw free fractions per depth and parameter
persist_records = []
for d in depth_levels:
    subset = df_all[df_all['n_fixed']==d]
    N = len(subset)
    if N == 0:
        continue
    for p in PARAM_COLS:
        # In the dataset, 1= fixed, 0 = free (estimated)
        free_frac = float((subset[p]==0).mean())
        persist_records.append({'depth': int(d), 'param': p, 'free_frac': free_frac, 'N': N})

persist_df = pd.DataFrame(persist_records)

# Enforce monotonic non-increasing free fraction with depth for each parameter
persist_df = persist_df.sort_values(['param','depth'])
persist_df['free_frac_mono'] = persist_df.groupby('param')['free_frac']\
    .cummin()  # non-increasing across depth
persist_pivot = persist_df.pivot(index='param', columns='depth', values='free_frac_mono')
pivot_pct = (persist_pivot*100).round(1)
new_index = [param_labels.get(p, p) for p in pivot_pct.index]
pivot_pct = pivot_pct.set_axis(new_index, axis=0)
pivot_pct.to_csv(os.path.join('salidas','persistence_heatmap_free_pct.csv'))

# Plot heatmap (parameters x depth) of free fraction (%)
figH, axHmap = plt.subplots(figsize=(max(8, len(depth_levels)*0.6), max(5, len(PARAM_COLS)*0.45)))
sns.heatmap(pivot_pct, cmap='Blues', vmin=0, vmax=100, annot=False, cbar_kws={'label':'Free fraction (%)'}, ax=axHmap)
axHmap.set_xlabel('Depth (n_fixed)')
axHmap.set_ylabel('Parameter')
axHmap.set_title('Persistence heatmap (free fraction by depth)')
figH.tight_layout()
os.makedirs(os.path.join('salidas','figs'), exist_ok=True)
figH.savefig(os.path.join('salidas','figs','persistence_heatmap.png'), dpi=350)
plt.close(figH)

# Global alluvial-style stacked area: average free vs fixed across parameters
avg_free_by_depth = persist_df.groupby('depth')['free_frac_mono'].mean().reindex(depth_levels).ffill()
avg_fixed_by_depth = 1.0 - avg_free_by_depth
alluvial_df = pd.DataFrame({
    'depth': depth_levels,
    'avg_free': avg_free_by_depth.values,
    'avg_fixed': avg_fixed_by_depth.values
})
alluvial_df.to_csv(os.path.join('salidas','persistence_alluvial_global.csv'), index=False)

figA, axA2 = plt.subplots(figsize=(max(8, len(depth_levels)*0.6), 4))
axA2.stackplot(alluvial_df['depth'], alluvial_df['avg_free'], alluvial_df['avg_fixed'],
               labels=['Estimated (free)','Fixed'], colors=[PAL_BLUE, PAL_GRAY], alpha=0.9)
axA2.set_xlim(min(depth_levels), max(depth_levels))
axA2.set_ylim(0,1)
axA2.set_xlabel('Depth (n_fixed)')
axA2.set_ylabel('Average fraction across parameters')
axA2.set_title('Alluvial-style flow of free vs fixed across depth (global)')
axA2.legend(loc='upper right')
figA.tight_layout()
figA.savefig(os.path.join('salidas','figs','persistence_alluvial_global.png'), dpi=350)
plt.close(figA)

# --- Faceted stacked areas by parameter (Option A) ------------------------ #
order_means = persist_df.groupby('param')['free_frac_mono'].mean().sort_values(ascending=False)
order_csv = order_means.rename('mean_free_frac').reset_index()
order_csv['label'] = order_csv['param'].map(param_labels)
order_csv.to_csv(os.path.join('salidas','persistence_facets_order.csv'), index=False)

n_params = len(order_means)
ncols = 4
nrows = int(np.ceil(n_params / ncols)) if n_params>0 else 1
figF, axesF = plt.subplots(nrows, ncols, figsize=(ncols*4.0, nrows*2.8), sharex=True, sharey=True)
axesF = np.atleast_2d(axesF)

for idx_p, p in enumerate(order_means.index):
    r = idx_p // ncols; c = idx_p % ncols
    ax = axesF[r, c]
    ser = persist_df[persist_df['param']==p].set_index('depth')['free_frac_mono']
    ser = ser.reindex(depth_levels).ffill().bfill()
    free = ser.values
    fixed = 1.0 - free
    ax.stackplot(depth_levels, free, fixed, labels=['Free','Fixed'], colors=[PAL_BLUE, PAL_GRAY], alpha=0.95)
    ax.set_title(param_labels.get(p, p))
    ax.set_ylim(0,1)
    ax.grid(alpha=0.2)
    if r == nrows-1:
        ax.set_xlabel('Depth (n_fixed)')
    if c == 0:
        ax.set_ylabel('Fraction')

# Hide any unused axes
for k in range(n_params, nrows*ncols):
    r = k // ncols; c = k % ncols
    figF.delaxes(axesF[r, c])

figF.suptitle('Parameter-wise persistence across depth (stacked areas)', y=1.02, fontsize=12)
figF.tight_layout()
figF.savefig(os.path.join('salidas','figs','persistence_facets.png'), dpi=350, bbox_inches='tight')
plt.close(figF)



# ========================================================================== #
# 3. FIGURE 2 – Complexity-stratified grid (FixFreq | PCA | Heat-map)         #
# ========================================================================== #
tiers = sorted(stage2['estim_params'].unique(), reverse=True)
n_rows = len(tiers)
fig2, axes = plt.subplots(n_rows, 3, figsize=(18, 4.5*n_rows),
                          gridspec_kw={'hspace':0.35,'wspace':0.28})
if n_rows == 1:
    axes = axes.reshape(1,3)

freq_all = (df_all[PARAM_COLS]==1).mean()*100

for r, n_par in enumerate(tiers):
    subset_all = df_all[df_all['estim_params']==n_par]
    subset_sel = subset_all[subset_all['stage']=='II']

    # -- (A) Fixation frequency ---------------------------------------------- #
    axF = axes[r,0]
    freq_sel = (subset_sel[PARAM_COLS]==1).mean()*100
    x = np.arange(TOTAL_PARAMS); barw = 0.35
    axF.bar(x-barw/2, freq_all, width=barw,
            color=PAL_GRAY, alpha=0.35, label='Stage I models')
    axF.bar(x+barw/2, freq_sel, width=barw,
            color=PAL_BLUE, alpha=0.85, label='Stage II models')
    axF.set_xticks(x); 
    axF.set_xticklabels([param_labels[p] for p in PARAM_COLS], rotation=90)
    axF.set_ylabel('% fixed'); axF.set_ylim(0,100)
    if r == 0:
        axF.legend(loc='upper right')
    axF.set_title(f'(A) FixFreq – {n_par} pars')

    # -- (B) PCA biplot ------------------------------------------------------- #
    axP = axes[r,1]
    X = subset_all[INDICES_PCA].astype(float)
    Xs = StandardScaler().fit_transform(X)
    pca = PCA(n_components=2).fit(Xs)
    sc  = pca.transform(Xs)
    expl = pca.explained_variance_ratio_*100

    # plot unselected vs selected
    mask_I  = subset_all['stage']=='I'
    mask_II = subset_all['stage']=='II'
    axP.scatter(sc[mask_I,0], sc[mask_I,1],
                color=PAL_GRAY, alpha=0.4, s=35)
    axP.scatter(sc[mask_II,0], sc[mask_II,1],
                color=PAL_BLUE, alpha=0.85, s=35)

    # bold index vectors
    for var, vec in zip(INDICES_PCA, pca.components_.T):
        axP.arrow(0, 0, vec[0]*3, vec[1]*3,
                  head_width=0.08, head_length=0.12,
                  color=PAL_3, linewidth=1)
        axP.text(vec[0]*3.4, vec[1]*3.4, var,
                 fontsize=8, color=PAL_3,fontweight='bold')

    # parameter vectors: thin black lines, full opacity, longer
    for p in PARAM_COLS:
        v = subset_all[p].values
        z = (v - v.mean()) / v.std(ddof=0)
        corr1 = np.corrcoef(z, sc[:,0])[0,1]
        corr2 = np.corrcoef(z, sc[:,1])[0,1]
        scale = 5  # increase length
        axP.arrow(0, 0, corr1*scale, corr2*scale,
                  head_width=0.04, head_length=0.06,
                  color='black', linewidth=0.5, alpha = 0.8)
        axP.text(corr1*scale*1.1, corr2*scale*1.1, param_labels[p],
                 fontsize=7, alpha=1.0, color='black', fontweight = 'bold')

    axP.set_xlabel(f'PC1 ({expl[0]:.1f}%)')
    axP.set_ylabel(f'PC2 ({expl[1]:.1f}%)')
    axP.set_title(f'(B) PCA – {n_par} pars')

    # -- (C) Heat-map (%Δ Index) – filtered models only ---------------------- #
    axH = axes[r,2]
    delta = {}
    for p in PARAM_COLS:
        fixed = subset_sel[subset_sel[p]==1][INDICES_HEAT]
        free  = subset_sel[subset_sel[p]==0][INDICES_HEAT]
        if free.empty:
            delta[p] = pd.Series([np.nan]*len(INDICES_HEAT), index=INDICES_HEAT)
        else:
            delta[p] = 100*(fixed.mean() - free.mean()).div(free.mean().replace(0, np.nan))
    heat_df = pd.DataFrame(delta).T[INDICES_HEAT].round(1)

    sns.heatmap(heat_df, cmap='vlag', center=0, robust=True,
                xticklabels=INDICES_HEAT, yticklabels=[param_labels[p] for p in PARAM_COLS],
                annot=True, fmt='.1f', annot_kws={'size':7},
                ax=axH)
    axH.set_title(f'(C) ΔIndex (%) – {n_par} pars')

fig2.tight_layout()
fig2.savefig('figure2_complexity_grid.png', dpi=350)

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

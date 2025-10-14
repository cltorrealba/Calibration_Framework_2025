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
    if count > 0:
        center = left + width/2
        axA.text(center, count + 0.3, f'{int(count)}',
                 ha='center', va='bottom', fontsize=8, color='black')

# filtered pool
bins2 = bins + 0.2
counts2, edges2, _ = axA.hist(
    stage2['n_fixed'], bins=bins2,
    color=PAL_BLUE, alpha=0.85, width=0.45, label='Stage II models'
)
for count, left in zip(counts2, edges2[:-1]):
    if count > 0:
        center = left + width/2
        axA.text(center, count + 0.6, f'{int(count)}',
                 ha='center', va='bottom', fontsize=8, color=PAL_BLUE)

axA.set_xlabel('Number of Fixed Parameters')
axA.set_ylabel('Count')
axA.set_title('Fixed-parameter distribution')
axA.legend()
fig1.tight_layout()
fig1.savefig('figure1_histogram_fixed.png', dpi=350)


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

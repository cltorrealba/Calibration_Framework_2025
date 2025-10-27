# -*- coding: utf-8 -*-
"""
Stage III – Full-scale calibration & robustness exploration
(final tweaks: PCA label offset and heatmap highlight for model 1750)

Created on Thu May  8 18:45:00 2025
Author : Cristóbal L. Torrealba V.
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
from sklearn.linear_model import ElasticNetCV, ElasticNet
from sklearn.model_selection import KFold
from pandas.plotting import parallel_coordinates
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
import os
import json
from itertools import combinations
from scipy.stats import fisher_exact
from datetime import datetime
import re

sns.set_theme(style="whitegrid")
PAL_GRAY = sns.color_palette("colorblind")[7]
PAL_BLUE = sns.color_palette("colorblind")[0]
PAL_GRN  = sns.color_palette("colorblind")[2]
PAL_ORN  = sns.color_palette("colorblind")[5]  # highlight color

# ========================================================================== #
# 1. LOAD & PREPARE DATA                                                    #
# ========================================================================== #
FP_STRUCT = (
    r"C:/Users/ctorrealba/OneDrive - Viña Concha y Toro S.A/Documentos/Doctorado/"
    r"Artículos/Artículo - Estimación/Codes/STEP 2/HIPPO_result.xlsx"
)
FP_ROBUST = (
    r"C:/Users/ctorrealba/OneDrive - Viña Concha y Toro S.A/Documentos/Doctorado/"
    r"Artículos/Artículo - Estimación/Codes/STEP 3/Zenteno_Final_2023b_WS.xlsx"
)

PARAM_COLS = ["mu0","betaG0","betaF0","Kn0","Kg0","Kf0",
              "Kig0","Kie0","Yxn","Yxg","Yxf","Yeg","Yef"]
param_labels = {
    "mu0": r"$\mu_0$", "betaG0": r"$\beta_{G0}$",
    "betaF0": r"$\beta_{F0}$","Kn0": r"$K_{n0}$",
    "Kg0": r"$K_{g0}$","Kf0": r"$K_{f0}$",
    "Kig0": r"$K_{ig0}$","Kie0": r"$K_{ie0}$",
    "Yxn": r"$Y_{xn}$","Yxg": r"$Y_{xg}$",
    "Yxf": r"$Y_{xf}$","Yeg": r"$Y_{eg}$",
    "Yef": r"$Y_{ef}$",
}
ROBUST_COLS = ["AICc","MNCI","RSQ2","GSS"]

# read
df_struct = pd.read_excel(FP_STRUCT, sheet_name="Sheet1")
df_robust = pd.read_excel(FP_ROBUST, sheet_name="Sheet1")
mask_viable = (df_struct["CCc"]==0)&(df_struct["I955"]==0)
dfM = (
    df_struct.loc[mask_viable, ["FFF"]+PARAM_COLS]
    .merge(df_robust[["FFF"]+ROBUST_COLS], on="FFF")
)
dfM["estim_params"] = (dfM[PARAM_COLS]==0).sum(axis=1)
dfM["n_fixed"]      = (dfM[PARAM_COLS]==1).sum(axis=1)
TOTAL_PARAMS = len(PARAM_COLS)
q75 = dfM["RSQ2"].dropna().quantile(0.75)

# Output directory (local to this script folder)
OUT_DIR = os.path.join(os.path.dirname(__file__), 'salidas')
os.makedirs(OUT_DIR, exist_ok=True)
with open(os.path.join(OUT_DIR, 'rsq_thresholds.json'), 'w', encoding='utf-8') as f:
    json.dump({"RSQ2_q75_global": float(q75), "generated_at": datetime.now().isoformat()}, f, indent=2)

# LaTeX-friendly PDF export settings and figures directory
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42
OUT_FIGS = os.path.join(OUT_DIR, 'figs')
os.makedirs(OUT_FIGS, exist_ok=True)

# -------------------------------------------------------------------------- #
# ElasticNetCV + manual CV for CIs                                          #
# -------------------------------------------------------------------------- #
X = dfM[PARAM_COLS].astype(float).to_numpy()
kf = KFold(n_splits=10, shuffle=False)
en_coefs = {}
for metric in ROBUST_COLS:
    y = dfM[metric].to_numpy()
    encv = ElasticNetCV(l1_ratio=[.1,.5,.9,1], cv=10, max_iter=5000).fit(X,y)
    alpha = float(getattr(encv, 'alpha_', 1.0))
    l1 = float(getattr(encv, 'l1_ratio_', 1.0))
    coefs = []
    for tr, _ in kf.split(X):
        en = ElasticNet(alpha=alpha, l1_ratio=l1, max_iter=5000)
        en.fit(X[tr], y[tr]); coefs.append(en.coef_)
    coefs = np.vstack(coefs)
    mean = coefs.mean(axis=0)
    lo, hi = np.percentile(coefs, [2.5,97.5], axis=0)
    en_coefs[metric] = pd.DataFrame({
        "param": PARAM_COLS,
        "coef": mean,
        "ci_lo": lo,
        "ci_hi": hi
    })

# ========================================================================== #
# 2. FIGURE 1 – Histogram (# fixed)                                           #
# ========================================================================== #
fig1, ax1 = plt.subplots(figsize=(6,4))
mn,mx = dfM["n_fixed"].min(), dfM["n_fixed"].max()
bins = np.arange(mn-0.5, mx+1.5, 1)
cnt_all, edges, _ = ax1.hist(dfM["n_fixed"], bins=bins,
    color=PAL_GRAY, alpha=0.35, width=0.45, label="All viable")
cnt_top, _, _ = ax1.hist(dfM.loc[dfM["RSQ2"]>=q75,"n_fixed"],
    bins=bins+0.2, color=PAL_BLUE, alpha=0.85, width=0.45,
    label="Top-quartile models")
for c,e in zip(cnt_all, edges[:-1]):
    cf = float(c)
    if cf>0: ax1.text(e+0.25, cf+0.3, f"{int(cf)}", ha="center", fontsize=8)
for c,e in zip(cnt_top, edges[:-1]):
    cf = float(c)
    if cf>0: ax1.text(e+0.45, cf+0.6, f"{int(cf)}",
        ha="center", fontsize=8, color=PAL_BLUE)
ax1.set_xticks(np.arange(mn, mx+1))
ax1.set_xticklabels(np.arange(mn, mx+1))
ax1.set_xlabel("Number of Fixed Parameters")
ax1.set_ylabel("Count")
ax1.set_title("Stage III – fixed-parameter distribution")
ax1.legend(); fig1.tight_layout()
fig1.savefig("stage3_Fig1_hist_fixed.png", dpi=300)

# ========================================================================== #
# 3. FIGURE 2 – FixFreq | PCA/Parallel | Δ-Index grid                         #
#    Drop tiers with <2 top models and exclude tiers with 9 and 3 free params #
#    Use compact per-row height for manuscript sizing                         #
# ========================================================================== #
tiers_all = sorted(dfM["estim_params"].unique(), reverse=True)
tiers = [
    n for n in tiers_all
    if (n not in {9, 3}) and (dfM[(dfM["estim_params"]==n) & (dfM["RSQ2"]>=q75)].shape[0] >= 2)
]
n_rows = len(tiers)
ROW_H = 3.8  # compact row height (inches per row)
fig2, axes = plt.subplots(n_rows, 3, figsize=(18, ROW_H * n_rows),
    gridspec_kw={"hspace":0.35, "wspace":0.28})
if n_rows==1: axes=axes.reshape(1,3)
freq_pool = (dfM[PARAM_COLS]==1).mean()*100

# collect exact heatmap values (mean-based Δ%) across tiers for CSV export
heatmap_rows = []

for r,n_par in enumerate(tiers):
    sub = dfM[dfM["estim_params"]==n_par].copy()
    sel = sub["RSQ2"]>=q75
    # A: FixFreq
    axF=axes[r,0]; x=np.arange(TOTAL_PARAMS); bw=0.35
    axF.bar(x-bw/2, freq_pool, width=bw, color=PAL_GRAY, alpha=0.35, label="All")
    axF.bar(x+bw/2, (sub.loc[sel,PARAM_COLS]==1).mean()*100,
            width=bw, color=PAL_BLUE, alpha=0.85, label="Top")
    axF.set_xticks(x); axF.set_xticklabels([param_labels[p] for p in PARAM_COLS], rotation=90)
    axF.set_ylabel("% fixed"); axF.set_ylim(0,100)
    if r==0: axF.legend(loc="upper right", fontsize=9)
    axF.set_title(f"(A) FixFreq – {n_par} free")

    # B: PCA / parallel + bold offset label for model 1750
    axP=axes[r,1]
    if len(sub)<3:
        df_pc=sub[ROBUST_COLS].copy()
        df_pc["AICc"]*=-1; df_pc["MNCI"]*=-1
        df_pc["model"]=sub["FFF"].astype(str)
        parallel_coordinates(df_pc, "model", cols=ROBUST_COLS,
            color=[PAL_GRAY,PAL_BLUE][:len(df_pc)], alpha=0.85, ax=axP)
        axP.set_title(f"(B) Profiles – {n_par} free")
        axP.legend([],[],frameon=False)
    else:
        X=sub[ROBUST_COLS].copy(); X["AICc"]*=-1; X["MNCI"]*=-1
        scs= StandardScaler().fit_transform(X)
        pca=PCA(2).fit(scs)
        sc= pca.transform(scs); expl=pca.explained_variance_ratio_*100

        axP.scatter(sc[:,0],sc[:,1],c=PAL_GRAY,alpha=0.4,s=35)
        axP.scatter(sc[sel,0],sc[sel,1],c=PAL_BLUE,alpha=0.85,s=35)

        # highlight model 1750 with a star marker, same color logic
        idx = sub.index[sub["FFF"] == 1750].tolist()
        if idx:
            i = idx[0]
            col = PAL_BLUE if bool(sel.loc[i]) else PAL_GRAY
            # compute offsets if you still want to place a label; here we just plot a star
            axP.scatter(
                sc[i, 0], sc[i, 1],
                marker="*",        # star shape
                s=200,             # size (adjust as needed)
                color=col,         # fill color
                edgecolor="black", # black border
                linewidth=0.8,
                zorder=5
            )

        for v,vec in zip(ROBUST_COLS,pca.components_.T):
            axP.arrow(0,0,vec[0]*3,vec[1]*3,head_width=0.09,head_length=0.13,
                      color=PAL_GRN,linewidth=1.1)
            axP.text(vec[0]*3.4,vec[1]*3.4,v,color=PAL_GRN,fontsize=8,fontweight="bold")

        for p in PARAM_COLS:
            v=sub[p].values; std=v.std(ddof=0)
            if std<=0 or np.isnan(std): continue
            z=(v-v.mean())/std
            c1,c2=np.corrcoef(z,sc[:,0])[0,1],np.corrcoef(z,sc[:,1])[0,1]
            axP.arrow(0,0,c1*5,c2*5,head_width=0.04,head_length=0.06,
                      color="black",linewidth=0.5,alpha=0.9)
            axP.text(c1*5*1.1,c2*5*1.1,param_labels[p],fontsize=7,color="black")

        axP.set_xlabel(f"PC1 ({expl[0]:.1f}%)")
        axP.set_ylabel(f"PC2 ({expl[1]:.1f}%)")
        axP.set_title(f"(B) PCA – {n_par} free")

    # C: Δ-Index heatmap
    axH=axes[r,2]
    delta={}
    for p in PARAM_COLS:
        f=sub.loc[sub[p]==1,ROBUST_COLS]
        fr=sub.loc[sub[p]==0,ROBUST_COLS]
        delta[p]=(100*(f.mean()-fr.mean())/fr.mean()).fillna(np.nan)
    heat_df=pd.DataFrame(delta).T[ROBUST_COLS].round(1)

    # export per-tier heatmap values and accumulate for consolidated CSV
    try:
        tier_csv = os.path.join(OUT_DIR, f'complexity_grid_heatmap_tier{n_par}.csv')
        heat_df.to_csv(tier_csv, index_label='param')
    except Exception:
        pass
    for idx in ROBUST_COLS:
        for p in heat_df.index:
            try:
                val = float(heat_df.loc[p, idx])
            except Exception:
                val = float('nan')
            heatmap_rows.append({
                'estim_params': int(n_par),
                'param': p,
                'index': idx,
                'delta_mean_pct': val
            })
    sns.heatmap(heat_df, cmap="vlag", center=0, robust=True,
                xticklabels=ROBUST_COLS,
                yticklabels=[param_labels[p] for p in PARAM_COLS],
                annot=True, fmt=".1f", annot_kws={"size":7},
                linewidths=0.5, linecolor="gray", ax=axH)
    axH.set_title(f"(C) Δ-Index (%) – {n_par} free")

# write consolidated CSV for all tiers with exact heatmap values
try:
    if heatmap_rows:
        pd.DataFrame(heatmap_rows).to_csv(os.path.join(OUT_DIR, 'complexity_grid_heatmap_values.csv'), index=False)
except Exception:
    pass

fig2.tight_layout()
# Save PNG and LaTeX-ready PDF into salidas/figs with fallback if locked
png_path = os.path.join(OUT_FIGS, "stage3_Fig2_complexity_grid.png")
fig2.savefig(png_path, dpi=300)
pdf_path = os.path.join(OUT_FIGS, "stage3_Fig2_complexity_grid.pdf")
try:
    fig2.savefig(pdf_path, dpi=300, bbox_inches='tight')
except PermissionError:
    alt_pdf_path = os.path.join(OUT_FIGS, "stage3_Fig2_complexity_grid_alt.pdf")
    fig2.savefig(alt_pdf_path, dpi=300, bbox_inches='tight')

# ========================================================================== #
# 4. FIGURE 3 – Fixation heatmap with model-1750 highlight & legend           #
# ========================================================================== #
fig3, ax3 = plt.subplots(figsize=(8,10))
heat = dfM.set_index("FFF")[PARAM_COLS].astype(int)
maskT = dfM.set_index("FFF")["RSQ2"]>=q75
h2 = heat.where(heat==0, 1)          # 0 free, 1 fixed
h2.loc[maskT, :] = h2.loc[maskT, :].replace({1:2})  # 2 fixed top
# now override only fixed params of 1750 => 3
if 1750 in h2.index:
    fixed_params = dfM.loc[dfM["FFF"]==1750, PARAM_COLS].iloc[0] == 1
    for p, is_fixed in fixed_params.items():
        if is_fixed:
            h2.loc[[1750], [p]] = 3
cmap = ListedColormap(["white","lightgray",PAL_BLUE,PAL_ORN])
sns.heatmap(h2, cmap=cmap, linewidths=0.5, linecolor="gray",
            cbar=False, ax=ax3)
ax3.set_ylabel("Model ID"); ax3.set_xlabel("Parameters"); ax3.set_yticks([])

legend_patches = [
    Patch(facecolor="white", edgecolor="gray", label="Free"),
    Patch(facecolor="lightgray", edgecolor="gray", label="Fixed, non-top"),
    Patch(facecolor=PAL_BLUE, edgecolor="gray", label="Fixed, top-quartile"),
    Patch(facecolor=PAL_ORN, edgecolor="gray", label="Model 1750"),
]
ax3.legend(handles=legend_patches, loc="upper right", frameon=False)
fig3.tight_layout()
fig3.savefig("stage3_Fig3_fixation_heatmap.png", dpi=300)

# ========================================================================== #
# 5. FIGURE 4 – ElasticNet coefficients with 95% CI (1×4 layout)             #
# ========================================================================== #
fig4, axs4 = plt.subplots(1, len(ROBUST_COLS), figsize=(16,6), sharey=True)
for i,metric in enumerate(ROBUST_COLS):
    dfc = en_coefs[metric]
    axs4[i].barh(dfc["param"], dfc["coef"],
                 xerr=[dfc["coef"]-dfc["ci_lo"], dfc["ci_hi"]-dfc["coef"]],
                 color=PAL_BLUE, alpha=0.8)
    axs4[i].axvline(0, color="k", linewidth=0.7)
    if i==0: axs4[i].set_ylabel("Parameters")
    axs4[i].set_title(metric)
    axs4[i].set_xlabel("Coefficient ±95% CI")
    axs4[i].grid(axis="x", linestyle="--", alpha=0.5)
fig4.tight_layout()
fig4.savefig("stage3_Fig4_elasticnet_CI.png", dpi=300)

# ========================================================================== #
# 6. INDICATORS & TABLES FOR RESULTS (3.3)                                   #
# ========================================================================== #

# (i) Tier sizes and RSQ threshold (global and per tier)
rows = []
for n_par in sorted(dfM['estim_params'].unique()):
    sub = dfM[dfM['estim_params']==n_par]
    cnt_total = int(len(sub))
    cnt_top = int((sub['RSQ2']>=q75).sum())
    q75_tier = float(sub['RSQ2'].quantile(0.75)) if cnt_total>0 else float('nan')
    rows.append({
        'estim_params': int(n_par),
        'count_total': cnt_total,
        'count_top_q75_global': cnt_top,
        'RSQ2_q75_global': float(q75),
        'RSQ2_q75_tier': q75_tier
    })
pd.DataFrame(rows).to_csv(os.path.join(OUT_DIR, 'tier_sizes_and_thresholds.csv'), index=False)

# (ii) PCA diagnostics per tier: variance explained & centroid separation (Top vs Rest)
pca_diag = []
perm_pvals = []
rng = np.random.default_rng(42)
for n_par in sorted(dfM['estim_params'].unique(), reverse=True):
    sub = dfM[dfM['estim_params']==n_par]
    if len(sub) < 3:
        continue
    X = sub[ROBUST_COLS].copy()
    X['AICc'] *= -1; X['MNCI'] *= -1
    Xs = StandardScaler().fit_transform(X)
    pca = PCA(2).fit(Xs)
    sc = pca.transform(Xs)
    expl = pca.explained_variance_ratio_*100
    mask_top = (sub['RSQ2']>=q75).values
    if mask_top.sum()==0 or (~mask_top).sum()==0:
        continue
    c_top = sc[mask_top].mean(axis=0)
    c_rest = sc[~mask_top].mean(axis=0)
    dist = float(np.linalg.norm(c_top - c_rest))
    pca_diag.append({'estim_params': int(n_par), 'pc1_pct': float(expl[0]), 'pc2_pct': float(expl[1]), 'centroid_distance': dist, 'n_top': int(mask_top.sum()), 'n_rest': int((~mask_top).sum())})
    # permutation test
    n = len(sc); k = mask_top.sum(); obs = dist; ge=0; perms=500
    for _ in range(perms):
        idx = rng.choice(n, size=k, replace=False)
        m = np.zeros(n, dtype=bool); m[idx] = True
        cA = sc[m].mean(axis=0); cB = sc[~m].mean(axis=0)
        d = np.linalg.norm(cA - cB)
        if d >= obs: ge += 1
    pval = (ge+1)/(perms+1)
    perm_pvals.append({'estim_params': int(n_par), 'p_perm_centroid_separation': float(pval)})

pd.DataFrame(pca_diag).round(3).to_csv(os.path.join(OUT_DIR, 'pca_diagnostics_top_vs_rest.csv'), index=False)
pd.DataFrame(perm_pvals).round(4).to_csv(os.path.join(OUT_DIR, 'pca_perm_pvalues_top_vs_rest.csv'), index=False)

# (iii) Delta-Index summaries: median [IQR] per parameter/index with bootstrap 95% CIs
def bootstrap_delta_median(fixed_vals, free_vals, B=1000):
    fixed_vals = np.asarray(fixed_vals); free_vals = np.asarray(free_vals)
    if len(fixed_vals)<2 or len(free_vals)<2:
        return np.nan, np.nan, np.nan
    deltas = []
    nfx, nfr = len(fixed_vals), len(free_vals)
    for _ in range(B):
        sfx = fixed_vals[rng.integers(0,nfx,nfx)]
        sfr = free_vals[rng.integers(0,nfr,nfr)]
        med_fx = np.nanmedian(sfx); med_fr = np.nanmedian(sfr)
        d = 100*(med_fx - med_fr)/(med_fr if med_fr!=0 else np.nan)
        deltas.append(d)
    deltas = np.array(deltas)
    return float(np.nanmedian(deltas)), float(np.nanpercentile(deltas,25)), float(np.nanpercentile(deltas,75))

delta_rows = []
for n_par in sorted(dfM['estim_params'].unique(), reverse=True):
    sub = dfM[dfM['estim_params']==n_par]
    for p in PARAM_COLS:
        fx_mask = sub[p]==1; fr_mask = sub[p]==0
        for idx in ROBUST_COLS:
            fx = sub.loc[fx_mask, idx].dropna().values
            fr = sub.loc[fr_mask, idx].dropna().values
            med, q1, q3 = bootstrap_delta_median(fx, fr, B=1000)
            # CI 95% from bootstrap distribution quantiles (2.5,97.5)
            # recompute quick distribution for CI
            ci_lo = np.nan; ci_hi = np.nan
            if len(fx)>=2 and len(fr)>=2:
                B=500
                ds=[]
                nfx,nfr=len(fx),len(fr)
                for _ in range(B):
                    sfx=fx[rng.integers(0,nfx,nfx)]; sfr=fr[rng.integers(0,nfr,nfr)]
                    d=100*(np.nanmedian(sfx)-np.nanmedian(sfr))/(np.nanmedian(sfr) if np.nanmedian(sfr)!=0 else np.nan)
                    ds.append(d)
                ci_lo=float(np.nanpercentile(ds,2.5)); ci_hi=float(np.nanpercentile(ds,97.5))
            delta_rows.append({'estim_params': int(n_par), 'param': p, 'index': idx, 'delta_median_pct': med, 'delta_iqr25_pct': q1, 'delta_iqr75_pct': q3, 'ci_low': ci_lo, 'ci_high': ci_hi, 'n_fixed_grp': int(fx_mask.sum()), 'n_free_grp': int(fr_mask.sum())})
pd.DataFrame(delta_rows).round(3).to_csv(os.path.join(OUT_DIR, 'delta_index_median_iqr_by_tier.csv'), index=False)

# (iv) Co-fixation enrichment (pairs): over-representation in top quartile
mask_top_all = dfM['RSQ2']>=q75
N_top = int(mask_top_all.sum()); N_rest = int((~mask_top_all).sum())
pair_rows = []
for p1, p2 in combinations(PARAM_COLS, 2):
    motif = (dfM[p1]==1) & (dfM[p2]==1)
    a = int((motif & mask_top_all).sum())
    b = int(motif.sum() - a)
    c = int(N_top - a)
    d = int(N_rest - b)
    # enrichment ratio (top vs rest)
    freq_top = a / N_top if N_top>0 else np.nan
    freq_rest = b / N_rest if N_rest>0 else np.nan
    enr = (freq_top / freq_rest) if (freq_top==freq_top and freq_rest and freq_rest>0) else np.nan
    # Fisher exact
    try:
        _, pval = fisher_exact([[a,c],[b,d]], alternative='greater')
    except Exception:
        pval = np.nan
    pair_rows.append({'pair': f'{p1}+{p2}', 'count_top': a, 'count_rest': b, 'N_top': N_top, 'N_rest': N_rest, 'freq_top': freq_top, 'freq_rest': freq_rest, 'enrichment_ratio': enr, 'p_value': pval})
enrich_df = pd.DataFrame(pair_rows)
enrich_df.sort_values(['enrichment_ratio','p_value'], ascending=[False, True]).to_csv(os.path.join(OUT_DIR, 'cofix_enrichment_pairs.csv'), index=False)

# (v) Position of model 1750 in PC space and Delta-Index signs vs tier median
model_id = 1750
if (dfM['FFF']==model_id).any():
    tier_1750 = int(dfM.loc[dfM['FFF']==model_id, 'estim_params'].iloc[0])
    sub = dfM[dfM['estim_params']==tier_1750]
    X = sub[ROBUST_COLS].copy(); X['AICc']*=-1; X['MNCI']*=-1
    Xs = StandardScaler().fit_transform(X)
    pca = PCA(2).fit(Xs)
    sc = pca.transform(Xs)
    idx_row = sub.index[sub['FFF']==model_id][0]
    pos = sc[sub.index.get_loc(idx_row)]
    pc_info = {'model_id': model_id, 'tier_estim_params': tier_1750, 'PC1': float(pos[0]), 'PC2': float(pos[1])}
    with open(os.path.join(OUT_DIR, 'model1750_pc_position.json'), 'w') as f:
        json.dump(pc_info, f, indent=2)

    # Delta signs for params fixed in 1750 vs tier-median
    fixed_series = dfM.loc[dfM['FFF']==model_id, PARAM_COLS].iloc[0]
    fixed_params_1750 = [p for p in PARAM_COLS if fixed_series[p]==1]
    tier_delta = pd.read_csv(os.path.join(OUT_DIR, 'delta_index_median_iqr_by_tier.csv'))
    tsel = tier_delta[tier_delta['estim_params']==tier_1750]
    marks = []
    for p in fixed_params_1750:
        for idx in ROBUST_COLS:
            row = tsel[(tsel['param']==p) & (tsel['index']==idx)]
            if not row.empty:
                dm = float(row['delta_median_pct'].iloc[0])
                sign = 'beneficial' if dm<0 else ('costly' if dm>0 else 'neutral')
                marks.append({'param': p, 'index': idx, 'delta_median_pct': dm, 'sign': sign})
    pd.DataFrame(marks).to_csv(os.path.join(OUT_DIR, 'model1750_delta_signs.csv'), index=False)

# (vi) Sensitivity of tier membership to ±5–10% changes in RSQ cut-off
thresholds = {
    'q65': float(dfM['RSQ2'].quantile(0.65)),
    'q70': float(dfM['RSQ2'].quantile(0.70)),
    'q75': float(q75),
    'q80': float(dfM['RSQ2'].quantile(0.80)),
    'q85': float(dfM['RSQ2'].quantile(0.85)),
}
sens_rows = []
for n_par in sorted(dfM['estim_params'].unique(), reverse=True):
    sub = dfM[dfM['estim_params']==n_par]
    base_set = set(sub.loc[sub['RSQ2']>=thresholds['q75'], 'FFF'].astype(int).tolist())
    base_n = len(base_set)
    for name, thr in thresholds.items():
        alt_set = set(sub.loc[sub['RSQ2']>=thr, 'FFF'].astype(int).tolist())
        inter = len(base_set & alt_set)
        union = len(base_set | alt_set) if (base_set or alt_set) else 0
        jacc = inter/union if union>0 else np.nan
        sens_rows.append({'estim_params': int(n_par), 'threshold': name, 'baseline_count_q75': base_n, 'alt_count': len(alt_set), 'jaccard_similarity': jacc, 'delta_count': len(alt_set)-base_n})
pd.DataFrame(sens_rows).round(3).to_csv(os.path.join(OUT_DIR, 'top_membership_sensitivity.csv'), index=False)

# ========================================================================== #
# 7. SUPPORTING INDICATORS FOR PARAMETER-LEVEL INTERPRETATION (TIERS 7 & 8)  #
#    (i) Per-state RSQ before/after recommended fixations                     #
#    (ii) Stability of estimates (CV proxy) and ρ(ΔCV, ΔMNCI)                 #
#    (iii) Sensitivity allocation (GSS share by class) before/after           #
#    (iv) Local faithfulness via Hamming-1 pairs (counterfactual signs)       #
#    (v) Noise robustness placeholders (σ=2%, 10%)                            #
#    (vi) Acceptance curve and contingency vs top-quartile                    #
# ========================================================================== #

# Recommended fixation policy (tier 7 logic applied to tier 8 as well)
RECOMM_FIX = {7: ["Yxn","Yxg","Yxf","Yeg","Yef","betaF0","Kf0"],
              8: ["Yxn","Yxg","Yxf","Yeg","Yef","betaF0","Kf0"]}
RECOMM_FREE = {7: ["betaG0","Kg0","Kie0"],
               8: ["betaG0","Kg0","Kie0"]}

# Parameter class mapping for sensitivity allocation
PARAM_CLASS = {
    "mu0": "growth",
    "betaG0": "uptake", "Kg0": "uptake", "betaF0": "uptake", "Kf0": "uptake", "Kn0": "uptake",
    "Kig0": "inhibition", "Kie0": "inhibition",
    "Yxn": "yields", "Yxg": "yields", "Yxf": "yields", "Yeg": "yields", "Yef": "yields",
}

TIERS_TARGET = [7, 8]

def models_after_mask(sub: pd.DataFrame, tier: int) -> pd.Series:
    """Return boolean mask of models that satisfy the recommended fix/free sets for a tier."""
    must_fix = RECOMM_FIX.get(tier, [])
    must_free = RECOMM_FREE.get(tier, [])
    if not must_fix and not must_free:
        return pd.Series(False, index=sub.index)
    m = pd.Series(True, index=sub.index)
    for p in must_fix:
        if p in sub.columns:
            m &= (sub[p] == 1)
    for p in must_free:
        if p in sub.columns:
            m &= (sub[p] == 0)
    return m

# Utility: detect columns by regex pattern (case-insensitive)
def detect_cols(df: pd.DataFrame, pattern: str):
    rx = re.compile(pattern, flags=re.IGNORECASE)
    return [c for c in df.columns if rx.search(c)]

# (i) Per-state RSQ before/after recommended fixations
state_cols = []
possible_state_patterns = [r"^RSQ[0-9]*_*.*(glucose)", r"^RSQ[0-9]*_*.*(fructose)", r"^RSQ[0-9]*_*.*(ethanol)", r"^RSQ[0-9]*_*.*(nitrogen)"]
for pat in possible_state_patterns:
    state_cols.extend([c for c in detect_cols(df_robust, pat) if c not in state_cols])
phase_cols = []
for pat in [r"^RSQ[0-9]*_*.*(pre).*YAN", r"^RSQ[0-9]*_*.*(post).*YAN"]:
    phase_cols.extend([c for c in detect_cols(df_robust, pat) if c not in phase_cols])

perstate_rows = []
phase_rows = []
for tier in TIERS_TARGET:
    sub = dfM[dfM["estim_params"] == tier].copy()
    ids = sub["FFF"].astype(int)
    rob = df_robust.set_index("FFF").loc[ids].copy()
    if state_cols:
        mask_after = models_after_mask(sub, tier)
        # boolean mask aligned with rob's row order
        mask_after_arr = mask_after.to_numpy(dtype=bool)
        rb_before = rob.iloc[~mask_after_arr]
        rb_after = rob.iloc[mask_after_arr]
        grp_before = rb_before[state_cols].median(numeric_only=True)
        grp_after = rb_after[state_cols].median(numeric_only=True)
        for c in state_cols:
            perstate_rows.append({
                "tier": tier,
                "metric": c,
                "median_before": float(grp_before.get(c, np.nan)),
                "median_after": float(grp_after.get(c, np.nan)),
                "delta_after_minus_before": float(grp_after.get(c, np.nan) - grp_before.get(c, np.nan)) if (c in grp_before and c in grp_after) else np.nan
            })
    if phase_cols:
        mask_after = models_after_mask(sub, tier)
        mask_after_arr = mask_after.to_numpy(dtype=bool)
        rb_before = rob.iloc[~mask_after_arr]
        rb_after = rob.iloc[mask_after_arr]
        grp_before = rb_before[phase_cols].median(numeric_only=True)
        grp_after = rb_after[phase_cols].median(numeric_only=True)
        for c in phase_cols:
            phase_rows.append({
                "tier": tier,
                "metric": c,
                "median_before": float(grp_before.get(c, np.nan)),
                "median_after": float(grp_after.get(c, np.nan)),
                "delta_after_minus_before": float(grp_after.get(c, np.nan) - grp_before.get(c, np.nan)) if (c in grp_before and c in grp_after) else np.nan
            })

if perstate_rows:
    pd.DataFrame(perstate_rows).to_csv(os.path.join(OUT_DIR, 'per_state_rsq_before_after_tier7_8.csv'), index=False)
else:
    with open(os.path.join(OUT_DIR, 'per_state_rsq_before_after_tier7_8.json'), 'w') as f:
        json.dump({"note": "Per-state RSQ columns not found; expected e.g. RSQ*_glucose/fructose/ethanol/nitrogen."}, f, indent=2)
if phase_rows:
    pd.DataFrame(phase_rows).to_csv(os.path.join(OUT_DIR, 'phase_rsq_delta_before_after_tier7_8.csv'), index=False)
else:
    with open(os.path.join(OUT_DIR, 'phase_rsq_delta_before_after_tier7_8.json'), 'w') as f:
        json.dump({"note": "Phase RSQ columns (pre/post YAN) not found; expected e.g. RSQ*_preYAN/postYAN."}, f, indent=2)

# (ii) Stability of estimates: CV of free parameters (if CV_* columns exist)
cv_cols = {}
for p in PARAM_COLS:
    cands = [f"CV_{p}", f"{p}_CV", f"CV.{p}"]
    for c in cands:
        if c in df_robust.columns:
            cv_cols[p] = c; break

stab_rows = []
rho_rows = []
for tier in TIERS_TARGET:
    sub = dfM[dfM["estim_params"] == tier].copy()
    ids = sub["FFF"].astype(int)
    rob = df_robust.set_index("FFF").loc[ids].copy()
    if not cv_cols:
        continue
    mask_after = models_after_mask(sub, tier)
    # compute per-model median CV across free parameters only
    def median_cv_free(row_struct, row_cv):
        vals = []
        for p, c in cv_cols.items():
            if p in row_struct.index and row_struct[p] == 0:  # free
                v = row_cv.get(c, np.nan)
                if pd.notna(v): vals.append(float(v))
        return float(np.nanmedian(vals)) if vals else np.nan
    mcv_before = []
    mcv_after = []
    mnci_before = []
    mnci_after = []
    for i, rid in enumerate(ids):
        row_struct = sub.loc[sub["FFF"] == rid, PARAM_COLS].iloc[0]
        row_cv = rob.loc[rid]
        mcv = median_cv_free(row_struct, row_cv)
        if mask_after.iloc[i]:
            mcv_after.append(mcv); mnci_after.append(float(dfM.loc[dfM["FFF"]==rid, "MNCI"].iloc[0]))
        else:
            mcv_before.append(mcv); mnci_before.append(float(dfM.loc[dfM["FFF"]==rid, "MNCI"].iloc[0]))
    if mcv_before or mcv_after:
        stab_rows.append({
            "tier": tier,
            "median_cv_free_before": float(np.nanmedian(mcv_before)) if mcv_before else np.nan,
            "median_cv_free_after": float(np.nanmedian(mcv_after)) if mcv_after else np.nan,
            "delta_after_minus_before": (float(np.nanmedian(mcv_after)) - float(np.nanmedian(mcv_before))) if (mcv_before and mcv_after) else np.nan,
            "n_before": len([x for x in mcv_before if x == x]),
            "n_after": len([x for x in mcv_after if x == x])
        })
        # Proxy correlation: association of median CV and MNCI within each group (not paired)
        try:
            if len(mcv_after) >= 3 and len(mnci_after) == len(mcv_after):
                r = pd.Series(mcv_after).corr(pd.Series(mnci_after), method='spearman')
                rho_rows.append({"tier": tier, "group": "after", "spearman_rho_CV_MNCI": float(r)})
            if len(mcv_before) >= 3 and len(mnci_before) == len(mcv_before):
                r = pd.Series(mcv_before).corr(pd.Series(mnci_before), method='spearman')
                rho_rows.append({"tier": tier, "group": "before", "spearman_rho_CV_MNCI": float(r)})
        except Exception:
            pass

if stab_rows:
    pd.DataFrame(stab_rows).to_csv(os.path.join(OUT_DIR, 'stability_cv_before_after_tier7_8.csv'), index=False)
else:
    with open(os.path.join(OUT_DIR, 'stability_cv_before_after_tier7_8.json'), 'w') as f:
        json.dump({"note": "CV per-parameter columns not found (expected e.g. CV_mu0)."}, f, indent=2)
if rho_rows:
    pd.DataFrame(rho_rows).to_csv(os.path.join(OUT_DIR, 'stability_spearman_cv_mnci_tier7_8.csv'), index=False)

# (iii) Sensitivity allocation: GSS share by class before/after (if per-param GSS exists)
gss_param_cols = {}
for p in PARAM_COLS:
    cands = [f"GSS_{p}", f"{p}_GSS", f"GSS.{p}"]
    for c in cands:
        if c in df_robust.columns:
            gss_param_cols[p] = c; break

alloc_rows = []
for tier in TIERS_TARGET:
    sub = dfM[dfM["estim_params"] == tier].copy()
    ids = sub["FFF"].astype(int)
    rob = df_robust.set_index("FFF").loc[ids].copy()
    if not gss_param_cols:
        continue
    mask_after = models_after_mask(sub, tier)
    mask_after_arr = mask_after.to_numpy(dtype=bool)
    for grp_name, mask_arr in [("before", ~mask_after_arr), ("after", mask_after_arr)]:
        part = rob.iloc[mask_arr]
        if part.empty:
            continue
        present_params = [p for p in PARAM_COLS if p in gss_param_cols]
        if not present_params:
            continue
        cols = [gss_param_cols[p] for p in present_params]
        gss_df = part[cols].copy()
        gss_df.columns = present_params
        total = gss_df.sum(axis=1)
        total_safe = total.replace(0, np.nan)
        for cls in ["growth","uptake","inhibition","yields"]:
            cls_params = [p for p in present_params if PARAM_CLASS.get(p) == cls]
            if not cls_params:
                continue
            cls_sum = gss_df[cls_params].sum(axis=1)
            share = 100.0 * (cls_sum / total_safe)
            mean_share = float(share.mean(skipna=True)) if len(share) else np.nan
            if mean_share == mean_share:  # not NaN
                alloc_rows.append({"tier": tier, "group": grp_name, "class": cls, "mean_share_pct": mean_share})

if alloc_rows:
    pd.DataFrame(alloc_rows).to_csv(os.path.join(OUT_DIR, 'gss_share_by_class_before_after_tier7_8.csv'), index=False)
else:
    with open(os.path.join(OUT_DIR, 'gss_share_by_class_before_after_tier7_8.json'), 'w') as f:
        json.dump({"note": "Per-parameter GSS columns not found (expected e.g. GSS_param)."}, f, indent=2)

# (iv) Local faithfulness: one-change counterfactuals within tier 7
def hamming1_pairs(sub_bin: pd.DataFrame, max_pairs=5):
    pairs = []
    used = set()
    # order by RSQ descending to pick representative models
    ranked = sub_bin.sort_values("RSQ2", ascending=False)
    X = ranked[PARAM_COLS].astype(int).to_numpy()
    idx_to_id = ranked["FFF"].astype(int).tolist()
    n = len(idx_to_id)
    for i in range(n):
        if len(pairs) >= max_pairs: break
        if idx_to_id[i] in used: continue
        for j in range(i+1, n):
            if idx_to_id[j] in used: continue
            hd = int(np.sum(np.abs(X[i] - X[j])))
            if hd == 1:  # exactly one param differs
                pairs.append((idx_to_id[i], idx_to_id[j]))
                used.add(idx_to_id[i]); used.add(idx_to_id[j])
                break
    return pairs

faith_rows = []
for tier in [7]:  # requested focus on tier 7
    sub = dfM[dfM["estim_params"] == tier].copy()
    if len(sub) < 2: continue
    pairs = hamming1_pairs(sub[["FFF","RSQ2"]+PARAM_COLS], max_pairs=5)
    for a,b in pairs:
        ra = dfM.loc[dfM["FFF"]==a, ROBUST_COLS].iloc[0]
        rb = dfM.loc[dfM["FFF"]==b, ROBUST_COLS].iloc[0]
        # which param flipped?
        va = dfM.loc[dfM["FFF"]==a, PARAM_COLS].iloc[0].astype(int)
        vb = dfM.loc[dfM["FFF"]==b, PARAM_COLS].iloc[0].astype(int)
        diff = (va - vb).abs()
        if diff.sum() == 1:
            pflip = diff.index[diff==1][0]
        else:
            pflip = "unknown"
        for idx in ROBUST_COLS:
            delta = float(rb[idx] - ra[idx])
            sign = 'increase' if delta>0 else ('decrease' if delta<0 else 'neutral')
            faith_rows.append({"tier": tier, "model_a": a, "model_b": b, "flipped_param": pflip, "index": idx, "delta_b_minus_a": delta, "sign": sign})

if faith_rows:
    pd.DataFrame(faith_rows).to_csv(os.path.join(OUT_DIR, 'local_faithfulness_hamming1_tier7.csv'), index=False)
else:
    with open(os.path.join(OUT_DIR, 'local_faithfulness_hamming1_tier7.json'), 'w') as f:
        json.dump({"note": "No Hamming-1 model pairs found in tier 7 or insufficient data."}, f, indent=2)

# (v) Noise robustness placeholders
noise_cols = detect_cols(df_robust, r"(AAIC|AIC|MNCI|RSQ|GSS).*sigma")
if noise_cols:
    with open(os.path.join(OUT_DIR, 'noise_robustness_note.json'), 'w') as f:
        json.dump({"note": "Noise-level specific columns detected; extend analysis here if needed.", "columns": noise_cols}, f, indent=2)
else:
    with open(os.path.join(OUT_DIR, 'noise_robustness_note.json'), 'w') as f:
        json.dump({"note": "No noise-level specific metrics (e.g., *_sigma2, *_sigma10) found; re-run MC–CV at σ=2% and 10% to enable this check."}, f, indent=2)

# (vi) Acceptance curve for the selection rule (tier 7 & 8)
for tier in TIERS_TARGET:
    sub = dfM[dfM["estim_params"] == tier].copy()
    if sub.empty: continue
    q75_tier = float(sub['RSQ2'].quantile(0.75))
    mnci_med = float(sub['MNCI'].median())
    accept_mask = (sub['RSQ2'] >= q75_tier) & (sub['MNCI'] <= mnci_med)
    top_mask = (sub['RSQ2'] >= q75)
    cont = pd.DataFrame({
        'accepted_rule': accept_mask.value_counts(),
        'top_quartile_global': top_mask.value_counts()
    }).fillna(0).astype(int)
    cont.to_csv(os.path.join(OUT_DIR, f'acceptance_contingency_tier{tier}.csv'))
    # Scatter figure
    fig, ax = plt.subplots(figsize=(5.5,4.5))
    ax.scatter(sub['MNCI'], sub['RSQ2'], c=PAL_GRAY, alpha=0.5, s=25, label='All')
    ax.scatter(sub.loc[accept_mask, 'MNCI'], sub.loc[accept_mask, 'RSQ2'], c=PAL_BLUE, alpha=0.9, s=30, label='Accepted')
    ax.axhline(q75_tier, color='black', linestyle='--', linewidth=0.8, label=f'RSQ q75 tier={tier}')
    ax.axvline(mnci_med, color='black', linestyle=':', linewidth=0.8, label='MNCI median')
    ax.set_xlabel('MNCI'); ax.set_ylabel('RSQ2'); ax.set_title(f'Acceptance Rule – Tier {tier}')
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_FIGS, f'acceptance_curve_tier{tier}.png'), dpi=300)
    fig.savefig(os.path.join(OUT_FIGS, f'acceptance_curve_tier{tier}.pdf'), dpi=300, bbox_inches='tight')

# ========================================================================== #
# 8. AUTO-GENERATED NARRATIVE SUMMARY (TIERS 7 & 8)                          #
# ========================================================================== #
def fmt(x, nd=4):
    try:
        return f"{float(x):.{nd}f}"
    except Exception:
        return "NA"

def safe_read_csv(path):
    try:
        return pd.read_csv(path)
    except Exception:
        return None

nar_lines = []
nar_lines.append("# Stage III – Supporting indicators (auto-summary)\n")

# Tier sizes and thresholds
nar_lines.append("## Tiers and thresholds\n")
for tier in [7,8]:
    sub = dfM[dfM['estim_params']==tier]
    if sub.empty:
        nar_lines.append(f"- Tier {tier}: no models available.\n"); continue
    n_total = int(len(sub)); n_top = int((sub['RSQ2']>=q75).sum())
    q75_tier = float(sub['RSQ2'].quantile(0.75))
    nar_lines.append(f"- Tier {tier}: n = {n_total}, top = {n_top}; RSQ2 q75 (global) = {fmt(q75,4)}, RSQ2 q75 (tier) = {fmt(q75_tier,4)}\n")

# PCA diagnostics and permutation p-values
pca_df = safe_read_csv(os.path.join(OUT_DIR, 'pca_diagnostics_top_vs_rest.csv'))
pp_df  = safe_read_csv(os.path.join(OUT_DIR, 'pca_perm_pvalues_top_vs_rest.csv'))
nar_lines.append("## PCA robustness map\n")
if pca_df is not None and pp_df is not None:
    m = pca_df.merge(pp_df, on='estim_params', how='left')
    for tier in [7,8]:
        row = m[m['estim_params']==tier]
        if not row.empty:
            r = row.iloc[0]
            nar_lines.append(
                f"- Tier {tier}: PC1={fmt(r['pc1_pct'],1)}%, PC2={fmt(r['pc2_pct'],1)}%; centroid distance={fmt(r['centroid_distance'],3)}; perm. p={fmt(r.get('p_perm_centroid_separation', np.nan),3)} (n_top={int(r.get('n_top',0))}, n_rest={int(r.get('n_rest',0))}).\n"
            )
else:
    nar_lines.append("- PCA diagnostics not available.\n")

# Delta-Index summaries: detect beneficial and costly fixations in tier 7
nar_lines.append("## Δ-Index (within-tier)\n")
delta_df = safe_read_csv(os.path.join(OUT_DIR, 'delta_index_median_iqr_by_tier.csv'))
def list_params_by_sign(tier, idx, cond):
    out = []
    if delta_df is None: return out
    dd = delta_df[(delta_df['estim_params']==tier) & (delta_df['index']==idx)]
    for p in PARAM_COLS:
        r = dd[dd['param']==p]
        if r.empty: continue
        val = float(r['delta_median_pct'].iloc[0])
        if cond(val):
            out.append(param_labels[p])
    return out

if delta_df is not None:
    # Beneficial to fix in tier 7: ΔAICc<0, ΔMNCI<0, and |ΔRSQ|<=1
    ben = set(list_params_by_sign(7, 'AICc', lambda v: v<0)) & \
          set(list_params_by_sign(7, 'MNCI', lambda v: v<0))
    near = set(list_params_by_sign(7, 'RSQ2', lambda v: abs(v)<=1.0))
    ben = [b for b in ben if b in near]
    # Costly in tier 7: ΔRSQ <-1 (drop)
    cost = list_params_by_sign(7, 'RSQ2', lambda v: v < -1.0)
    if ben:
        nar_lines.append(f"- Tier 7 – likely beneficial fixations (ΔAICc<0, ΔMNCI<0, ~neutral ΔRSQ): {', '.join(ben)}.\n")
    if cost:
        nar_lines.append(f"- Tier 7 – potential RSQ detriment when fixed (ΔRSQ < -1%): {', '.join(cost)}.\n")
else:
    nar_lines.append("- Δ-Index summaries not available.\n")

# Stability (CV) and RSQ per-state/phase
nar_lines.append("## Stabilisation and per-state skill\n")
stab_df = safe_read_csv(os.path.join(OUT_DIR, 'stability_cv_before_after_tier7_8.csv'))
rho_df  = safe_read_csv(os.path.join(OUT_DIR, 'stability_spearman_cv_mnci_tier7_8.csv'))
if stab_df is not None:
    for tier in [7,8]:
        rr = stab_df[stab_df['tier']==tier]
        if rr.empty: continue
        r = rr.iloc[0]
        nar_lines.append(
            f"- Tier {tier}: median CV_free before={fmt(r['median_cv_free_before'],2)}, after={fmt(r['median_cv_free_after'],2)}, Δ={fmt(r['delta_after_minus_before'],2)} (n_before={int(r['n_before'])}, n_after={int(r['n_after'])}).\n"
        )
if rho_df is not None and not rho_df.empty:
    for tier in [7,8]:
        g = rho_df[rho_df['tier']==tier]
        if not g.empty:
            vals = ", ".join([f"{row['group']}: ρ={fmt(row['spearman_rho_CV_MNCI'],2)}" for _,row in g.iterrows()])
            nar_lines.append(f"- Tier {tier}: Spearman ρ(CV, MNCI) – {vals}.\n")

ps_df = safe_read_csv(os.path.join(OUT_DIR, 'per_state_rsq_before_after_tier7_8.csv'))
ph_df = safe_read_csv(os.path.join(OUT_DIR, 'phase_rsq_delta_before_after_tier7_8.csv'))
if ps_df is not None and not ps_df.empty:
    for tier in [7,8]:
        rr = ps_df[ps_df['tier']==tier]
        if rr.empty: continue
        deltas = rr[['metric','delta_after_minus_before']].dropna().sort_values('metric')
        entries = ", ".join([f"{m}: Δ={fmt(d,3)}" for m,d in zip(deltas['metric'], deltas['delta_after_minus_before'])])
        nar_lines.append(f"- Tier {tier}: per-state ΔRSQ (after–before): {entries}.\n")
if ph_df is not None and not ph_df.empty:
    for tier in [7,8]:
        rr = ph_df[ph_df['tier']==tier]
        if rr.empty: continue
        deltas = rr[['metric','delta_after_minus_before']].dropna().sort_values('metric')
        entries = ", ".join([f"{m}: Δ={fmt(d,3)}" for m,d in zip(deltas['metric'], deltas['delta_after_minus_before'])])
        nar_lines.append(f"- Tier {tier}: phase ΔRSQ (after–before): {entries}.\n")

# Sensitivity allocation (GSS shares)
nar_lines.append("## Sensitivity allocation (GSS shares)\n")
alloc_df = safe_read_csv(os.path.join(OUT_DIR, 'gss_share_by_class_before_after_tier7_8.csv'))
if alloc_df is not None and not alloc_df.empty:
    for tier in [7,8]:
        g = alloc_df[alloc_df['tier']==tier]
        if g.empty: continue
        try:
            piv = g.pivot_table(index='class', columns='group', values='mean_share_pct', aggfunc='mean')
            piv['delta_after_minus_before'] = piv.get('after', np.nan) - piv.get('before', np.nan)
            rows = []
            for cls, r in piv.iterrows():
                rows.append(f"{cls}: before={fmt(r.get('before', np.nan),1)}%, after={fmt(r.get('after', np.nan),1)}%, Δ={fmt(r.get('delta_after_minus_before', np.nan),1)}%")
            nar_lines.append(f"- Tier {tier}: {'; '.join(rows)}.\n")
        except Exception:
            pass
else:
    nar_lines.append("- Per-parameter GSS not available for class-wise allocation.\n")

# Acceptance rule summary
nar_lines.append("## Acceptance rule (RSQ q75 tier; MNCI median)\n")
for tier in [7,8]:
    sub = dfM[dfM['estim_params']==tier]
    if sub.empty: continue
    q75_tier = float(sub['RSQ2'].quantile(0.75))
    mnci_med = float(sub['MNCI'].median())
    cont_path = os.path.join(OUT_DIR, f'acceptance_contingency_tier{tier}.csv')
    cont_df = safe_read_csv(cont_path)
    if cont_df is not None:
        nar_lines.append(f"- Tier {tier}: thresholds RSQ2≥{fmt(q75_tier,4)} and MNCI≤{fmt(mnci_med,3)}; see acceptance_contingency_tier{tier}.csv.\n")
    else:
        nar_lines.append(f"- Tier {tier}: thresholds RSQ2≥{fmt(q75_tier,4)} and MNCI≤{fmt(mnci_med,3)}.\n")

with open(os.path.join(OUT_DIR, 'stage3_supporting_narrative.md'), 'w', encoding='utf-8') as f:
    f.write("\n".join(nar_lines))



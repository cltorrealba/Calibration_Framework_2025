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

# -------------------------------------------------------------------------- #
# ElasticNetCV + manual CV for CIs                                          #
# -------------------------------------------------------------------------- #
X = dfM[PARAM_COLS].astype(float).to_numpy()
kf = KFold(n_splits=10, shuffle=False)
en_coefs = {}
for metric in ROBUST_COLS:
    y = dfM[metric].to_numpy()
    encv = ElasticNetCV(l1_ratio=[.1,.5,.9,1], cv=10, max_iter=5000).fit(X,y)
    alpha, l1 = encv.alpha_, encv.l1_ratio_
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
    if c>0: ax1.text(e+0.25, c+0.3, f"{int(c)}", ha="center", fontsize=8)
for c,e in zip(cnt_top, edges[:-1]):
    if c>0: ax1.text(e+0.45, c+0.6, f"{int(c)}",
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
#    drop tiers with <2 top models                                            #
# ========================================================================== #
tiers = [n for n in sorted(dfM["estim_params"].unique(), reverse=True)
         if dfM[(dfM["estim_params"]==n)&(dfM["RSQ2"]>=q75)].shape[0]>=2]
n_rows = len(tiers)
fig2, axes = plt.subplots(n_rows,3, figsize=(18,4.5*n_rows),
    gridspec_kw={"hspace":0.35,"wspace":0.28})
if n_rows==1: axes=axes.reshape(1,3)
freq_pool = (dfM[PARAM_COLS]==1).mean()*100

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
            col = PAL_BLUE if sel.iloc[i] else PAL_GRAY
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
    sns.heatmap(heat_df, cmap="vlag", center=0, robust=True,
                xticklabels=ROBUST_COLS,
                yticklabels=[param_labels[p] for p in PARAM_COLS],
                annot=True, fmt=".1f", annot_kws={"size":7},
                linewidths=0.5, linecolor="gray", ax=axH)
    axH.set_title(f"(C) Δ-Index (%) – {n_par} free")

fig2.tight_layout()
fig2.savefig("stage3_Fig2_complexity_grid.png", dpi=300)

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
            h2.loc[1750, p] = 3
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


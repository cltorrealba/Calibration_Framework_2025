# -*- coding: utf-8 -*-
"""
Validation & Transfer analysis
Author: Cristóbal L. Torrealba V.  (adapted suggestions by ChatGPT)
Created: 2025-05-14

This script reads:
  • HIPPO_result.xlsx           – model‐structure + fixation flags
  • Zenteno_Final_2023b_WS.xlsx – Stage III robustness indices
  • validation_metrics.csv      – NEW file produced by Main_Validacion.py
                                  (one row per model×dataset with AD_stat_*,
                                   DW_stat_*, r2_adj_*)

and generates Figures V-1 … V-6 and Table V-1 for the manuscript.

Edit the three paths below, then `python stage4_validation_analysis.py`.
"""

# ------------------------------------------------------------------ #
# 0. Imports & constants
# ------------------------------------------------------------------ #
import pandas    as pd
import numpy     as np
import matplotlib.pyplot as plt
import seaborn   as sns
from sklearn.preprocessing  import StandardScaler
from sklearn.linear_model   import ElasticNetCV, LogisticRegression
from sklearn.metrics        import roc_auc_score, confusion_matrix, silhouette_score
from kmodes.kmodes          import KModes
from sklearn.tree           import DecisionTreeClassifier, plot_tree
from statsmodels.stats.multitest import multipletests
from scipy.stats            import pointbiserialr
import pathlib, warnings

warnings.filterwarnings("ignore")

# ---------- file paths (EDIT ME) ---------------------------------- #
FP_STRUCT   = pathlib.Path("C:/Users/ctorrealba/OneDrive - Viña Concha y Toro S.A/Documentos/Doctorado/Artículos/Artículo - Estimación/Codes/STEP 2/HIPPO_result.xlsx")
FP_ROBUST   = pathlib.Path("C:/Users/ctorrealba/OneDrive - Viña Concha y Toro S.A/Documentos/Doctorado/Artículos/Artículo - Estimación/Codes/STEP 3/Zenteno_Final_2023b_WS.xlsx")
FP_VALIDATE = pathlib.Path("validation_metrics_Zenteno.csv")

# ---------- parameter definitions --------------------------------- #
PARAM_COLS = [
    'mu0','betaG0','betaF0','Kn0','Kg0','Kf0','Kig0',
    'Kie0','Yxn','Yxg','Yxf','Yeg','Yef'
]
param_labels = {
    'mu0':    r'$\mu_{0}$',   'betaG0': r'$\beta_{G0}$',
    'betaF0': r'$\beta_{F0}$','Kn0':    r'$K_{n0}$',
    'Kg0':    r'$K_{g0}$',    'Kf0':    r'$K_{f0}$',
    'Kig0':   r'$K_{ig0}$',   'Kie0':   r'$K_{ie0}$',
    'Yxn':    r'$Y_{xn}$',    'Yxg':    r'$Y_{xg}$',
    'Yxf':    r'$Y_{xf}$',    'Yeg':    r'$Y_{eg}$',
    'Yef':    r'$Y_{ef}$',
}

# ---------- helper: save fig -------------------------------------- #
OUTDIR = pathlib.Path("fig_validation")
OUTDIR.mkdir(exist_ok=True)
def savefig(fig, name):
    fig.savefig(OUTDIR/name, dpi=300, bbox_inches="tight")


# ------------------------------------------------------------------ #
# 1. Load & merge data
# ------------------------------------------------------------------ #
# model structure
df_struct = pd.read_excel(FP_STRUCT, sheet_name=0)[["FFF"] + PARAM_COLS]

# Stage-III robustness
df_rob = pd.read_excel(FP_ROBUST, sheet_name=0)[["FFF","AICc","MNCI","RSQ2","GSS"]]

# NEW: validation metrics CSV
df_val = pd.read_csv(FP_VALIDATE)

# aggregate the three analyte-specific metrics
r2_cols = ['r2_adj_Fructose','r2_adj_Glucose','r2_adj_YAN']
ad_cols = ['AD_stat_Fructose','AD_stat_Glucose','AD_stat_YAN']
dw_cols = ['DW_stat_Fructose','DW_stat_Glucose','DW_stat_YAN']

df_val['R2_adj'] = df_val[r2_cols].mean(axis=1)
df_val['AD_pass'] = (df_val[ad_cols] > 0.05).all(axis=1).astype(int)
# Durbin-Watson near 2 → pass if in [1,3]
dw_mask = (df_val[dw_cols] >= 1.0) & (df_val[dw_cols] <= 3.0)
df_val['DW_pass'] = dw_mask.all(axis=1).astype(int)
# merge in structure flags
df_v1 = (
    df_val
    .merge(df_struct, left_on="model_id", right_on="FFF")
    .assign(free=lambda d: (d[PARAM_COLS]==0).sum(axis=1))
)

# create a simple 'Dataset' label for plotting
df_v1['Dataset'] = df_v1.apply(
    lambda r: f"exp{int(r.exper_id)}·s{int(r.scale_id)}",
    axis=1
)


# ------------------------------------------------------------------ #
# 2. Figure V-1 – adj-R² vs free-parameter count
# ------------------------------------------------------------------ #
sns.set_theme(style="whitegrid")
fig, ax = plt.subplots(figsize=(6,4))
sns.scatterplot(
    data=df_v1, x="free", y="R2_adj",
    hue="Dataset", palette="colorblind", ax=ax
)
sns.regplot(
    data=df_v1, x="free", y="R2_adj",
    lowess=True, scatter=False, color="k", ax=ax
)
ax.set_xlabel("Number of free parameters")
ax.set_ylabel(r"$R^2_{\mathrm{adj}}$ (validation)")
ax.set_title("Fig. V-1  Validation performance vs model complexity")
savefig(fig, "Fig_V1_R2_vs_free.png")
plt.show()

# ------------------------------------------------------------------ #
# 3. Table V-1 – point-biserial correlations
# ------------------------------------------------------------------ #
rows=[]
for p in PARAM_COLS:
    fixed_flag = (df_v1[p]==1).astype(int)
    r,pval = pointbiserialr(fixed_flag, df_v1["R2_adj"])
    rows.append({"Parameter": p, "r_pb": r, "p": pval})
tbl = pd.DataFrame(rows)
tbl["q"]   = multipletests(tbl["p"], method="fdr_bh")[1]
tbl["sig"] = np.where(tbl["q"]<0.05, "**", "")
tbl_out = tbl.sort_values("q")[["Parameter","r_pb","q","sig"]]
tbl_out.to_csv("Table_V1_PointBiserial.csv", index=False)


# ------------------------------------------------------------------ #
# 4. Figure V-2 – ElasticNet logistic coefficients
# ------------------------------------------------------------------ #
# define 'success' = top-quartile R2_adj & both tests passed
q75     = df_v1["R2_adj"].quantile(0.75)
success = (
    (df_v1["R2_adj"]>=q75) &
    (df_v1["AD_pass"]==1) &
    (df_v1["DW_pass"]==1)
).astype(int)

X = (df_v1[PARAM_COLS]==1).astype(int).values
y = success.values

# fit ElasticNet‐penalized logistic
encv = ElasticNetCV(l1_ratio=[.1,.5,.9,1], cv=10, random_state=1).fit(X,y)
alpha,l1 = encv.alpha_, encv.l1_ratio_
model = LogisticRegression(
    penalty="elasticnet", solver="saga",
    l1_ratio=l1, C=1/alpha, max_iter=5000
).fit(X,y)
coefs = model.coef_.flatten()

# ── stratified bootstrap to ensure both classes in each sample ──────
boot=[]
rng = np.random.default_rng(0)
pos_idx = np.where(y==1)[0]
neg_idx = np.where(y==0)[0]
n_pos, n_neg = len(pos_idx), len(neg_idx)
n_boot = 250

for _ in range(n_boot):
    # sample equally (with replacement) from each class
    samp_pos = rng.choice(pos_idx, size=n_pos, replace=True)
    samp_neg = rng.choice(neg_idx, size=n_neg, replace=True)
    idx      = np.concatenate([samp_pos, samp_neg])
    rng.shuffle(idx)
    m = LogisticRegression(
        penalty="elasticnet", solver="saga",
        l1_ratio=l1, C=1/alpha, max_iter=3000
    ).fit(X[idx], y[idx])
    boot.append(m.coef_.flatten())

boot = np.vstack(boot)
ci_lo, ci_hi = np.percentile(boot, [2.5,97.5], axis=0)

# ── plot with 95% CI ────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7,5))
ax.barh(
    range(len(PARAM_COLS)), coefs,
    xerr=[coefs-ci_lo, ci_hi-coefs],
    color=sns.color_palette()[0], alpha=0.8
)
ax.set_yticks(range(len(PARAM_COLS)))
ax.set_yticklabels([param_labels[p] for p in PARAM_COLS])
ax.axvline(0, lw=0.8, color="k")
ax.set_xlabel("ElasticNet-logistic coefficient")
ax.set_title("Fig. V-2  Drivers of top-performing models")
savefig(fig, "Fig_V2_EN_coeffs.png")

# report AUROC & confusion matrix
prob = model.predict_proba(X)[:,1]
print("\nAUROC =", roc_auc_score(y, prob).round(3))
print("Confusion matrix:\n", confusion_matrix(y, prob>=0.5), "\n")
plt.show()

# ------------------------------------------------------------------ #
# 5. Figure V-3 – fixation clusters
# ------------------------------------------------------------------ #
bin_matrix = (df_struct.set_index("FFF")[PARAM_COLS]==1).astype(int)

# encuentra k óptimo por silhouette
best = (None, -np.inf, None)
for k in range(2,7):
    km = KModes(n_clusters=k, random_state=2).fit(bin_matrix)
    sil = silhouette_score(bin_matrix, km.labels_, metric="hamming")
    if sil > best[1]:
        best = (k, sil, km)
k_opt, _, km = best

# construimos un DataFrame de clusters para cada modelo
df_clusters = pd.DataFrame({
    "model_id": bin_matrix.index.astype(int),
    "cluster":  km.labels_
})

# vuelvo a unir el cluster a df_struct
df_struct['cluster'] = df_struct['FFF'].map(
    df_clusters.set_index('model_id')['cluster']
)

# heatmap de patrones de fijación (V-3a)
fig, ax = plt.subplots(figsize=(6,8))
sns.heatmap(
    bin_matrix.loc[df_struct.sort_values("cluster")["FFF"]],
    cmap="Greys", cbar=False, yticklabels=False,
    linewidths=0.3, linecolor="grey", ax=ax
)
ax.set_xticklabels([param_labels[p] for p in PARAM_COLS], rotation=90)
ax.set_title(f"Fig. V-3a  Fixation patterns – k-modes (k={k_opt})")
savefig(fig, "Fig_V3a_fixation_heatmap.png")
plt.show()

# ya puedes definir 'order' para usarlo en la V-6
order = df_struct.sort_values("cluster")["FFF"].tolist()
valid_models = df_val["model_id"].unique().tolist()
order = [m for m in order if m in valid_models]

# ------------------------------------------------------------------ #
# 5b. Figure V-3b – ΔR² radar by cluster (promediando replicados)
# ------------------------------------------------------------------ #
# 1) promedia los dos experimentos por modelo×escala
df_pivot = (
    df_val
    .groupby(['model_id','scale_id'])['R2_adj']
    .mean()
    .unstack()    # columnas: 1=lab, 2=pilot
)

# 2) calcula ΔR2 = pilot (2) – lab (1)
df_delta = (
    (df_pivot[2] - df_pivot[1])
    .rename("ΔR2")
    .reset_index()
    .merge(df_clusters, on="model_id")
)

fig, ax = plt.subplots(figsize=(5,4), subplot_kw=dict(polar=True))
angles = np.linspace(0, 2*np.pi, df_delta['cluster'].nunique(), endpoint=False)
for cl in sorted(df_delta['cluster'].unique()):
    vals = df_delta.query("cluster==@cl")['ΔR2'].values
    ax.plot([angles[cl]]*len(vals), vals, 'o', label=f"Cluster {cl}")

ax.set_title("Fig. V-3b  ΔR² per cluster")
ax.set_ylim(df_delta['ΔR2'].min() - .05, df_delta['ΔR2'].max() + .05)
ax.set_xticks(angles)
ax.set_xticklabels([f"C{c}" for c in sorted(df_delta['cluster'].unique())])
ax.legend(loc="upper left", bbox_to_anchor=(1,1))
savefig(fig, "Fig_V3b_cluster_deltas.png")


savefig(fig, "Fig_V3b_cluster_deltas.png")
plt.show()

# ------------------------------------------------------------------ #
# 6. Figure V-4 – decision-tree for Δ-degradation
# ------------------------------------------------------------------ #
# 1) promedio R2_adj por (model_id, scale_id)
df_pivot = (
    df_val
    .groupby(['model_id','scale_id'])['R2_adj']
    .mean()
    .unstack()   # columnas: 1, 2
)

# 2) arma df_tree con el delta y flags de estructura
df_tree = (
    df_pivot
    .assign(delta=lambda d: d[2] - d[1])
    .reset_index()
    .merge(
        df_struct.rename(columns={'FFF':'model_id'}),
        on='model_id'
    )
)

# 3) prepara X e y_bad
Xtree = (df_tree[PARAM_COLS] == 1).astype(int)
y_bad  = (df_tree['delta'] < -0.10).astype(int)

# 4) entrena árbol y grafica
dt = DecisionTreeClassifier(max_depth=3, random_state=0).fit(Xtree, y_bad)
fig, ax = plt.subplots(figsize=(8,4))
plot_tree(
    dt, feature_names=PARAM_COLS,
    class_names=['OK','Drop'],
    filled=True, impurity=False, ax=ax
)
ax.set_title("Fig. V-4  Rules for scale-up degradation (ΔR² < -0.10)")
savefig(fig, "Fig_V4_decision_tree.png")
plt.show()


# ------------------------------------------------------------------ #
# 7. Figure V-5 – |Δθ| distribution
theta_shift = pd.read_excel("param_shift_summary.xlsx")
fig, ax = plt.subplots(figsize=(7,4))
sns.boxplot(
    data=theta_shift,
    x="param", y="rel_shift",
    palette="colorblind", ax=ax
)
ax.set_xticklabels(
    [param_labels[p] for p in theta_shift["param"].unique()],
    rotation=90
)
ax.set_ylabel(r"$|\Delta\theta| / \theta_{lab}$")
ax.set_title("Fig. V-5  Sensitivity of re‐estimated free parameters")
savefig(fig, "Fig_V5_theta_shift.png")
plt.show()
# ------------------------------------------------------------------ #
# 8. Figure V-6 – residual diagnostic heatmap
# ------------------------------------------------------------------ #
diag_cols = ["R2_pass","AD_pass","DW_pass"]
df_diag = (
    df_val.assign(R2_pass=lambda d: d["R2_adj"]>=q75)
          .set_index("model_id")[diag_cols]
          .loc[order]
)
fig, ax = plt.subplots(figsize=(5,8))
sns.heatmap(
    df_diag.astype(int),
    cmap=sns.color_palette(["#BC3B3B","#00A878"]),
    cbar=False, linewidths=.3, linecolor="gray",
    ax=ax
)
ax.set_title("Fig. V-6  Residual diagnostics summary")
ax.set_xlabel("Criteria"); ax.set_ylabel("Model ID")
savefig(fig, "Fig_V6_diag_heatmap.png")
plt.show()
print("\nAll figures saved to", OUTDIR.resolve())

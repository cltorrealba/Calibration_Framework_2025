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
from sklearn.tree           import DecisionTreeClassifier, plot_tree, export_text
from sklearn.model_selection import StratifiedKFold
from statsmodels.stats.multitest import multipletests
from scipy.stats            import pointbiserialr
from statsmodels.nonparametric.smoothers_lowess import lowess
from matplotlib.colors import ListedColormap
from itertools import combinations
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
METRICSDIR = OUTDIR/"metrics"
METRICSDIR.mkdir(exist_ok=True)
METRICSDIR = OUTDIR / "metrics"
METRICSDIR.mkdir(exist_ok=True)
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
# Anderson–Darling at 5% for normality: statistic < 0.751 (approx). If you stored p-values instead, replace with p>0.05.
AD_CRIT_5 = 0.751
df_val['AD_pass'] = (df_val[ad_cols] < AD_CRIT_5).all(axis=1).astype(int)
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

# V-1 metrics: Spearman rho/p and LOWESS slope; counts by Dataset
from scipy.stats import spearmanr
res = spearmanr(pd.to_numeric(df_v1["free"]).to_numpy(), pd.to_numeric(df_v1["R2_adj"]).to_numpy())
try:
    # Newer SciPy returns an object with correlation/pvalue
    rho_val_f = float(getattr(res, 'correlation'))
    p_val_f   = float(getattr(res, 'pvalue'))
except Exception:
    try:
        rho_val_f = float(getattr(res, 'statistic'))
        p_val_f   = float(getattr(res, 'pvalue'))
    except Exception:
        # Fallback to tuple-like
        res_tuple = tuple(res)
        rho_val_f = float(res_tuple[0])
        p_val_f   = float(res_tuple[1])
try:
    smth = lowess(pd.to_numeric(df_v1["R2_adj"]).to_numpy(), pd.to_numeric(df_v1["free"]).to_numpy(), frac=0.6, it=0, return_sorted=True)
    x_s, y_s = smth[:,0], smth[:,1]
    lowess_slope = float(np.polyfit(x_s, y_s, 1)[0])
except Exception:
    lowess_slope = float('nan')
pd.DataFrame([{ "spearman_rho": rho_val_f, "spearman_p": p_val_f, "lowess_slope": lowess_slope }]) \
    .to_csv(METRICSDIR/"V1_complexity_vs_perf_summary.csv", index=False)
df_v1.groupby("Dataset").size().rename("n_points").to_csv(METRICSDIR/"V1_counts_by_dataset.csv")

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
tbl_out.to_csv(str(METRICSDIR/"Table_V1_PointBiserial.csv"), index=False)

# also export top-5 by absolute correlation
tbl_out.reindex(tbl_out['r_pb'].abs().sort_values(ascending=False).index) \
    .head(5) \
    .to_csv(str(METRICSDIR/"Table_V1_PointBiserial_top5.csv"), index=False)


# ------------------------------------------------------------------ #
# 4. Figure V-2 – ElasticNet logistic coefficients
# ------------------------------------------------------------------ #
def _pick_labels_with_fallback(df: pd.DataFrame) -> tuple[pd.Series, str]:
    """
    Devuelve (y, desc) intentando distintas definiciones hasta obtener 2 clases.
    Orden de intentos:
      1) top‐quartile y AD/DW pass
      2) top‐quartile solo
      3) >= mediana
      4) >= percentil 0.66
    """
    R = df["R2_adj"].to_numpy()
    attempts = [
        ( (R >= np.nanpercentile(R, 75)) & (df["AD_pass"].eq(1)) & (df["DW_pass"].eq(1)), "q75 + AD&DW" ),
        ( (R >= np.nanpercentile(R, 75)), "q75 only" ),
        ( (R >= np.nanpercentile(R, 50)), "median" ),
        ( (R >= np.nanpercentile(R, 66)), "q66" ),
    ]
    for mask, desc in attempts:
        y = pd.Series(mask.astype(int))
        if y.nunique() >= 2 and y.sum() > 0 and (len(y) - y.sum()) > 0:
            return y, desc
    return pd.Series(np.zeros(len(df), dtype=int)), "failed"

# define 'success' robustamente con fallback
q75     = df_v1["R2_adj"].quantile(0.75)
X = (df_v1[PARAM_COLS]==1).astype(int).to_numpy()
y, y_desc = _pick_labels_with_fallback(df_v1)

if y_desc == "failed":
    print("[V-2] WARNING: No fue posible construir dos clases. Se omite ElasticNet-logistic.")
    # export placeholders
    pd.DataFrame([{ 'AUROC': np.nan, 'note': 'insufficient class variation' }]).to_csv(METRICSDIR/"V2_EN_auc.csv", index=False)
    pd.DataFrame({ 'param': PARAM_COLS, 'coef': [np.nan]*len(PARAM_COLS), 'ci_lo': [np.nan]*len(PARAM_COLS), 'ci_hi': [np.nan]*len(PARAM_COLS) }).to_csv(METRICSDIR/"V2_EN_coefficients.csv", index=False)
else:
    # fit ElasticNet‐penalized logistic
    try:
        encv = ElasticNetCV(l1_ratio=[.1,.5,.9,1], cv=10, random_state=1).fit(X,y)
        alpha = float(encv.alpha_)
        l1 = float(getattr(encv, 'l1_ratio_', 0.5))
        model = LogisticRegression(
            penalty="elasticnet", solver="saga",
            l1_ratio=l1, C=1/max(alpha, 1e-6), max_iter=5000,
            class_weight='balanced'
        ).fit(X,y)
        coefs = model.coef_.flatten()

        # ── stratified bootstrap ───────────────────────────────────
        boot=[]
        rng = np.random.default_rng(0)
        pos_idx = np.where(y==1)[0]
        neg_idx = np.where(y==0)[0]
        n_pos, n_neg = len(pos_idx), len(neg_idx)
        n_boot = 250
        for _ in range(n_boot):
            samp_pos = rng.choice(pos_idx, size=n_pos, replace=True)
            samp_neg = rng.choice(neg_idx, size=n_neg, replace=True)
            idx      = np.concatenate([samp_pos, samp_neg])
            rng.shuffle(idx)
            m = LogisticRegression(
                penalty="elasticnet", solver="saga",
                l1_ratio=l1, C=1/max(alpha,1e-6), max_iter=3000,
                class_weight='balanced'
            ).fit(X[idx], y.iloc[idx])
            boot.append(m.coef_.flatten())
        boot = np.vstack(boot)
        ci_lo, ci_hi = np.percentile(boot, [2.5,97.5], axis=0)

        # ── plot with 95% CI ───────────────────────────────────────
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
        ax.set_title(f"Fig. V-2  Drivers of top-performing models (labels: {y_desc})")
        savefig(fig, "Fig_V2_EN_coeffs.png")

        # report AUROC & confusion; export CSVs
        prob = model.predict_proba(X)[:,1]
        auroc_val = float(roc_auc_score(y, prob))
        cm = confusion_matrix(y, (prob>=0.5).astype(int))
        print("\n[V-2] Labels:", y_desc)
        print("AUROC =", round(auroc_val,3))
        print("Confusion matrix:\n", cm, "\n")
        pd.DataFrame([{ 'AUROC': auroc_val, 'labels': y_desc }]).to_csv(METRICSDIR/"V2_EN_auc.csv", index=False)
        pd.DataFrame(cm, index=["True0","True1"], columns=["Pred0","Pred1"]).to_csv(METRICSDIR/"V2_EN_confusion.csv")
        pd.DataFrame({ 'param': PARAM_COLS, 'coef': coefs, 'ci_lo': ci_lo, 'ci_hi': ci_hi }).to_csv(METRICSDIR/"V2_EN_coefficients.csv", index=False)
        plt.show()
    except Exception as e:
        print(f"[V-2] ERROR entrenando EN-logistic: {e}")
        pd.DataFrame([{ 'AUROC': np.nan, 'note': f'fit error: {e}', 'labels': y_desc }]).to_csv(METRICSDIR/"V2_EN_auc.csv", index=False)
        pd.DataFrame({ 'param': PARAM_COLS, 'coef': [np.nan]*len(PARAM_COLS), 'ci_lo': [np.nan]*len(PARAM_COLS), 'ci_hi': [np.nan]*len(PARAM_COLS) }).to_csv(METRICSDIR/"V2_EN_coefficients.csv", index=False)

# ------------------------------------------------------------------ #
# 5. Figure V-3 – fixation clusters
# ------------------------------------------------------------------ #
bin_matrix = (df_struct.set_index("FFF")[PARAM_COLS]==1).astype(int)

# encuentra k óptimo por silhouette
best = (None, -np.inf, None)
for k in range(2,7):
    km_tmp = KModes(n_clusters=k, random_state=2).fit(bin_matrix)
    sil = silhouette_score(bin_matrix, km_tmp.labels_, metric="hamming")
    if sil > best[1]:
        best = (k, sil, km_tmp)
k_opt = best[0] if best[0] is not None else 2
km = best[2] if best[2] is not None else KModes(n_clusters=int(k_opt), random_state=2).fit(bin_matrix)

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
    vals = df_delta.query("cluster==@cl")['ΔR2'].to_numpy()
    ax.plot([angles[int(cl)]]*len(vals), vals, 'o', label=f"Cluster {cl}")

ax.set_title("Fig. V-3b  ΔR² per cluster")
ax.set_ylim(df_delta['ΔR2'].min() - .05, df_delta['ΔR2'].max() + .05)
ax.set_xticks(angles)
ax.set_xticklabels([f"C{c}" for c in sorted(df_delta['cluster'].unique())])
ax.legend(loc="upper left", bbox_to_anchor=(1,1))
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
    cmap=ListedColormap(["#BC3B3B","#00A878"]),
    cbar=False, linewidths=.3, linecolor="gray",
    ax=ax
)
ax.set_title("Fig. V-6  Residual diagnostics summary")
ax.set_xlabel("Criteria"); ax.set_ylabel("Model ID")
savefig(fig, "Fig_V6_diag_heatmap.png")
plt.show()
print("\nAll figures saved to", OUTDIR.resolve())

# ---------------- Additional metrics & summaries -------------------
# Export cluster ΔR2 stats and silhouette bootstrap for k_opt
try:
    cl_stats = (
        df_delta.groupby('cluster')['ΔR2']
        .agg(['count','mean',lambda x: np.percentile(x,25),lambda x: np.percentile(x,75)])
        .reset_index()
    )
    cl_stats.columns = ['cluster','count','mean','q25','q75']
    cl_stats.to_csv(METRICSDIR/"V3b_cluster_delta_stats.csv", index=False)
    pd.DataFrame([{ 'global_mean': float(df_delta['ΔR2'].mean()), 'global_q25': float(np.percentile(df_delta['ΔR2'],25)), 'global_q75': float(np.percentile(df_delta['ΔR2'],75)) }]) \
      .to_csv(METRICSDIR/"V3b_delta_global_stats.csv", index=False)
except Exception:
    pass

def _sil_boot(mat, k, n=100, seed=3):
    rngb = np.random.default_rng(seed)
    vals=[]
    for _ in range(n):
        idx = rngb.integers(0, mat.shape[0], mat.shape[0])
        km_b = KModes(n_clusters=k, random_state=int(rngb.integers(0, 1<<31))).fit(mat.iloc[idx])
        vals.append(silhouette_score(mat.iloc[idx], km_b.labels_, metric='hamming'))
    return float(np.mean(vals)), tuple(np.percentile(vals, [2.5,97.5]))

try:
    sil_mean, (sil_lo, sil_hi) = _sil_boot((df_struct.set_index("FFF")[PARAM_COLS]==1).astype(int), int(k_opt))
    pd.DataFrame([{ 'k_opt': int(k_opt), 'silhouette_mean': sil_mean, 'silhouette_ci_lo': float(sil_lo), 'silhouette_ci_hi': float(sil_hi) }]) \
      .to_csv(METRICSDIR/"V3a_kmodes_silhouette_bootstrap.csv", index=False)
except Exception:
    pass

# Export decision tree rules, CV accuracy, and feature importances
try:
    rules_txt = export_text(dt, feature_names=PARAM_COLS)
    with open(METRICSDIR/"V4_tree_rules.txt", "w", encoding="utf-8") as f:
        f.write(rules_txt)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
    acc=[]
    for tr, te in skf.split(Xtree, y_bad):
        dt_cv = DecisionTreeClassifier(max_depth=3, random_state=0).fit(Xtree.iloc[tr], y_bad.iloc[tr])
        acc.append(dt_cv.score(Xtree.iloc[te], y_bad.iloc[te]))
    pd.DataFrame([{ 'cv_mean_acc': float(np.mean(acc)), 'cv_std_acc': float(np.std(acc, ddof=1)) }]).to_csv(METRICSDIR/"V4_tree_cv_accuracy.csv", index=False)
    pd.DataFrame({ 'feature': PARAM_COLS, 'importance': dt.feature_importances_ }).to_csv(METRICSDIR/"V4_tree_feature_importances.csv", index=False)
except Exception:
    pass

# Export theta-shift stats
try:
    theta_stats = theta_shift.groupby('param')['rel_shift'].agg(['median', lambda x: (np.asarray(x)>0.3).mean()]).reset_index()
    theta_stats.columns = ['param','median_rel_shift','prop_gt_0p3']
    theta_stats.to_csv(METRICSDIR/"V5_theta_shift_stats.csv", index=False)
except Exception:
    pass

# Coverage and thresholds
cov = {
    'n_rows': int(len(df_v1)),
    'n_structures': int(df_v1['model_id'].nunique()),
    'n_datasets': int(df_v1['Dataset'].nunique())
}
pd.DataFrame([cov]).to_csv(METRICSDIR/"V_cov_coverage.csv", index=False)
q75_global = df_v1['R2_adj'].quantile(0.75)
pd.DataFrame([{ 'q75_global': float(q75_global) }]).to_csv(METRICSDIR/"V_thresholds_q75_global.csv", index=False)
an_melt = df_val.melt(id_vars=['model_id','exper_id','scale_id'], value_vars=r2_cols, var_name='analyte', value_name='r2adj')
an_melt.groupby('analyte')['r2adj'].quantile(0.75).reset_index().to_csv(METRICSDIR/"V_thresholds_q75_by_analyte.csv", index=False)
avg_by_model = df_v1.groupby('model_id')['R2_adj'].mean()
pd.DataFrame([{ 'pct_models_above_q75': float((avg_by_model >= q75_global).mean()) }]).to_csv(METRICSDIR/"V_pct_models_above_q75.csv", index=False)

# Analyte R2_adj stats
an_stats = an_melt.groupby('analyte')['r2adj'].agg(['mean',lambda x: np.percentile(x,25),lambda x: np.percentile(x,75)]).reset_index()
an_stats.columns = ['analyte','mean','q25','q75']
an_stats.to_csv(METRICSDIR/"V_analyte_r2adj_stats.csv", index=False)

# Diagnostic pass rates with bootstrap CIs
def _prop_ci_boot(mask, n=250, seed=2):
    rngb = np.random.default_rng(seed)
    vals = mask.astype(int).to_numpy()
    if len(vals) == 0:
        return (np.nan, np.nan)
    bs = []
    for _ in range(n):
        idx = rngb.integers(0, len(vals), len(vals))
        bs.append(np.mean(vals[idx]))
    return tuple(np.percentile(bs, [2.5,97.5]))

rates=[]
rates.append({ 'scope':'global','criterion':'AD','rate': float(df_v1['AD_pass'].mean()), 'ci_lo': _prop_ci_boot(df_v1['AD_pass'])[0], 'ci_hi': _prop_ci_boot(df_v1['AD_pass'])[1] })
rates.append({ 'scope':'global','criterion':'DW','rate': float(df_v1['DW_pass'].mean()), 'ci_lo': _prop_ci_boot(df_v1['DW_pass'])[0], 'ci_hi': _prop_ci_boot(df_v1['DW_pass'])[1] })
for a, col in zip(['Fructose','Glucose','YAN'], ad_cols):
    mask = (df_val[col] < AD_CRIT_5)
    lo, hi = _prop_ci_boot(mask)
    rates.append({ 'scope': a, 'criterion':'AD', 'rate': float(mask.mean()), 'ci_lo': lo, 'ci_hi': hi })
for a, col in zip(['Fructose','Glucose','YAN'], dw_cols):
    mask = df_val[col].between(1.0, 3.0)
    lo, hi = _prop_ci_boot(mask)
    rates.append({ 'scope': a, 'criterion':'DW', 'rate': float(mask.mean()), 'ci_lo': lo, 'ci_hi': hi })
pd.DataFrame(rates).to_csv(METRICSDIR/"V_analyte_diag_pass_rates.csv", index=False)

# ΔR2 summaries and degradation rates
df_lab = df_v1[df_v1['Dataset'].str.contains('s1')]
df_pil = df_v1[df_v1['Dataset'].str.contains('s2')]
lab_avg = df_lab.groupby('model_id')['R2_adj'].mean()
pil_avg = df_pil.groupby('model_id')['R2_adj'].mean()
delta = (pil_avg - lab_avg).dropna()
pd.DataFrame([{ 'mean': float(delta.mean()), 'q25': float(np.percentile(delta,25)), 'q75': float(np.percentile(delta,75)) }]).to_csv(METRICSDIR/"V_transfer_deltaR2_stats.csv", index=False)
for thr in [-0.10, -0.05]:
    mask = (delta < thr)
    lo, hi = _prop_ci_boot(mask)
    pd.DataFrame([{ 'threshold': thr, 'degradation_rate': float(mask.mean()), 'ci_lo': lo, 'ci_hi': hi }]).to_csv(METRICSDIR/f"V_transfer_degradation_thr_{str(thr).replace('-','m').replace('.','p')}.csv", index=False)

# Pilot R2 pass rate using lab q75
q75_lab = df_lab['R2_adj'].quantile(0.75) if len(df_lab)>0 else q75_global
pilot_mask_R2 = (pil_avg >= q75_lab)
plo, phi = _prop_ci_boot(pilot_mask_R2)
pd.DataFrame([{ 'criterion':'R2_pass_pilot', 'rate': float(pilot_mask_R2.mean()), 'ci_lo': plo, 'ci_hi': phi }]).to_csv(METRICSDIR/"V_pilot_R2_pass_rate.csv", index=False)
 
# ---------------- New: Complementary requested exports ----------------
# Global aggregated R2_adj stats (mean, q25, q75)
try:
    pd.DataFrame([{ 'mean': float(df_v1['R2_adj'].mean()), 'q25': float(np.percentile(df_v1['R2_adj'],25)), 'q75': float(np.percentile(df_v1['R2_adj'],75)) }]) \
      .to_csv(METRICSDIR/"V_global_r2adj_stats.csv", index=False)
except Exception:
    pass

# AUROC 95% CI (bootstrap) and non-zero params list for ElasticNet-logistic
try:
    # Reuse X, y, model, prob from section V-2
    rngb = np.random.default_rng(42)
    n_bs = 500
    aurocs = []
    pos_idx = np.where(y==1)[0]
    neg_idx = np.where(y==0)[0]
    for _ in range(n_bs):
        samp_pos = rngb.choice(pos_idx, size=len(pos_idx), replace=True)
        samp_neg = rngb.choice(neg_idx, size=len(neg_idx), replace=True)
        idx = np.concatenate([samp_pos, samp_neg])
        rngb.shuffle(idx)
        m_bs = LogisticRegression(
            penalty="elasticnet", solver="saga",
            l1_ratio=l1, C=1/alpha, max_iter=3000
        ).fit(X[idx], y[idx])
        prob_bs = m_bs.predict_proba(X[idx])[:,1]
        aurocs.append(roc_auc_score(y[idx], prob_bs))
    lo, hi = np.percentile(aurocs, [2.5, 97.5])
    pd.DataFrame([{ 'AUROC': auroc_val, 'ci_lo': float(lo), 'ci_hi': float(hi), 'n_boot': n_bs }]) \
      .to_csv(METRICSDIR/"V2_EN_auc_ci.csv", index=False)
    # Non-zero coefficients (sparse selection by elasticnet)
    nonzero = pd.DataFrame({ 'param': PARAM_COLS, 'coef': coefs, 'ci_lo': ci_lo, 'ci_hi': ci_hi })
    nonzero = nonzero[nonzero['coef'] != 0].assign(sign=lambda d: np.sign(d['coef']).astype(int))
    nonzero.to_csv(METRICSDIR/"V2_EN_nonzero_params.csv", index=False)
except Exception:
    pass

# ΔR2 by analyte (mean, q25, q75)
try:
    # Melt to analyte level
    an_map = {
        'r2_adj_Fructose': 'Fructose',
        'r2_adj_Glucose':  'Glucose',
        'r2_adj_YAN':      'YAN'
    }
    m = df_val.melt(id_vars=['model_id','exper_id','scale_id'], value_vars=list(an_map.keys()), var_name='analyte_col', value_name='r2adj')
    m['analyte'] = m['analyte_col'].map(an_map)
    # average per model×scale×analyte, then pivot to lab vs pilot
    mp = (m.groupby(['model_id','scale_id','analyte'])['r2adj'].mean().reset_index())
    piv = mp.pivot_table(index=['model_id','analyte'], columns='scale_id', values='r2adj')
    if 1 in piv.columns and 2 in piv.columns:
        dlt = (piv[2] - piv[1]).rename('ΔR2').reset_index()
        stats = dlt.groupby('analyte')['ΔR2'].agg(['mean', lambda x: np.percentile(x,25), lambda x: np.percentile(x,75)]).reset_index()
        stats.columns = ['analyte','mean','q25','q75']
        stats.to_csv(METRICSDIR/"V_transfer_deltaR2_by_analyte.csv", index=False)
except Exception:
    pass

# Co-fixation enrichment in top-transfer (obs/exp ratio, Fisher p, FDR)
try:
    # Use aggregated ΔR2 computed earlier (df_delta)
    thr = np.percentile(df_delta['ΔR2'].dropna(), 75)
    top_models = df_delta.loc[df_delta['ΔR2'] >= thr, 'model_id'].unique().tolist()
    all_models = df_struct['FFF'].astype(int).unique().tolist()
    bin_mat = (df_struct.set_index('FFF')[PARAM_COLS]==1).astype(int)
    # ensure alignment
    bin_all = bin_mat.loc[[m for m in all_models if m in bin_mat.index]]
    bin_top = bin_mat.loc[[m for m in top_models if m in bin_mat.index]]
    n_all = bin_all.shape[0]
    n_top = bin_top.shape[0]
    rows=[]
    for i, j in combinations(range(len(PARAM_COLS)), 2):
        p_i, p_j = PARAM_COLS[i], PARAM_COLS[j]
        co_all = int(((bin_all[p_i]==1) & (bin_all[p_j]==1)).sum())
        co_top = int(((bin_top[p_i]==1) & (bin_top[p_j]==1)).sum())
        exp_top = (co_all / max(n_all,1)) * n_top
        ratio = (co_top / max(exp_top,1e-9)) if n_top>0 else np.nan
        # Fisher exact
        from scipy.stats import fisher_exact
        a = co_top
        b = n_top - co_top
        c = co_all - co_top
        d = (n_all - n_top) - (co_all - co_top)
        table = [[a,b],[c,d]]
        try:
            _, p = fisher_exact(table, alternative='greater')
        except Exception:
            p = np.nan
        rows.append({ 'p_i': p_i, 'p_j': p_j, 'obs_top': a, 'exp_top': float(exp_top), 'ratio_obs_exp': float(ratio), 'p_value': p })
    enr = pd.DataFrame(rows)
    if not enr.empty:
        enr['q_value'] = multipletests(enr['p_value'].fillna(1.0), method='fdr_bh')[1]
    enr.to_csv(METRICSDIR/"V3c_enrichment_cofix_toptransfer.csv", index=False)
except Exception:
    pass

# Theta-shift bootstrap CI for median and add IQR
try:
    def _median_ci_boot(x, n=500, seed=7):
        x = np.asarray(x)
        rng = np.random.default_rng(seed)
        if len(x)==0:
            return (np.nan, np.nan)
        bs=[]
        for _ in range(n):
            idx = rng.integers(0, len(x), len(x))
            bs.append(np.median(x[idx]))
        lo, hi = np.percentile(bs, [2.5,97.5])
        return (float(lo), float(hi))
    out=[]
    for p, g in theta_shift.groupby('param'):
        med = float(np.median(g['rel_shift']))
        q25 = float(np.percentile(g['rel_shift'],25))
        q75 = float(np.percentile(g['rel_shift'],75))
        lo, hi = _median_ci_boot(g['rel_shift'])
        out.append({ 'param': p, 'median': med, 'q25': q25, 'q75': q75, 'ci_lo': lo, 'ci_hi': hi })
    pd.DataFrame(out).to_csv(METRICSDIR/"V5_theta_shift_ci.csv", index=False)
except Exception:
    pass

# Pilot AD/DW pass (per-model, strict all-replicates) and intersection with R2-pass
try:
    pilot_rows = df_v1[df_v1['Dataset'].str.contains('s2')].copy()
    # aggregate per model: require all replicates pass
    agg = pilot_rows.groupby('model_id').agg({ 'AD_pass': 'min', 'DW_pass': 'min', 'R2_adj': 'mean' })
    # R2-pass-pilot threshold is q75_lab computed earlier
    agg['R2_pass'] = (agg['R2_adj'] >= q75_lab).astype(int)
    inter = (agg[['AD_pass','DW_pass','R2_pass']].sum(axis=1) == 3).astype(int)
    # Bootstrap CIs for rates
    def _rate_ci(vals, n=500, seed=11):
        vals = np.asarray(vals).astype(int)
        if len(vals)==0:
            return (np.nan, np.nan)
        rng = np.random.default_rng(seed)
        bs=[]
        for _ in range(n):
            idx = rng.integers(0, len(vals), len(vals))
            bs.append(np.mean(vals[idx]))
        lo, hi = np.percentile(bs,[2.5,97.5])
        return (float(lo), float(hi))
    rows=[]
    for crit in ['AD_pass','DW_pass','R2_pass']:
        lo, hi = _rate_ci(agg[crit])
        rows.append({ 'criterion': crit, 'rate': float(agg[crit].mean()), 'ci_lo': lo, 'ci_hi': hi })
    pd.DataFrame(rows).to_csv(METRICSDIR/"V_pilot_diag_pass_rates.csv", index=False)
    lo, hi = _rate_ci(inter)
    pd.DataFrame([{ 'criterion': 'intersection_AD_DW_R2', 'rate': float(inter.mean()), 'ci_lo': lo, 'ci_hi': hi }]).to_csv(METRICSDIR/"V_pilot_diag_intersection.csv", index=False)
except Exception:
    pass

# Compact matrix per structure with lab/pilot R2, ΔR2 and pilot diagnostics
try:
    # lab and pilot averages
    lab_avg_tbl = df_lab.groupby('model_id')['R2_adj'].mean().rename('R2_lab')
    pil_avg_tbl = df_pil.groupby('model_id')['R2_adj'].mean().rename('R2_pilot')
    mat = pd.concat([lab_avg_tbl, pil_avg_tbl], axis=1).dropna()
    mat['ΔR2'] = mat['R2_pilot'] - mat['R2_lab']
    # pilot diagnostics (strict all-replicates)
    pilot_rows = df_v1[df_v1['Dataset'].str.contains('s2')]
    diag = pilot_rows.groupby('model_id')[['AD_pass','DW_pass']].min().rename(columns={'AD_pass':'AD_pass_pilot','DW_pass':'DW_pass_pilot'})
    mat = mat.merge(diag, left_index=True, right_index=True, how='left')
    mat['R2_pass_pilot'] = (mat['R2_pilot'] >= q75_lab).astype(int)
    mat['intersection'] = ((mat[['AD_pass_pilot','DW_pass_pilot','R2_pass_pilot']].sum(axis=1) == 3).astype(int))
    mat.reset_index().rename(columns={'index':'model_id'}).to_csv(METRICSDIR/"V_top_structures_matrix.csv", index=False)
    (mat.sort_values('R2_pilot', ascending=False).head(15).reset_index().rename(columns={'index':'model_id'})) \
        .to_csv(METRICSDIR/"V_top15_structures_matrix.csv", index=False)
except Exception:
    pass

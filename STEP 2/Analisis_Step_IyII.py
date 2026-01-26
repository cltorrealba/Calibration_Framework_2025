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
import matplotlib as mpl
from matplotlib.ticker import PercentFormatter
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
# PDF export settings (LaTeX-friendly)
mpl.rcParams['pdf.fonttype'] = 42  # TrueType fonts in PDF
mpl.rcParams['ps.fonttype'] = 42
mpl.rcParams['savefig.transparent'] = True
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

def plot_parameter_fixation_tree(df_all, param_cols, param_labels,
                                 save_dir=os.path.join("salidas","figs"),
                                 filename="parameter_fixation_tree_stageII"):
    """
    Single tree-type figure summarizing how parameters are fixed across HIPPO depth,
    considering only viable models (Stage II).

    - X-axis: number of fixed parameters in the structure (n_fixed).
    - Y-axis: model parameters.
    - For each parameter, a branch is drawn through the depth levels.
      The size of each node (bubble) at a given level corresponds to the fraction
      of Stage II structures at that level where that parameter is fixed (1).

    A simpler version than the 3-panel figure: a single image, without PCA or heatmaps,
    showing persistence and fixation patterns of parameters in models classified as viable.
    """
    import os
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns

    os.makedirs(save_dir, exist_ok=True)

    # Basic checks
    if "stage" not in df_all.columns or "estim_params" not in df_all.columns:
        raise ValueError("df_all must contain columns 'stage' and 'estim_params'.")

    # Work ONLY with viable models (Stage II)
    stage2 = df_all[df_all["stage"] == "II"].copy()
    if stage2.empty:
        raise ValueError("No viable models (Stage II) found in df_all.")

    # Use estim_params directly as n_free (number of free/estimated parameters)
    # This aligns with STEP 3 definition: n_free = sum(PARAM_COLS==0)
    stage2["n_free"] = stage2["estim_params"]
    df_all["n_free"] = df_all["estim_params"]

    # Depth: use n_free range from 3 to 9
    depth_levels = sorted(set(int(x) for x in df_all["n_free"].unique() if 3 <= x <= 9))
    if not depth_levels:
        raise ValueError("No depth levels found in n_free range [3, 9].")

    # ------------------------------------------------------------------ #
    # 1) For each depth (n_free) and parameter, fraction of Stage II where #
    #    the parameter is fixed (1 = fixed, 0 = free).                     #
    # ------------------------------------------------------------------ #
    records = []
    for d in depth_levels:
        subset = stage2[stage2["n_free"] == d]
        N = len(subset)
        for p in param_cols:
            if p not in df_all.columns:
                continue
            # If no Stage II at that level, fraction=0 so level appears
            frac_fixed = float((subset[p] == 1).mean()) if N > 0 else 0.0
            count_fixed = int((subset[p] == 1).sum()) if N > 0 else 0
            records.append({
                "depth": d,
                "param": p,
                "frac_fixed": frac_fixed,
                "count_fixed": count_fixed,
                "N_depth": N,
            })

    tree_df = pd.DataFrame(records)
    if tree_df.empty:
        raise ValueError("tree_df is empty – check that param_cols exist in df_all.")

    # Parameter order: from most fixed (on average) to least fixed
    avg_fix = tree_df.groupby("param")["frac_fixed"].mean().sort_values(ascending=False)
    param_order = list(avg_fix.index)

    # Mapping parameter -> vertical position and color
    y_positions = {p: i for i, p in enumerate(param_order)}
    n_params = len(param_order)
    # Numeric scale (fixed fraction) from cool to hot
    cmap = plt.get_cmap("coolwarm")
    norm = mpl.colors.Normalize(vmin=0, vmax=1)

    # ------------------------------------------------------------------ #
    # 2) Plot: x = depth (n_fixed), y = parameter index,                 #
    #    bubble size = fixed fraction (Stage II)                         #
    # ------------------------------------------------------------------ #
    fig, ax = plt.subplots(figsize=(9, 5 + 0.2*n_params))

    # First: draw background histogram showing Stage II model counts per depth
    # This forms a Gaussian-like envelope across the plot
    depth_counts = stage2.groupby("n_free").size()
    max_depth_count = depth_counts.max()
    y_bottom = -0.8
    y_top = len(param_order) - 0.2
    plot_height = y_top - y_bottom
    
    for d in depth_levels:
        count = depth_counts.get(d, 0)
        if count > 0:
            # Normalize height to 80% of plot height for breathing room
            bar_height = 0.8 * plot_height * (count / max_depth_count)
            ax.bar(d, bar_height, width=0.9, bottom=y_bottom, 
                   color='#505050', alpha=0.25, edgecolor='none', zorder=0)
            
            # Add label at top-right corner of each bar
            label_x = d + 0.35
            label_y = y_bottom + bar_height - 0.3
            ax.text(label_x, label_y, f"n={int(count)}", 
                   fontsize=8, ha='right', va='top', color='#404040', 
                   fontweight='bold', alpha=0.8, zorder=1)

    # Second pass: draw branches and nodes on top
    for p in param_order:
        dfp = tree_df[tree_df["param"] == p].sort_values("depth")
        if dfp.empty:
            continue
        xs = dfp["depth"].to_numpy(dtype=float)
        ys = np.full_like(xs, fill_value=y_positions[p], dtype=float)
        frac = dfp["frac_fixed"].to_numpy(dtype=float)
        counts = dfp["count_fixed"].to_numpy(dtype=float)

        # Branch (line) using average branch color (fixed fraction)
        branch_color = cmap(norm(frac.mean())) if len(frac) > 0 else "gray"
        ax.plot(xs, ys, color=branch_color, alpha=0.6, linewidth=1.0, zorder=3)

        # Nodes (bubbles): color = fixed fraction; size = count of Stage II models with parameter fixed
        sizes = np.where(counts > 0, 20.0 + 15.0*np.sqrt(counts), 0.0)
        colors = cmap(norm(frac))
        ax.scatter(xs, ys,
                   s=sizes,
                   color=colors,
                   alpha=0.9,
                   edgecolors="k",
                   linewidths=0.3,
                   zorder=4)

    # Y-axis: parameter names (with LaTeX)
    ax.set_yticks(list(y_positions.values()))
    ax.set_yticklabels([param_labels.get(p, p) for p in param_order])
    ax.set_ylim(-0.8, len(param_order) - 0.2)

    # X-axis: depth (n_free = number of free parameters)
    ax.set_xlabel("Number of free parameters in structure ($n_{\\mathrm{free}}$)")
    ax.set_ylabel("Model parameter")
    ax.set_xticks(depth_levels)
    ax.set_xticklabels(depth_levels)
    ax.set_xlim(min(depth_levels) - 0.5, max(depth_levels) + 0.5)

    # Title aligned with article discourse
    ax.set_title("Parameter fixation tree along Stage II")

    # Soft grid on X-axis to aid reading levels
    ax.grid(axis="x", linestyle="--", alpha=0.3)

    # Color bar with numeric meaning
    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    cbar = fig.colorbar(sm, ax=ax, pad=0.015, fraction=0.04, shrink=0.65)
    cbar.set_label("Fraction of viable models with parameter fixed")

    fig.tight_layout()

    png_path = os.path.join(save_dir, f"{filename}.png")
    pdf_path = os.path.join(save_dir, f"{filename}.pdf")
    fig.savefig(png_path, dpi=350, bbox_inches="tight")
    try:
        fig.savefig(pdf_path, format="pdf", bbox_inches="tight")
    except Exception:
        pass

    plt.close(fig)


# viability mask
mask_viable = (df['CCc']==0) & (df['I955']==0)
df_all = df.copy()
df_all['stage']   = np.where(mask_viable, 'II', 'I')
df_all['n_fixed'] = TOTAL_PARAMS - df_all['estim_params']
df_all['n_free']  = df_all['estim_params']

# Split Stage I / Stage II and attach n_free
stage1 = df_all[df_all['stage']=='I'].copy()
stage2 = df_all[df_all['stage']=='II'].copy()
stage1['n_free'] = stage1['estim_params']
stage2['n_free'] = stage2['estim_params']

# Selective filtering for Stage II: only n_free=7,8 aligned to STEP 3 subset
zenteno_robust_path = '../STEP 3/Zenteno_Final_2023b_WS.xlsx'
stage2_filtered = stage2.copy()
try:
    df_robust = pd.read_excel(zenteno_robust_path, sheet_name='Sheet1')
    valid_fff_codes = set(df_robust['FFF'].unique())

    stage2_n78   = stage2[stage2['n_free'].isin([7, 8])].copy()
    stage2_other = stage2[~stage2['n_free'].isin([7, 8])].copy()
    stage2_n78_filtered = stage2_n78[stage2_n78['FFF'].isin(valid_fff_codes)].copy()

    stage2_filtered = pd.concat([stage2_n78_filtered, stage2_other], ignore_index=True)
    print(f"Fixation tree/histogram: n_free=7,8 filtered to {len(stage2_n78_filtered)} models (STEP 3 subset)")
    print(f"  n_free=7,8 distribution: {dict(stage2_n78_filtered['n_free'].value_counts().sort_index())}")
    print(f"Other tiers: {len(stage2_other)} models (all Stage II)")
    print(f"Total for filtered Stage II: {len(stage2_filtered)} models")
except Exception as e:
    print(f"Warning: Could not load Zenteno_Final file - using full Stage II dataset ({e})")

# Reuse filtered Stage II later (tree, histogram)
stage2_for_tree = stage2_filtered.copy()

# ========================================================================== #
# 2. FIGURE 1 – Panel A (histogram with counts)                              #
# ========================================================================== #
fig1, axA = plt.subplots(figsize=(7,4))
combined_nfree = pd.concat([stage1['n_free'], stage2_filtered['n_free']], ignore_index=True)
min_nfree = int(combined_nfree.min())
max_nfree = int(combined_nfree.max())
bins = np.arange(min_nfree - 0.5, max_nfree + 1.5, 1)
width = bins[1] - bins[0]

# Stage I models (gray)
counts_all, edges_all, _ = axA.hist(
    stage1['n_free'], bins=bins,
    color=PAL_GRAY, alpha=0.4, width=0.45, label='Stage I models'
)
for count, left in zip(counts_all, edges_all[:-1]):
    c = float(count)
    if c > 0:
        center = left + width/2
        axA.text(center, c + 0.3, f'{int(c)}',
                 ha='center', va='bottom', fontsize=8, color='black')

# Stage II models (filtered for n_free=7,8)
bins2 = bins + 0.2
counts2, edges2, _ = axA.hist(
    stage2_filtered['n_free'], bins=bins2,
    color=PAL_BLUE, alpha=0.85, width=0.45, label='Stage II models'
)
for count, left in zip(counts2, edges2[:-1]):
    c = float(count)
    center = left + width/2
    label_y = c + 0.6 if c > 0 else 0.15
    axA.text(center, label_y, f'{int(c)}',
             ha='center', va='bottom', fontsize=8, color=PAL_BLUE)

axA.set_xlabel('Number of Free Parameters ($n_{\mathrm{free}}$)')
axA.set_ylabel('N° of model structures')
axA.set_xticks(np.arange(min_nfree, max_nfree + 1, 1))
axA.legend()
fig1.tight_layout()
fig1.savefig('figure1_histogram_fixed.png', dpi=350)
os.makedirs('salidas/figs', exist_ok=True)
fig1.savefig(os.path.join('salidas','figs','figure1_histogram_fixed.pdf'), dpi=350, bbox_inches='tight')


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
print(f"estim_params mean (all vs retained): {stats['estim_params_all_mean']} -> {stats['estim_params_sel_mean']} (Delta = {stats['avg_complexity_reduction_mean_pars']})")
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

def bootstrap_delta_abs_and_pct(fixed_vals, free_vals, rng, B=1000):
    """Bootstrap 95% CI for absolute and percent deltas.

    Returns:
        (ci_abs_lo, ci_abs_hi, ci_pct_lo, ci_pct_hi)
    """
    fixed_vals = np.asarray(fixed_vals, dtype=float)
    free_vals = np.asarray(free_vals, dtype=float)
    fixed_vals = fixed_vals[np.isfinite(fixed_vals)]
    free_vals = free_vals[np.isfinite(free_vals)]
    nfx, nfr = len(fixed_vals), len(free_vals)
    if nfx < 2 or nfr < 2:
        return (np.nan, np.nan, np.nan, np.nan)

    abs_diffs = []
    pct_diffs = []
    for _ in range(int(B)):
        sfx = fixed_vals[rng.integers(0, nfx, nfx)]
        sfr = free_vals[rng.integers(0, nfr, nfr)]
        mfx = float(np.mean(sfx))
        mfr = float(np.mean(sfr))
        d_abs = mfx - mfr
        abs_diffs.append(d_abs)
        if mfr != 0:
            pct_diffs.append(100.0 * d_abs / mfr)
        else:
            pct_diffs.append(np.nan)

    ci_abs_lo = float(np.nanpercentile(abs_diffs, 2.5))
    ci_abs_hi = float(np.nanpercentile(abs_diffs, 97.5))
    ci_pct_lo = float(np.nanpercentile(pct_diffs, 2.5))
    ci_pct_hi = float(np.nanpercentile(pct_diffs, 97.5))
    return (ci_abs_lo, ci_abs_hi, ci_pct_lo, ci_pct_hi)

for p in PARAM_COLS:
    fixed = stage2[stage2[p]==1][INDICES_HEAT].astype(float)
    free  = stage2[stage2[p]==0][INDICES_HEAT].astype(float)
    for idx in INDICES_HEAT:
        fx = fixed[idx].dropna().values if (idx in fixed.columns) else np.array([], dtype=float)
        fr = free[idx].dropna().values if (idx in free.columns) else np.array([], dtype=float)
        n_models_fixed = int(np.isfinite(fx).sum())
        n_models_free = int(np.isfinite(fr).sum())

        if n_models_fixed == 0 or n_models_free == 0:
            mu_fixed = np.nan
            mu_free = np.nan
            d_abs = np.nan
            d_pct = np.nan
            pval = np.nan
            ci_abs_lo = np.nan
            ci_abs_hi = np.nan
            ci_pct_lo = np.nan
            ci_pct_hi = np.nan
        else:
            mu_fixed = float(np.nanmean(fx))
            mu_free = float(np.nanmean(fr))
            d_abs = mu_fixed - mu_free
            d_pct = 100.0 * d_abs / (mu_free if mu_free != 0 else np.nan)

            # Welch t-test
            if n_models_fixed >= 2 and n_models_free >= 2:
                _, pval = ttest_ind(fx, fr, equal_var=False, nan_policy='omit')
            else:
                pval = np.nan

            # bootstrap CI (absolute and percent deltas)
            ci_abs_lo, ci_abs_hi, ci_pct_lo, ci_pct_hi = bootstrap_delta_abs_and_pct(
                fixed_vals=fx,
                free_vals=fr,
                rng=rng,
                B=1000,
            )

        # Keep legacy columns (delta_pct, ci_low, ci_high) for backward compatibility
        # ci_low/ci_high refer to percent-delta CI.
        delta_rows.append({
            'param': p,
            'index': idx,
            'n_fixed_models': n_models_fixed,
            'n_free_models': n_models_free,
            'mu_fixed': mu_fixed,
            'mu_free': mu_free,
            'delta_abs': float(d_abs) if np.isfinite(d_abs) else np.nan,
            'delta_pct': float(d_pct) if np.isfinite(d_pct) else np.nan,
            'ci_low': ci_pct_lo,
            'ci_high': ci_pct_hi,
            'ci_low_abs': ci_abs_lo,
            'ci_high_abs': ci_abs_hi,
            'p_value': float(pval) if np.isfinite(pval) else np.nan,
        })
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
# 2quinquies. STAGE II RETENTION VS n_fixed (KNEE PLOT)                     #
# ========================================================================== #
# Exact per-integer n_free (estim_params) retention: Stage I denominator, Stage II numerator
grp_all = df_all.groupby('estim_params').size().rename('N_all')
grp_sel = stage2.groupby('estim_params').size().rename('N_retained')
ret_by_nfree = pd.concat([grp_all, grp_sel], axis=1).fillna(0).astype(int).reset_index()\
                  .rename(columns={'estim_params':'n_free'})
ret_by_nfree['retention'] = ret_by_nfree['N_retained'] / ret_by_nfree['N_all'].replace(0, np.nan)

def wilson_ci(k, n, z=1.96):
    if n <= 0:
        return (np.nan, np.nan)
    p = k/n
    den = 1 + z**2/n
    center = (p + z**2/(2*n)) / den
    half = z * np.sqrt(p*(1-p)/n + z**2/(4*n**2)) / den
    lo = max(0.0, center - half)
    hi = min(1.0, center + half)
    return (lo, hi)

# Compute Wilson CI on the n_free table
cis = ret_by_nfree.apply(lambda r: wilson_ci(r['N_retained'], r['N_all']), axis=1, result_type='expand')
ret_by_nfree['ci_lo'] = cis[0]
ret_by_nfree['ci_hi'] = cis[1]

# Knee (elbow) detection: farthest point from the line connecting endpoints
def knee_point(xs, ys):
    xs = np.asarray(xs, dtype=float)
    ys = np.asarray(ys, dtype=float)
    if xs.size < 3:
        return None
    x0, y0 = xs[0], ys[0]
    x1, y1 = xs[-1], ys[-1]
    # line vector
    vx, vy = x1 - x0, y1 - y0
    norm = np.hypot(vx, vy)
    if norm == 0:
        return None
    # distances of each point to the line
    dists = np.abs(vy*(xs - x0) - vx*(ys - y0)) / norm
    idx = int(np.argmax(dists))
    return idx

# Metric for knee quality: deflection angle (degrees)
# Measures the change in slope direction at the knee point
def knee_deflection_angle(xs, ys, knee_idx):
    """
    Computes the knee quality as the change in slope magnitude (steepness).
    
    Returns the ratio: |slope_before| / |slope_after|
    - Ratio > 2.0 means the slope before is >2x steeper than after → SHARP knee
    - Ratio 1.2-2.0 means moderate change in steepness → MODERATE knee
    - Ratio < 1.2 means similar slopes → WEAK knee
    
    Also returns the "deflection angle" as arctan(|slope_before|) - arctan(|slope_after|) 
    in degrees, representing the change in the angle of decline.
    """
    xs = np.asarray(xs, dtype=float)
    ys = np.asarray(ys, dtype=float)
    if knee_idx is None or knee_idx < 1 or knee_idx >= len(xs)-1:
        return np.nan
    
    # Compute slopes (rise/run) before and after knee
    slope_before = (ys[knee_idx] - ys[knee_idx-1]) / (xs[knee_idx] - xs[knee_idx-1])
    slope_after = (ys[knee_idx+1] - ys[knee_idx]) / (xs[knee_idx+1] - xs[knee_idx])
    
    # For visualization: angle of decline in degrees
    # Using absolute values to measure steepness
    abs_slope_before = abs(slope_before)
    abs_slope_after = abs(slope_after)
    
    if abs_slope_before < 1e-9 or abs_slope_after < 1e-9:
        return np.nan
    
    # Deflection angle: difference in the angles of decline
    angle_before = np.degrees(np.arctan(abs_slope_before))
    angle_after = np.degrees(np.arctan(abs_slope_after))
    deflection_angle = angle_before - angle_after
    
    return float(deflection_angle)

ret_by_nfree = ret_by_nfree.sort_values('n_free').reset_index(drop=True)
knee_idx = knee_point(ret_by_nfree['n_free'], ret_by_nfree['retention'])
ret_by_nfree['is_knee'] = False
if knee_idx is not None:
    ret_by_nfree.loc[knee_idx, 'is_knee'] = True

# Export CSV with Stage II Fobj stats by n_free (mean, std, n, 95% CI)
ret_by_out = ret_by_nfree.copy()
fobj_stats = (
    stage2.groupby('estim_params')['Fobj']
          .agg(Fobj_mean='mean', Fobj_std='std', Fobj_n='count')
          .reset_index()
          .rename(columns={'estim_params':'n_free'})
)
ret_by_out = ret_by_out.merge(fobj_stats, on='n_free', how='left')
# 95% CI for the mean (normal approx)
z = 1.96
ret_by_out['Fobj_se'] = ret_by_out['Fobj_std'] / np.sqrt(ret_by_out['Fobj_n'].replace(0, np.nan))
ret_by_out['Fobj_ci_lo'] = ret_by_out['Fobj_mean'] - z * ret_by_out['Fobj_se']
ret_by_out['Fobj_ci_hi'] = ret_by_out['Fobj_mean'] + z * ret_by_out['Fobj_se']

ret_by_out['retention_pct'] = (100*ret_by_out['retention']).round(2)
ret_by_out['ci_lo_pct'] = (100*ret_by_out['ci_lo']).round(2)
ret_by_out['ci_hi_pct'] = (100*ret_by_out['ci_hi']).round(2)
ret_by_out.to_csv(os.path.join('salidas','retention_by_nfree_counts.csv'), index=False)

# Plot
figK, axK = plt.subplots(figsize=(7.5, 4.2))
# Plot range restriction to focus on reliable sample sizes
min_free, max_free = 3, 9
mask_plot = (ret_by_out['n_free'] >= min_free) & (ret_by_out['n_free'] <= max_free)
ret_plot = ret_by_out[mask_plot].copy()
if ret_plot.empty:
    # Fallback to all if range not available
    ret_plot = ret_by_out.copy()
    min_free = int(ret_plot['n_free'].min())
    max_free = int(ret_plot['n_free'].max())

x = ret_plot['n_free'].to_numpy(dtype=float)
y = ret_plot['retention'].to_numpy(dtype=float)
ylo = ret_plot['ci_lo'].to_numpy(dtype=float)
yhi = ret_plot['ci_hi'].to_numpy(dtype=float)

# Curve and points (no retention shading)
axK.plot(x, y, color=PAL_BLUE, linewidth=2, label='Retention')
axK.scatter(x, y, color=PAL_BLUE, s=45, zorder=3)

# Knee annotation (visual only; no legend label) — recompute on filtered data
knee_idx_plot = knee_point(x, y)
if knee_idx_plot is not None:
    kx = x[knee_idx_plot]; ky = y[knee_idx_plot]
    axK.scatter([kx], [ky], color='orange', edgecolors='black', s=120, marker='*', zorder=4, label='_nolegend_')
    axK.axvline(kx, color='orange', linestyle=':', linewidth=1)

# Secondary axis: Fobj mean (Stage II) by n_free with 95% CI shading
axK2 = axK.twinx()
fobj_mean = ret_plot['Fobj_mean'].to_numpy(dtype=float)
fobj_lo = ret_plot['Fobj_ci_lo'].to_numpy(dtype=float)
fobj_hi = ret_plot['Fobj_ci_hi'].to_numpy(dtype=float)
axK2.fill_between(x, fobj_lo, fobj_hi, color=PAL_3, alpha=0.18, linewidth=0)
axK2.plot(x, fobj_mean, color=PAL_3, linewidth=1.8, marker='o', alpha=0.95, label='Fobj (mean)')
axK2.set_ylabel('Fobj (mean)')

axK.set_xlabel('Number of Free Parameters (n_free)')
axK.set_ylabel('Retention (share kept)')
axK.set_title('Stage II – Retention vs number of free parameters')
axK.set_xticks(list(ret_plot['n_free'].astype(int).to_list()))
axK.set_ylim(0, 1.0)
axK.yaxis.set_major_formatter(PercentFormatter(1.0))
axK.grid(True, axis='y', alpha=0.25)
# Combined legend (upper-left)
handles1, labels1 = axK.get_legend_handles_labels()
handles2, labels2 = axK2.get_legend_handles_labels()
axK.legend(handles1 + handles2, labels1 + labels2, loc='upper left', frameon=False)
figK.tight_layout()
os.makedirs(os.path.join('salidas','figs'), exist_ok=True)
figK.savefig(os.path.join('salidas','figs','stage2_retention_knee_nfree.png'), dpi=350)
figK.savefig(os.path.join('salidas','figs','stage2_retention_knee_nfree.pdf'), dpi=350, bbox_inches='tight')
plt.close(figK)

# Export knee-related metrics associated to the figure
try:
    os.makedirs('salidas', exist_ok=True)
    ret_plot = ret_plot.copy()
    ret_plot['is_knee_plot'] = False
    if knee_idx_plot is not None and len(ret_plot) > 0:
        knee_pos = int(knee_idx_plot)
        ret_plot.at[ret_plot.index[knee_pos], 'is_knee_plot'] = True
        knee_row = ret_plot.iloc[knee_pos]
        knee_n_free = int(knee_row['n_free']) if not pd.isna(knee_row['n_free']) else np.nan
        
        # KNEE QUALITY METRIC: deflection angle (degrees)
        x_vals = ret_plot['n_free'].values.astype(float)
        y_vals = ret_plot['retention'].values.astype(float)
        deflection_angle = knee_deflection_angle(x_vals, y_vals, knee_idx_plot)
        
        # Local slopes for retention around knee (finite differences)
        idx = knee_pos
        slope_left = np.nan
        slope_right = np.nan
        if idx-1 >= 0:
            slope_left = (ret_plot.iloc[idx]['retention'] - ret_plot.iloc[idx-1]['retention']) / (ret_plot.iloc[idx]['n_free'] - ret_plot.iloc[idx-1]['n_free'])
        if idx+1 < len(ret_plot):
            slope_right = (ret_plot.iloc[idx+1]['retention'] - ret_plot.iloc[idx]['retention']) / (ret_plot.iloc[idx+1]['n_free'] - ret_plot.iloc[idx]['n_free'])
        # Correlations in plot range
        rho_ret = pd.Series(ret_plot['n_free']).corr(ret_plot['retention'], method='spearman')
        rho_fobj = pd.Series(ret_plot['n_free']).corr(ret_plot['Fobj_mean'], method='spearman')
        summary = pd.DataFrame([
            {
                'range_min_n_free': int(min_free),
                'range_max_n_free': int(max_free),
                'knee_n_free': knee_n_free,
                'knee_retention': float(knee_row['retention']),
                'knee_retention_ci_lo': float(knee_row['ci_lo']),
                'knee_retention_ci_hi': float(knee_row['ci_hi']),
                'knee_N_all': int(knee_row['N_all']) if not pd.isna(knee_row['N_all']) else np.nan,
                'knee_N_retained': int(knee_row['N_retained']) if not pd.isna(knee_row['N_retained']) else np.nan,
                'knee_Fobj_mean': float(knee_row['Fobj_mean']),
                'knee_Fobj_ci_lo': float(knee_row['Fobj_ci_lo']) if not pd.isna(knee_row['Fobj_ci_lo']) else np.nan,
                'knee_Fobj_ci_hi': float(knee_row['Fobj_ci_hi']) if not pd.isna(knee_row['Fobj_ci_hi']) else np.nan,
                'knee_Fobj_n': int(knee_row['Fobj_n']) if not pd.isna(knee_row['Fobj_n']) else np.nan,
                'knee_deflection_angle_deg': round(deflection_angle, 2) if np.isfinite(deflection_angle) else np.nan,
                'retention_slope_left': float(slope_left) if slope_left == slope_left else np.nan,
                'retention_slope_right': float(slope_right) if slope_right == slope_right else np.nan,
                'spearman_rho_nfree_retention': float(rho_ret) if not pd.isna(rho_ret) else np.nan,
                'spearman_rho_nfree_fobjmean': float(rho_fobj) if not pd.isna(rho_fobj) else np.nan,
            }
        ])
    else:
        summary = pd.DataFrame([
            {
                'range_min_n_free': int(min_free),
                'range_max_n_free': int(max_free),
                'knee_n_free': np.nan,
                'knee_retention': np.nan,
                'knee_retention_ci_lo': np.nan,
                'knee_retention_ci_hi': np.nan,
                'knee_N_all': np.nan,
                'knee_N_retained': np.nan,
                'knee_Fobj_mean': np.nan,
                'knee_Fobj_ci_lo': np.nan,
                'knee_Fobj_ci_hi': np.nan,
                'knee_Fobj_n': np.nan,
                'knee_deflection_angle_deg': np.nan,
                'retention_slope_left': np.nan,
                'retention_slope_right': np.nan,
                'spearman_rho_nfree_retention': np.nan,
                'spearman_rho_nfree_fobjmean': np.nan,
            }
        ])
    # Save summary and plot-range table
    summary.to_csv(os.path.join('salidas','stage2_knee_summary.csv'), index=False)
    ret_plot.to_csv(os.path.join('salidas','retention_by_nfree_counts_plotrange.csv'), index=False)
    
    # Print knee quality metric to console
    print("\n=== KNEE QUALITY METRIC ===")
    if knee_idx_plot is not None and len(ret_plot) > 0:
        deflection = summary.iloc[0]['knee_deflection_angle_deg']
        n_free = summary.iloc[0]['knee_n_free']
        retention = summary.iloc[0]['knee_retention']
        if not pd.isna(deflection):
            quality = "SHARP" if deflection > 30 else "MODERATE" if deflection > 15 else "WEAK"
            print(f"Knee at n_free = {int(n_free)} (retention = {retention:.1%})")
            print(f"Slope deflection = {deflection:.2f}° [{quality} change in steepness]")
        else:
            print("Could not compute deflection angle")
    else:
        print("No knee point found")
except Exception as e:
    print(f"[WARN] Could not export knee summary: {e}")


# ========================================================================== #
# 3. FIGURE 2 – Complexity-stratified grid (FixFreq | PCA | Heat-map)         #
# ========================================================================== #
tiers_all = sorted(stage2['estim_params'].unique(), reverse=True)
# Exclude rows (tiers) with 9 and 3 free parameters to reduce figure height
exclude_tiers = {9, 3}
tiers = [t for t in tiers_all if t not in exclude_tiers]
n_rows = len(tiers)
# Slightly reduce per-row height for a more compact grid
row_height = 4.0
fig2, axes = plt.subplots(n_rows, 3, figsize=(18, row_height*n_rows),
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
os.makedirs('salidas/figs', exist_ok=True)
pdf_path = os.path.join('salidas','figs','stage2_Fig_complexity_grid.pdf')
try:
    fig2.savefig(pdf_path, format='pdf', bbox_inches='tight')
except PermissionError:
    # write with a versioned name if previous is open
    fig2.savefig(os.path.join('salidas','figs','stage2_Fig_complexity_grid_v2.pdf'), format='pdf', bbox_inches='tight')


# ========================================================================== #
# FIGURA – Árbol de fijación de parámetros (versión simple para el artículo) #
# ========================================================================== #

# Reuse the filtered Stage II set (n_free=7,8 aligned to STEP 3)
df_all_filtered = stage2_for_tree.copy()

plot_parameter_fixation_tree(
    df_all=df_all_filtered,
    param_cols=PARAM_COLS,
    param_labels=param_labels,
)


# ========================================================================== #
# TABLE S1: STAGE I ROBUSTNESS DIAGNOSTICS                                   #
# ========================================================================== #
print("\n=== Generating Table S1: Stage I Robustness Diagnostics ===")

def compute_robust_stats(x):
    """Compute robust statistics for a given metric array."""
    return {
        'mean': float(np.mean(x)),
        'std': float(np.std(x, ddof=1)),
        'median': float(np.median(x)),
        'q1': float(np.percentile(x, 25)),
        'q3': float(np.percentile(x, 75)),
        'iqr': float(np.percentile(x, 75) - np.percentile(x, 25)),
        'min': float(np.min(x)),
        'max': float(np.max(x)),
        'p5': float(np.percentile(x, 5)),
        'p95': float(np.percentile(x, 95)),
    }

def count_tukey_outliers(x):
    """Count outliers using Tukey's fences (1.5 * IQR rule)."""
    q1 = np.percentile(x, 25)
    q3 = np.percentile(x, 75)
    iqr = q3 - q1
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr
    n_outliers = int(np.sum((x < lower_fence) | (x > upper_fence)))
    return n_outliers, lower_fence, upper_fence

# Table S1A: Overall Stage I population statistics (all models)
print("  Computing overall Stage I statistics...")
table_s1a_rows = []
for metric_name in ['Akaike', 'MeanCC', 'Fobj']:
    x = df_all[metric_name].astype(float).values
    stats = compute_robust_stats(x)
    n_outliers, lower_fence, upper_fence = count_tukey_outliers(x)
    
    table_s1a_rows.append({
        'Metric': metric_name,
        'N': len(x),
        'Mean': stats['mean'],
        'SD': stats['std'],
        'Median': stats['median'],
        'Q1': stats['q1'],
        'Q3': stats['q3'],
        'IQR': stats['iqr'],
        'Min': stats['min'],
        'Max': stats['max'],
        'P5': stats['p5'],
        'P95': stats['p95'],
        'N_Outliers': n_outliers,
        'Lower_Fence': lower_fence,
        'Upper_Fence': upper_fence,
    })

table_s1a = pd.DataFrame(table_s1a_rows)

# Table S1B: Statistics by n_fixed category
print("  Computing statistics by n_fixed category...")
table_s1b_rows = []
for n_fix in sorted(df_all['n_fixed'].unique()):
    df_subset = df_all[df_all['n_fixed'] == n_fix]
    n_models = len(df_subset)
    
    for metric_name in ['Akaike', 'MeanCC', 'Fobj']:
        x = df_subset[metric_name].astype(float).values
        stats = compute_robust_stats(x)
        n_outliers, lower_fence, upper_fence = count_tukey_outliers(x)
        
        table_s1b_rows.append({
            'n_fixed': int(n_fix),
            'Metric': metric_name,
            'N_models': n_models,
            'Mean': stats['mean'],
            'SD': stats['std'],
            'Median': stats['median'],
            'Q1': stats['q1'],
            'Q3': stats['q3'],
            'IQR': stats['iqr'],
            'P5': stats['p5'],
            'P95': stats['p95'],
            'N_Outliers': n_outliers,
        })

table_s1b = pd.DataFrame(table_s1b_rows)

# Table S1C: Spearman correlation analysis (sensitivity to n_fixed)
print("  Computing Spearman correlations with n_fixed...")
table_s1c_rows = []
for metric_name in ['Akaike', 'MeanCC', 'Fobj']:
    rho, pval = spearmanr(df_all['n_fixed'], df_all[metric_name])
    
    table_s1c_rows.append({
        'Metric': metric_name,
        'Spearman_rho': float(rho),
        'p_value': float(pval),
        'Significance': 'p < 0.001' if pval < 0.001 else f'p = {pval:.4f}',
    })

table_s1c = pd.DataFrame(table_s1c_rows)

# Save all tables
table_s1a.round(4).to_csv(os.path.join('salidas', 'tableS1A_overall_stats.csv'), index=False)
table_s1b.round(4).to_csv(os.path.join('salidas', 'tableS1B_stats_by_nfixed.csv'), index=False)
table_s1c.round(4).to_csv(os.path.join('salidas', 'tableS1C_spearman_sensitivity.csv'), index=False)

print("\n  Table S1 components saved:")
print(f"    - tableS1A_overall_stats.csv (overall population)")
print(f"    - tableS1B_stats_by_nfixed.csv (by complexity category)")
print(f"    - tableS1C_spearman_sensitivity.csv (sensitivity analysis)")

# Optional: Generate LaTeX-ready combined table
print("\n  Generating LaTeX-formatted Table S1...")

# Create a comprehensive LaTeX table string
latex_lines = []
latex_lines.append(r"\begin{table}[h!]")
latex_lines.append(r"\centering")
latex_lines.append(r"\caption{Stage I Robustness Diagnostics: Overall statistics, category-wise breakdown, and sensitivity analysis for key model selection indices.}")
latex_lines.append(r"\label{tab:S1}")
latex_lines.append(r"\small")
latex_lines.append(r"\begin{tabular}{llrrrrrrr}")
latex_lines.append(r"\hline")
latex_lines.append(r"\textbf{Part A: Overall Statistics} & & & & & & & & \\")
latex_lines.append(r"\hline")
latex_lines.append(r"Metric & N & Mean & SD & Median & IQR & P5--P95 & N$_{\mathrm{outliers}}$ \\")
latex_lines.append(r"\hline")

for _, row in table_s1a.iterrows():
    metric = row['Metric']
    if metric == 'Akaike':
        metric_label = 'AICc'
    elif metric == 'MeanCC':
        metric_label = r'$\overline{CC_p}$'
    else:
        metric_label = r'$F_{\mathrm{obj}}$'
    
    latex_lines.append(
        f"{metric_label} & {row['N']:.0f} & {row['Mean']:.2f} & {row['SD']:.2f} & "
        f"{row['Median']:.2f} & {row['IQR']:.2f} & {row['P5']:.2f}--{row['P95']:.2f} & "
        f"{row['N_Outliers']:.0f} \\\\"
    )

latex_lines.append(r"\hline")
latex_lines.append(r"\textbf{Part B: By Complexity Category} (selected $n_{\mathrm{fixed}}$ values) & & & & & & & & \\")
latex_lines.append(r"\hline")
latex_lines.append(r"$n_{\mathrm{fixed}}$ & Metric & N & Mean & Median & IQR & P5--P95 & N$_{\mathrm{outliers}}$ \\")
latex_lines.append(r"\hline")

# Show a subset of n_fixed values for brevity (4, 5, 6, 7, 8, 9, 10)
for n_fix in [4, 5, 6, 7, 8, 9, 10]:
    subset = table_s1b[table_s1b['n_fixed'] == n_fix]
    for _, row in subset.iterrows():
        metric = row['Metric']
        if metric == 'Akaike':
            metric_label = 'AICc'
        elif metric == 'MeanCC':
            metric_label = r'$\overline{CC_p}$'
        else:
            metric_label = r'$F_{\mathrm{obj}}$'
        
        latex_lines.append(
            f"{n_fix} & {metric_label} & {row['N_models']:.0f} & {row['Mean']:.2f} & "
            f"{row['Median']:.2f} & {row['IQR']:.2f} & {row['P5']:.2f}--{row['P95']:.2f} & "
            f"{row['N_Outliers']:.0f} \\\\"
        )

latex_lines.append(r"\hline")
latex_lines.append(r"\textbf{Part C: Sensitivity Analysis (Spearman correlation with $n_{\mathrm{fixed}}$)} & & & & & & & & \\")
latex_lines.append(r"\hline")
latex_lines.append(r"Metric & $\rho$ & $p$-value & Interpretation & & & & \\")
latex_lines.append(r"\hline")

for _, row in table_s1c.iterrows():
    metric = row['Metric']
    if metric == 'Akaike':
        metric_label = 'AICc'
    elif metric == 'MeanCC':
        metric_label = r'$\overline{CC_p}$'
    else:
        metric_label = r'$F_{\mathrm{obj}}$'
    
    interp = "Strong negative" if row['Spearman_rho'] < -0.7 else \
             "Moderate negative" if row['Spearman_rho'] < -0.3 else \
             "Weak" if abs(row['Spearman_rho']) < 0.3 else \
             "Moderate positive" if row['Spearman_rho'] < 0.7 else "Strong positive"
    
    latex_lines.append(
        f"{metric_label} & {row['Spearman_rho']:.3f} & {row['Significance']} & {interp} & & & & \\\\"
    )

latex_lines.append(r"\hline")
latex_lines.append(r"\end{tabular}")
latex_lines.append(r"\end{table}")

# Save LaTeX table
with open(os.path.join('salidas', 'tableS1_latex.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(latex_lines))

print(f"    - tableS1_latex.txt (LaTeX-formatted table)")
print("\n=== Table S1 generation complete ===\n")

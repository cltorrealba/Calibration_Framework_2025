#!/usr/bin/env python3
"""
Stage-IV analysis – Optimal model-structure selection   (FULL REVISED SCRIPT)
Author: <your name> – May 2025
"""

# ─────────────────────────────────────────────────────────────────────────────
# 0  Imports & constants
# ─────────────────────────────────────────────────────────────────────────────
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import fisher_exact, spearmanr, kendalltau, ttest_ind
from itertools import combinations
import os
from mpl_toolkits.mplot3d import Axes3D   # noqa: F401 (needed for 3-D)
from matplotlib import cm

# ❶  FILE PATHS  ── adjust if required
HIPPO_PATH  = r"C:/Users/ctorrealba/OneDrive - Viña Concha y Toro S.A/Documentos/Doctorado/Artículos/Artículo - Estimación/Codes/STEP 2/HIPPO_result.xlsx"
ROBUST_PATH = r"C:/Users/ctorrealba/OneDrive - Viña Concha y Toro S.A/Documentos/Doctorado/Artículos/Artículo - Estimación/Codes/STEP 3/Zenteno_Final_2023b_WS.xlsx"

# ❷  Parameter meta-data
PARAM_COLS = ['mu0','betaG0','betaF0','Kn0','Kg0','Kf0','Kig0','Kie0',
              'Yxn','Yxg','Yxf','Yeg','Yef']

PARAM_LABELS = {
    'mu0': r'$\mu_0$',  'betaG0': r'$\beta_{G0}$',  'betaF0': r'$\beta_{F0}$',
    'Kn0': r'$K_{n0}$', 'Kg0': r'$K_{g0}$', 'Kf0': r'$K_{f0}$',
    'Kig0': r'$K_{ig0}$', 'Kie0': r'$K_{ie0}$',
    'Yxn': r'$Y_{xn}$',  'Yxg': r'$Y_{xg}$',  'Yxf': r'$Y_{xf}$',
    'Yeg': r'$Y_{eg}$',  'Yef': r'$Y_{ef}$',
}

WEIGHT_SCENARIOS = {
    'No-priority'    : dict(AICc=0.25, MNCI=0.25, RSQ2=0.25, GSS=0.25),
    'Parsimony'      : dict(AICc=0.70, MNCI=0.10, RSQ2=0.10, GSS=0.10),
    'Goodness-of-fit': dict(AICc=0.10, MNCI=0.10, RSQ2=0.70, GSS=0.10),
    'Identifiability': dict(AICc=0.10, MNCI=0.70, RSQ2=0.10, GSS=0.10),
    'Sensitivity'    : dict(AICc=0.10, MNCI=0.10, RSQ2=0.10, GSS=0.70),
}
CRIT_SENSE = dict(AICc='min', MNCI='min', RSQ2='max', GSS='max')

# ─────────────────────────────────────────────────────────────────────────────
# 1  Load & harmonise data
# ─────────────────────────────────────────────────────────────────────────────
hippo  = pd.read_excel(HIPPO_PATH)
robust = pd.read_excel(ROBUST_PATH)

mask_viable = (hippo['CCc'] == 0) & (hippo['I955'] == 0)
struct_df   = hippo.loc[mask_viable].copy()

struct_df = struct_df.rename(columns={'FFF':'model_id'})
robust    = robust.rename(columns={'FFF':'model_id'})

models = (struct_df
          .merge(robust, on='model_id', how='inner')
          .set_index('model_id'))

# ─────────────────────────────────────────────────────────────────────────────
# 2  Helper functions – MCDM algorithms
# ─────────────────────────────────────────────────────────────────────────────
def _normalise(df, senses):
    out = df.copy()
    for c, s in senses.items():
        rng = df[c].max() - df[c].min()
        if rng == 0:
            out[c] = 0
        elif s == 'min':
            out[c] = (df[c].max() - df[c]) / rng
        else:
            out[c] = (df[c] - df[c].min()) / rng
    return out

def _topsis(n,w):
    v_plus, v_minus = (n*w).max(), (n*w).min()
    s_plus  = np.sqrt(((n*w - v_plus )**2).sum(axis=1))
    s_minus = np.sqrt(((n*w - v_minus)**2).sum(axis=1))
    return (s_minus/(s_plus+s_minus)).rank(ascending=False)

def _linmap(n,w):
    v_plus = (n*w).max()
    return np.sqrt(((n*w - v_plus)**2).sum(axis=1)).rank()

def _vikor(n,w,v=0.5):
    f_star = (n*w).max(); s=((f_star-n*w).abs()).sum(axis=1)
    r=((f_star-n*w).abs()).max(axis=1)
    q=v*(s-s.min())/(s.max()-s.min())+(1-v)*(r-r.min())/(r.max()-r.min())
    return q.rank()

def _saw(n,w): return (n*w).sum(axis=1).rank(ascending=False)
def _mew(n,w): return np.prod(np.power(n,w),axis=1).rank(ascending=False)

def _gra(df, w):
    ref=df.max(); num=np.abs(ref-df); gamma=1
    rel=(num.min().min()+gamma*num.max().max())/(num+gamma*num.max().max())
    return rel.mean(axis=1).rank(ascending=False)

def _fuca(rank_df,w): return (rank_df*w).sum(axis=1).rank()

MCDM_FUNCS={'TOPSIS':_topsis,'LINMAP':_linmap,'VIKOR':_vikor,
            'SAW':_saw,'MEW':_mew,'GRA':_gra,'FUCA':_fuca}

# ─────────────────────────────────────────────────────────────────────────────
# 3  Rankings & votes
# ─────────────────────────────────────────────────────────────────────────────
results=[]
for scen,w_dict in WEIGHT_SCENARIOS.items():
    w=pd.Series(w_dict)
    nrm=_normalise(models[w.index], CRIT_SENSE)
    crit_ranks=nrm.rank(ascending=False, axis=0)
    for m,func in MCDM_FUNCS.items():
        ranks=func(crit_ranks if m=='FUCA' else nrm, w).astype(int)
        results.append({'scenario':scen,'method':m,'ranks':ranks,
                        'best_model':ranks.idxmin()})

vote_df=(pd.DataFrame(results)
         .groupby('best_model').size().rename('votes'))
models=models.join(vote_df,how='left').fillna({'votes':0})

# top-statistics
# Top-15 se definirá más abajo tras calcular fitness_mean (desempaate por fitness)
best_id    = int(models['votes'].idxmax())
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'salidas')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# 3.1  Supporting indicators (i–xii)
# ─────────────────────────────────────────────────────────────────────────────
# Build full rank matrix across all method–scenario combinations
rank_blocks = []
keys = []
for r in results:
    ser = r['ranks'].reindex(models.index)
    rank_blocks.append(ser)
    keys.append(f"{r['method']}::{r['scenario']}")
rank_matrix_all = pd.concat(rank_blocks, axis=1)
rank_matrix_all.columns = keys
max_rank_all = rank_matrix_all.max().max()
fitness_all = 1 - (rank_matrix_all - 1) / (max_rank_all - 1)

# (i) Consensus strength: vote share and dispersion of rank/fitness
consensus_df = pd.DataFrame(index=models.index)
consensus_df['votes'] = models['votes']
consensus_df['vote_share'] = models['votes'] / float(len(WEIGHT_SCENARIOS) * len(MCDM_FUNCS))
consensus_df['rank_sd'] = rank_matrix_all.std(axis=1, ddof=1)
consensus_df['rank_iqr'] = rank_matrix_all.quantile(0.75, axis=1) - rank_matrix_all.quantile(0.25, axis=1)
consensus_df['fitness_mean'] = fitness_all.mean(axis=1)
consensus_df['fitness_sd'] = fitness_all.std(axis=1, ddof=1)
consensus_df['fitness_iqr'] = fitness_all.quantile(0.75, axis=1) - fitness_all.quantile(0.25, axis=1)
consensus_df.sort_values(['votes','fitness_mean'], ascending=[False, False]).to_csv(os.path.join(OUTPUT_DIR,'Stage4_consensus_strength.csv'))

# Definir Top-15: por votos y, en caso de empate (incluyendo cero votos), por mayor fitness medio
_ordered = consensus_df.sort_values(['votes','fitness_mean'], ascending=[False, False])
top15_ids = _ordered.head(15).index
_ordered.head(15).assign(top15_rank=range(1, 1+min(15, len(_ordered)))).to_csv(
    os.path.join(OUTPUT_DIR,'Stage4_top15_selection.csv')
)

# (ii) Scenario stability: Jaccard overlap of Top-k sets across scenarios
def scenario_topk_sets(k=15):
    sets = {}
    for scen, w in WEIGHT_SCENARIOS.items():
        # average fitness within scenario across methods
        cols = [f"{m}::{scen}" for m in MCDM_FUNCS]
        f = fitness_all[cols].mean(axis=1)
        sets[scen] = set(f.sort_values(ascending=False).head(k).index)
    return sets

def pairwise_jaccard(sets_dict):
    scen_names = list(sets_dict.keys())
    rows = []
    for i in range(len(scen_names)):
        for j in range(i+1, len(scen_names)):
            a, b = scen_names[i], scen_names[j]
            A, B = sets_dict[a], sets_dict[b]
            inter = len(A & B); union = len(A | B)
            jacc = inter / union if union else np.nan
            rows.append({'scenario_a': a, 'scenario_b': b, 'jaccard': jacc, 'intersect': inter, 'union': union})
    return pd.DataFrame(rows)

sets_k10 = scenario_topk_sets(k=10)
sets_k15 = scenario_topk_sets(k=15)
j10 = pairwise_jaccard(sets_k10); j15 = pairwise_jaccard(sets_k15)
j10.to_csv(os.path.join(OUTPUT_DIR,'Stage4_scenario_jaccard_k10.csv'), index=False)
j15.to_csv(os.path.join(OUTPUT_DIR,'Stage4_scenario_jaccard_k15.csv'), index=False)
stab_summary = pd.DataFrame({
    'k': [10, 15],
    'mean_jaccard': [float(j10['jaccard'].mean()), float(j15['jaccard'].mean())],
    'min_jaccard': [float(j10['jaccard'].min()), float(j15['jaccard'].min())],
    'max_jaccard': [float(j10['jaccard'].max()), float(j15['jaccard'].max())]
})
stab_summary.to_csv(os.path.join(OUTPUT_DIR,'Stage4_scenario_stability_summary.csv'), index=False)

# (iii) Cross-method agreement: within-scenario rank correlations
rows = []
for scen in WEIGHT_SCENARIOS.keys():
    cols = [f"{m}::{scen}" for m in MCDM_FUNCS]
    for a, b in combinations(cols, 2):
        ra = pd.to_numeric(rank_matrix_all[a], errors='coerce')
        rb = pd.to_numeric(rank_matrix_all[b], errors='coerce')
        # Use pandas corr to avoid tuple handling
        rho_val = ra.corr(rb, method='spearman')
        rows.append({'scenario': scen, 'pair': f"{a} vs {b}", 'spearman_rho': float(rho_val) if pd.notna(rho_val) else np.nan})
cross_agree = pd.DataFrame(rows)
cross_agree.to_csv(os.path.join(OUTPUT_DIR,'Stage4_cross_method_agreement.csv'), index=False)
agree_summary = cross_agree.groupby('scenario')['spearman_rho'].agg(['mean','min','max']).reset_index()
agree_summary.to_csv(os.path.join(OUTPUT_DIR,'Stage4_cross_method_agreement_summary.csv'), index=False)

# (iv) Fitness contrast Top-15 vs rest
fitness_mean = consensus_df['fitness_mean']
top_mask = fitness_mean.index.isin(top15_ids)
mu_top = float(fitness_mean[top_mask].mean()); mu_rest = float(fitness_mean[~top_mask].mean())
sd_top = float(fitness_mean[top_mask].std(ddof=1)); sd_rest = float(fitness_mean[~top_mask].std(ddof=1))
n_top = int(top_mask.sum()); n_rest = int((~top_mask).sum())
sp = np.sqrt(((n_top-1)*sd_top**2 + (n_rest-1)*sd_rest**2) / (n_top + n_rest - 2)) if n_top>1 and n_rest>1 else np.nan
cohens_d = (mu_top - mu_rest) / sp if sp>0 else np.nan
# 95% CI for mean difference (normal approx)
se_diff = np.sqrt(sd_top**2/n_top + sd_rest**2/n_rest) if n_top>0 and n_rest>0 else np.nan
ci_lo = (mu_top - mu_rest) - 1.96*se_diff if np.isfinite(se_diff) else np.nan
ci_hi = (mu_top - mu_rest) + 1.96*se_diff if np.isfinite(se_diff) else np.nan
pd.DataFrame([{
    'mu_top15': mu_top, 'mu_rest': mu_rest,
    'diff_mu': mu_top - mu_rest, 'diff_95ci_lo': ci_lo, 'diff_95ci_hi': ci_hi,
    'cohens_d': float(cohens_d) if np.isfinite(cohens_d) else np.nan,
    'n_top15': n_top, 'n_rest': n_rest
}]).to_csv(os.path.join(OUTPUT_DIR,'Stage4_fitness_contrast.csv'), index=False)

# (v) Landscape geometry: distances to Top-15 centroid in {AICc, MNCI, RSQ2}
geom_cols = ['AICc','MNCI','RSQ2']
scaled_geom = models[geom_cols].apply(lambda c: (c - c.min()) / (c.max() - c.min()))
centroid = scaled_geom.loc[top15_ids].median(axis=0)
distances = pd.Series((((scaled_geom - centroid)**2).sum(axis=1))**0.5, index=scaled_geom.index).astype(float)
geom_summary = pd.DataFrame([
    {
        'median_dist_top15': float(distances.loc[top15_ids].median()),
        'median_dist_rest': float(distances.loc[~models.index.isin(top15_ids)].median())
    }
])
geom_summary['median_ratio_rest_over_top15'] = geom_summary['median_dist_rest'] / geom_summary['median_dist_top15']
distances.rename('dist_to_top15_centroid').to_frame().to_csv(os.path.join(OUTPUT_DIR,'Stage4_distances_to_centroid.csv'))
geom_summary.to_csv(os.path.join(OUTPUT_DIR,'Stage4_geometry_summary.csv'), index=False)

# (vi) Weight-perturbation robustness (±10% multiplicative noise, renormalize)
rng = np.random.default_rng(42)
def perturb_weights(w_dict, eps=0.10):
    w = pd.Series(w_dict, dtype=float)
    noise = rng.uniform(1-eps, 1+eps, size=len(w))
    w_pert = w * noise
    w_pert = np.clip(w_pert, 1e-9, None)
    return (w_pert / w_pert.sum())

def recompute_winner_and_topk(scen_name, w_series, k=15):
    nrm = _normalise(models[w_series.index], CRIT_SENSE)
    # ranks per method
    rank_cols = {}
    for m, func in MCDM_FUNCS.items():
        r = func(nrm if m!='FUCA' else nrm.rank(ascending=False, axis=0), w_series)
        rank_cols[m] = r
    ranks_df = pd.concat(rank_cols, axis=1)
    # aggregate fitness
    max_r = ranks_df.max().max()
    fit = 1 - (ranks_df - 1)/(max_r - 1)
    fit_mean = fit.mean(axis=1)
    winner = fit_mean.idxmax()
    topk = set(fit_mean.sort_values(ascending=False).head(k).index)
    return winner, topk

robust_rows = []
for scen, w0 in WEIGHT_SCENARIOS.items():
    # baseline
    w_base = pd.Series(w0, dtype=float)
    base_winner, base_topk = recompute_winner_and_topk(scen, w_base)
    changes_winner = 0; changes_topk = 0; B = 200
    for _ in range(B):
        w_pert = perturb_weights(w0, eps=0.10)
        win_p, topk_p = recompute_winner_and_topk(scen, w_pert)
        if win_p != base_winner: changes_winner += 1
        if topk_p != base_topk: changes_topk += 1
    robust_rows.append({'scenario': scen,
                        'prob_winner_change': changes_winner/B,
                        'prob_topk_change': changes_topk/B})
pd.DataFrame(robust_rows).to_csv(os.path.join(OUTPUT_DIR,'Stage4_weight_perturbation_robustness.csv'), index=False)

# (vii) Fixed-parameter enrichment (Fisher) for Top-15 vs remainder
top_mask_series = models.index.isin(top15_ids)
enrich_rows = []
for p in PARAM_COLS:
    fixed = struct_df.set_index('model_id')[p].reindex(models.index).fillna(0).astype(int)
    a = int(((fixed==1) & top_mask_series).sum())
    b = int(((fixed==0) & top_mask_series).sum())
    c = int(((fixed==1) & (~top_mask_series)).sum())
    d = int(((fixed==0) & (~top_mask_series)).sum())
    table = np.array([[a,b],[c,d]])
    try:
        OR, pval = fisher_exact(table)
    except Exception:
        OR, pval = (np.nan, np.nan)
    enrich_rows.append({'param': p, 'OR': OR, 'p_value': pval, 'a_fixed_top15': a, 'b_free_top15': b, 'c_fixed_rest': c, 'd_free_rest': d})
enrich_df = pd.DataFrame(enrich_rows)
# FDR (Benjamini-Hochberg) with NaN handling
q_vals = np.full(len(enrich_df), np.nan)
valid = enrich_df['p_value'].notna().to_numpy()
pv = enrich_df.loc[valid, 'p_value'].to_numpy(dtype=float)
order = np.argsort(pv)
m = len(pv); prev = 1.0; q_comp = np.empty(m)
for i in range(m-1, -1, -1):
    p_i = pv[order[i]]; q_i = p_i * m / (i+1)
    prev = min(prev, q_i); q_comp[order[i]] = prev
q_vals[valid] = np.clip(q_comp, 0, 1)
enrich_df['q_value'] = q_vals
enrich_df['param_label'] = enrich_df['param'].map(PARAM_LABELS)
enrich_df.to_csv(os.path.join(OUTPUT_DIR,'Stage4_fisher_enrichment_top15.csv'), index=False)

# (viii) Co-fixation motifs: pairs and triads over-representation
def motif_test(combo):
    # both/all fixed in combo
    mat = struct_df.set_index('model_id')[list(combo)].reindex(models.index).fillna(0).astype(int)
    top_all = int(((mat.sum(axis=1) == len(combo)) & top_mask_series).sum())
    top_not = int((top_mask_series.sum()) - top_all)
    rest_all = int((((mat.sum(axis=1) == len(combo)) & (~top_mask_series)).sum()))
    rest_not = int(((~top_mask_series).sum()) - rest_all)
    table = np.array([[top_all, top_not],[rest_all, rest_not]])
    try:
        OR, pval = fisher_exact(table)
    except Exception:
        OR, pval = (np.nan, np.nan)
    return OR, pval, top_all, rest_all

pair_rows = []
for a,b in combinations(PARAM_COLS, 2):
    OR, pval, top_all, rest_all = motif_test((a,b))
    pair_rows.append({'pair': f"{a}&{b}", 'OR': OR, 'p_value': pval, 'top_count': top_all, 'rest_count': rest_all})
pairs_df = pd.DataFrame(pair_rows)
q_vals = np.full(len(pairs_df), np.nan)
valid = pairs_df['p_value'].notna().to_numpy()
pv = pairs_df.loc[valid, 'p_value'].to_numpy(dtype=float)
order = np.argsort(pv)
m = len(pv); prev = 1.0; q_comp = np.empty(m)
for i in range(m-1, -1, -1):
    p_i = pv[order[i]]; q_i = p_i * m / (i+1); prev = min(prev, q_i); q_comp[order[i]] = prev
q_vals[valid] = np.clip(q_comp, 0, 1)
pairs_df['q_value'] = q_vals
pairs_df.to_csv(os.path.join(OUTPUT_DIR,'Stage4_cofixation_pairs.csv'), index=False)

triad_rows = []
for combo in combinations(PARAM_COLS, 3):
    OR, pval, top_all, rest_all = motif_test(combo)
    triad_rows.append({'triad': '&'.join(combo), 'OR': OR, 'p_value': pval, 'top_count': top_all, 'rest_count': rest_all})
triads_df = pd.DataFrame(triad_rows)
q_vals = np.full(len(triads_df), np.nan)
valid = triads_df['p_value'].notna().to_numpy()
pv = triads_df.loc[valid, 'p_value'].to_numpy(dtype=float)
order = np.argsort(pv)
m = len(pv); prev = 1.0; q_comp = np.empty(m)
for i in range(m-1, -1, -1):
    p_i = pv[order[i]]; q_i = p_i * m / (i+1); prev = min(prev, q_i); q_comp[order[i]] = prev
q_vals[valid] = np.clip(q_comp, 0, 1)
triads_df['q_value'] = q_vals
triads_df.to_csv(os.path.join(OUTPUT_DIR,'Stage4_cofixation_triads.csv'), index=False)

# (ix) Parameter–criteria links: point-biserial (Pearson) and Δ-means
link_rows = []
for p in PARAM_COLS:
    fixed = struct_df.set_index('model_id')[p].reindex(models.index).fillna(0).astype(int)
    for crit in ['AICc','MNCI','RSQ2','GSS']:
        x = models[crit].astype(float)
        r, _ = spearmanr(fixed, x)  # monotone link; swap to pearson if needed
        mu_fixed = float(x[fixed==1].mean()) if (fixed==1).any() else np.nan
        mu_free  = float(x[fixed==0].mean()) if (fixed==0).any() else np.nan
        link_rows.append({'param': p, 'criterion': crit, 'spearman_rho': r, 'delta_mean_fixed_minus_free': (mu_fixed - mu_free) if np.isfinite(mu_fixed) and np.isfinite(mu_free) else np.nan})
links_df = pd.DataFrame(link_rows)
links_df['param_label'] = links_df['param'].map(PARAM_LABELS)
links_df.to_csv(os.path.join(OUTPUT_DIR,'Stage4_param_criteria_links.csv'), index=False)

# (x) Model-1750 snapshot (PC space and Δ-index vs Top-15 median)
target_id = 1750 if 1750 in models.index else int(best_id)
feat = models[['AICc','MNCI','RSQ2','GSS']].copy()
# orient so that higher=better: negate minimization criteria
feat_oriented = feat.copy(); feat_oriented[['AICc','MNCI']] = -feat_oriented[['AICc','MNCI']]
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
scaler = StandardScaler().fit(feat_oriented)
Z = scaler.transform(feat_oriented)
pca2 = PCA(2).fit(Z)
scores = pca2.transform(Z)
pc_df = pd.DataFrame(scores, index=models.index, columns=['PC1','PC2'])
centroid_pc = pc_df.loc[top15_ids].median(axis=0)
dist_pc = float(np.sqrt(((pc_df.loc[target_id] - centroid_pc)**2).sum())) if target_id in pc_df.index else np.nan
median_top15 = models.loc[top15_ids, ['AICc','MNCI','RSQ2','GSS']].median()
delta_index = {}
if target_id in models.index:
    row_target = models.loc[[target_id], ['AICc','MNCI','RSQ2','GSS']].iloc[0]
    delta_index = (row_target - median_top15).to_dict()
if target_id in pc_df.index:
    pc1_val = float(pd.to_numeric(pd.Series(pc_df.loc[target_id, 'PC1'])).iloc[0])
    pc2_val = float(pd.to_numeric(pd.Series(pc_df.loc[target_id, 'PC2'])).iloc[0])
else:
    pc1_val = np.nan; pc2_val = np.nan
snap = {
    'target_id': int(target_id),
    'pc1': pc1_val,
    'pc2': pc2_val,
    'dist_to_top15_centroid_pc': dist_pc,
    'delta_vs_top15_median': delta_index,
    'explained_var_pct': [float(p*100) for p in pca2.explained_variance_ratio_]
}
pd.Series(snap, dtype=object).to_json(os.path.join(OUTPUT_DIR,'Stage4_model1750_snapshot.json'))

# (xi) Shortlist compression & complexity shift
fix_mat = struct_df.set_index('model_id')[PARAM_COLS].reindex(models.index).fillna(0).astype(int)
n_fixed = fix_mat.sum(axis=1)
est_free = len(PARAM_COLS) - n_fixed
shortlist_ids = set(top15_ids)
comp_summary = pd.DataFrame([{
    'N_VMS': int(len(models)),
    'N_shortlist': int(len(shortlist_ids)),
    'shortlist_pct': float(len(shortlist_ids)/len(models)*100.0),
    'median_fixed_pool': int(n_fixed.median()),
    'median_fixed_shortlist': int(n_fixed.loc[list(shortlist_ids)].median()),
    'median_free_pool': int(est_free.median()),
    'median_free_shortlist': int(est_free.loc[list(shortlist_ids)].median()),
}])
comp_summary.to_csv(os.path.join(OUTPUT_DIR,'Stage4_shortlist_compression.csv'), index=False)

# (xii) Rank-reversal check under re-normalization (SAW, min–max vs z-score)
rev_rows = []
for scen, w in WEIGHT_SCENARIOS.items():
    # min–max normalized
    nrm_minmax = _normalise(models[list(w.keys())], CRIT_SENSE)
    ranks_minmax = _saw(nrm_minmax, pd.Series(w))
    # z-score normalized (orient sense first)
    X = models[list(w.keys())].copy()
    for c, s in CRIT_SENSE.items():
        if c in X.columns and s == 'min':
            X[c] = -X[c]
    Xz = (X - X.mean())/X.std(ddof=0)
    ranks_z = _saw(Xz, pd.Series(w))
    # pairwise order changes among Top-15 baseline (by votes)
    ids = list(top15_ids)
    changes = 0; total = 0
    for i in range(len(ids)):
        for j in range(i+1, len(ids)):
            a, b = ids[i], ids[j]
            total += 1
            ord1 = ranks_minmax[a] < ranks_minmax[b]
            ord2 = ranks_z[a] < ranks_z[b]
            if ord1 != ord2:
                changes += 1
    frac = changes/total if total>0 else np.nan
    rev_rows.append({'scenario': scen, 'pairwise_reversal_frac_top15': frac})
pd.DataFrame(rev_rows).to_csv(os.path.join(OUTPUT_DIR,'Stage4_rank_reversal_check.csv'), index=False)

# ─────────────────────────────────────────────────────────────────────────────
# 4  FIGURES  –  **FINAL PATCH 3**
# ─────────────────────────────────────────────────────────────────────────────
import warnings, matplotlib
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
warnings.filterwarnings("ignore", category=matplotlib.MatplotlibDeprecationWarning)

sns.set(style='white', font_scale=1.05)

# 4.0  score-matrix + voted IDs
score_mat = pd.concat(
    {f"{r['method']}-{r['scenario']}": r['ranks'].reindex(models.index)
     for r in results}, axis=1).dropna(how='all')
voted_ids = models.loc[models['votes'] > 0].index
score_mat = score_mat.loc[voted_ids]

# ─────────────────────────  FIGURE 1  ─────────────────────────
fig1, axes = plt.subplots(len(WEIGHT_SCENARIOS),
                          figsize=(9, 1.8*len(WEIGHT_SCENARIOS)),
                          constrained_layout=True, sharex=True)
method_palette = sns.color_palette('tab10', n_colors=len(MCDM_FUNCS))
x_positions = np.arange(len(voted_ids))
id2pos = dict(zip(sorted(voted_ids), x_positions))

for ax, (scen, _) in zip(axes, WEIGHT_SCENARIOS.items()):
    winners = pd.DataFrame([r for r in results if r['scenario'] == scen])
    winners = winners[winners['best_model'].isin(voted_ids)]
    ax.set_title(f"Scenario: {scen}", loc='left', fontweight='bold')
    for i, method in enumerate(MCDM_FUNCS):
        chosen = winners.loc[winners['method'] == method, 'best_model']
        ax.scatter([id2pos[x] for x in chosen], np.full_like(chosen, i),
                   s=80, color=method_palette[i])
    ax.set_yticks(range(len(MCDM_FUNCS))); ax.set_yticklabels(MCDM_FUNCS.keys())
    ax.set_xlabel("Model ID");
    ax.set_xticks(x_positions); ax.set_xticklabels(sorted(voted_ids), rotation=90)
    ax.grid(axis='x', linestyle='--', alpha=.3)

fig1.savefig(os.path.join(OUTPUT_DIR,'Fig1_model_selection_by_scenario.png'), dpi=300)
plt.show()

# ─────────────────────────  FIGURE 2  ─────────────────────────
rank_matrix = score_mat.copy()
max_rank = rank_matrix.max().max()
fitness = 1 - (rank_matrix - 1) / (max_rank - 1)
plt.figure(figsize=(10, max(6, 0.35*len(fitness))))
sns.heatmap(fitness, cmap='viridis', vmin=0, vmax=1,
            cbar_kws={'label': 'Relative fitness (1 = best)'})
plt.xlabel("Method–Scenario"); plt.ylabel("Model ID")
plt.title("Figure 2 – Relative fitness across methods & scenarios",
          loc='left', fontweight='bold')
plt.tight_layout();
plt.savefig(os.path.join(OUTPUT_DIR,'Fig2_fitness_heatmap.png'), dpi=300)
plt.show()

# ─────────────────────────  FIGURE 3  ─────────────────────────
from matplotlib.colors import ListedColormap

pattern = struct_df.set_index('model_id').loc[top15_ids, PARAM_COLS]

# 0 = libre, 1 = fijo, 2 = fijo & modelo más votado
matrix = np.zeros(pattern.shape, dtype=int)
matrix[pattern == 1] = 1
if best_id in pattern.index:
    row = pattern.index.get_loc(best_id)           # fila del modelo best
    matrix[row, pattern.loc[best_id] == 1] = 2     # solo celdas fijas → 2

cmap = ListedColormap(['white', 'black', 'red'])   # 0,1,2 → colores
plt.figure(figsize=(7, 6))
sns.heatmap(matrix, cmap=cmap, cbar=False,
            yticklabels=[str(x) for x in pattern.index.tolist()],
            xticklabels=[PARAM_LABELS[c] for c in PARAM_COLS])
plt.xticks(rotation=45, ha='right')
plt.title("Figure 3 – Fixed parameters (black);\nBest model highlighted in red",
          loc='left', pad=10, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR,'Fig3_param_pattern.png'), dpi=300)
plt.show()
# ─────────────────────────  FIGURE 4  –  pool completo + voted destacados  ─────────────────────────
indicators = ['AICc', 'MNCI', 'RSQ2', 'GSS']
scaled = models[indicators].apply(lambda c: (c - c.min()) / (c.max() - c.min()))

fig4 = plt.figure(figsize=(9, 7))
ax4 = fig4.add_subplot(111, projection='3d', proj_type='persp')
from typing import Any
ax4_t: Any = ax4

# ❶  Pool completo (color-map viridis por GSS)
x = np.asarray(scaled['AICc'].to_list(), dtype=float)
y = np.asarray(scaled['MNCI'].to_list(), dtype=float)
z = np.asarray(scaled['RSQ2'].to_list(), dtype=float)
colours = np.asarray(scaled['GSS'].to_list(), dtype=float)
scatter = ax4_t.scatter(x, y, z, c=colours, cmap='viridis',
                        s=50, alpha=.35)

# ❷  Modelos con ≥1 voto — resaltados encima
for mid in voted_ids:
    vals = scaled.loc[mid, ['AICc', 'MNCI', 'RSQ2']].values.astype(float).ravel()
    xi, yi, zi = float(vals[0]), float(vals[1]), float(vals[2])
    is_best = mid == best_id
    ax4_t.scatter(xi, yi, zi,
                c='red' if is_best else 'none',      # relleno rojo solo si best
                s=180 if is_best else 110,
                marker='*' if is_best else 'o',
                edgecolor='red' if is_best else 'orange',
                linewidth=1.2, zorder=5)
    ax4.text(xi, yi, zi,
             f" {mid}", color='red' if is_best else 'black',
             fontsize=9, zorder=6)
    # Proyección a z = 0
    ax4_t.plot([xi, xi], [yi, yi], [0, zi],
             linestyle='--', linewidth=.8,
             color='red' if is_best else 'orange', alpha=.8, zorder=4)

# Ejes, rótulos y estilo
ax4.set_xlabel('AICc (scaled)', labelpad=12)
ax4.set_ylabel('MNCI (scaled)', labelpad=12)
ax4.set_zlabel('RSQ2 (scaled)', labelpad=18);

ax4.set_title("Figure 4 – 3-D robustness landscape\n"
              "Color = GSS (scaled); voted models highlighted; * = best model",
              loc='left', fontweight='bold', pad=15)

fig4.colorbar(scatter, label='GSS (scaled)', shrink=0.6)
ax4.view_init(elev=28, azim=38)
fig4.subplots_adjust(left=0.18, right=0.96, bottom=0.12, top=0.92)
fig4.savefig(os.path.join(OUTPUT_DIR,'Fig4_robustness_landscape.png'), dpi=300)
plt.show()
# ─────────────────────────  FIGURE 5  ─────────────────────────
ROBUST_COLS = ['AICc', 'MNCI', 'RSQ2', 'GSS']
X = models.loc[top15_ids, ROBUST_COLS].copy()
scs = StandardScaler().fit_transform(X)
pca = PCA(2).fit(scs)
sc = pca.transform(scs);  expl = pca.explained_variance_ratio_ * 100

fig5, ax5 = plt.subplots(figsize=(7, 6))
ax5.scatter(sc[:, 0], sc[:, 1], c='gray', alpha=.6, s=60)
for i, mid in enumerate(top15_ids):
    ax5.text(sc[i, 0], sc[i, 1], f" {mid}",
             color='red' if mid == best_id else 'black',
             fontsize=8, fontweight='bold' if mid == best_id else 'normal')

# vectores – indicadores
for v, vec in zip(ROBUST_COLS, pca.components_.T):
    ax5.arrow(0, 0, vec[0]*3, vec[1]*3,
              head_width=.08, head_length=.1,
              color='green', linewidth=1.2)
    ax5.text(vec[0]*3.3, vec[1]*3.3, v, color='green', fontsize=9,fontweight='bold')

# vectores – parámetros
for p in PARAM_COLS:
    vals = struct_df.set_index('model_id').loc[top15_ids, p].astype(float).to_numpy()
    if np.var(vals) == 0:
        continue
    z_arr = (vals - np.mean(vals)) / (np.std(vals, ddof=0) if np.std(vals, ddof=0)>0 else 1.0)
    c1 = np.corrcoef(z_arr, sc[:, 0])[0, 1]
    c2 = np.corrcoef(z_arr, sc[:, 1])[0, 1]
    ax5.arrow(0, 0, c1*5, c2*5,
              head_width=.05, head_length=.07,
              color='black', linewidth=.9, alpha=.85)
    ax5.text(c1*5*1.08, c2*5*1.08, PARAM_LABELS[p], fontsize=7)

ax5.axhline(0, ls='--', lw=.5, color='grey')
ax5.axvline(0, ls='--', lw=.5, color='grey')
ax5.set_xlabel(f"PC1 ({expl[0]:.1f}%)")
ax5.set_ylabel(f"PC2 ({expl[1]:.1f}%)")
ax5.set_title("Figure 5 – PCA of Top-15 models\n"
              "Green = robustness vectors  •  Black = parameter vectors",
              loc='left', fontweight='bold', pad=12)

# quitar el cuadro alrededor del gráfico
for spine in ax5.spines.values():
    spine.set_visible(False)

plt.tight_layout();  fig5.savefig(os.path.join(OUTPUT_DIR,'Fig5_PCA.png'), dpi=300)
plt.show()
# ─────────────────────────  FIGURE 6  –  Composite 2×2  ─────────────────────────
import matplotlib.image as mpimg
fig6, axes6 = plt.subplots(2, 2, figsize=(13, 11))

panel_files = [
    os.path.join(OUTPUT_DIR,'Fig1_model_selection_by_scenario.png'),
    os.path.join(OUTPUT_DIR,'Fig3_param_pattern.png'),
    os.path.join(OUTPUT_DIR,'Fig4_robustness_landscape.png'),
    os.path.join(OUTPUT_DIR,'Fig5_PCA.png')
]

for ax, fname in zip(axes6.flat, panel_files):
    img = mpimg.imread(fname)
    ax.imshow(img)
    ax.axis('off')

fig6.suptitle("Figure 6 – Consolidated overview (Figures 1, 3, 4 & 5)",
              fontsize=16, fontweight='bold', y=0.96)
plt.tight_layout(); fig6.savefig(os.path.join(OUTPUT_DIR,'Fig6_composite.png'), dpi=300); plt.show()

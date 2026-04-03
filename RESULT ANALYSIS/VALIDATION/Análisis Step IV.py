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
from scipy.stats import fisher_exact
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
top15_ids  = models.sort_values('votes', ascending=False).head(15).index
best_id    = int(models['votes'].idxmax())

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

fig1.savefig('Fig1_model_selection_by_scenario.png', dpi=300)
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
plt.tight_layout(); plt.show()

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
            yticklabels=pattern.index,
            xticklabels=[PARAM_LABELS[c] for c in PARAM_COLS])
plt.xticks(rotation=45, ha='right')
plt.title("Figure 3 – Fixed parameters (black);\nBest model highlighted in red",
          loc='left', pad=10, fontweight='bold')
plt.tight_layout()
plt.savefig('Fig3_param_pattern.png', dpi=300)
plt.show()
# ─────────────────────────  FIGURE 4  –  pool completo + voted destacados  ─────────────────────────
indicators = ['AICc', 'MNCI', 'RSQ2', 'GSS']
scaled = models[indicators].apply(lambda c: (c - c.min()) / (c.max() - c.min()))

fig4 = plt.figure(figsize=(9, 7))
ax4 = fig4.add_subplot(111, projection='3d', proj_type='persp')

# ❶  Pool completo (color-map viridis por GSS)
x, y, z = scaled['AICc'], scaled['MNCI'], scaled['RSQ2']
colours = scaled['GSS']
scatter = ax4.scatter(x, y, z, c=colours, cmap='viridis',
                      s=50, alpha=.35)

# ❷  Modelos con ≥1 voto — resaltados encima
for mid in voted_ids:
    xi, yi, zi = scaled.loc[mid, ['AICc', 'MNCI', 'RSQ2']]
    is_best = mid == best_id
    ax4.scatter(xi, yi, zi,
                c='red' if is_best else 'none',      # relleno rojo solo si best
                s=180 if is_best else 110,
                marker='*' if is_best else 'o',
                edgecolor='red' if is_best else 'orange',
                linewidth=1.2, zorder=5)
    ax4.text(xi, yi, zi,
             f" {mid}", color='red' if is_best else 'black',
             fontsize=9, zorder=6)
    # Proyección a z = 0
    ax4.plot([xi, xi], [yi, yi], [0, zi],
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
fig4.savefig('Fig4_robustness_landscape.png', dpi=300)
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
    vals = struct_df.set_index('model_id').loc[top15_ids, p].values
    if vals.var() == 0:
        continue
    z = (vals - vals.mean()) / vals.std(ddof=0)
    c1 = np.corrcoef(z, sc[:, 0])[0, 1]
    c2 = np.corrcoef(z, sc[:, 1])[0, 1]
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

plt.tight_layout();  fig5.savefig('Fig5_PCA.png', dpi=300)
plt.show()
# ─────────────────────────  FIGURE 6  –  Composite 2×2  ─────────────────────────
import matplotlib.image as mpimg
fig6, axes6 = plt.subplots(2, 2, figsize=(13, 11))

panel_files = ['Fig1_model_selection_by_scenario.png',
               'Fig3_param_pattern.png',
               'Fig4_robustness_landscape.png',
               'Fig5_PCA.png']

for ax, fname in zip(axes6.flat, panel_files):
    img = mpimg.imread(fname)
    ax.imshow(img)
    ax.axis('off')

fig6.suptitle("Figure 6 – Consolidated overview (Figures 1, 3, 4 & 5)",
              fontsize=16, fontweight='bold', y=0.96)
plt.tight_layout(); plt.show()

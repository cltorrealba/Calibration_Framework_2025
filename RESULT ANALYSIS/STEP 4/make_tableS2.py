"""
Generate Table S2 (Stage IV shortlist) with full metadata:
- Model ID, rank, votes, fitness stats
- Complexity (n_fixed/n_free) and fixation pattern
- Normalised robustness indicators (AICc, MNCI, RSQ2, GSS)
- Vote matrix by method–scenario (35 combinations)
Outputs: salidas/TableS2.csv
"""
import pandas as pd
import numpy as np
import os

# --- Constants (reuse from Stage IV script) ---
HIPPO_PATH  = r"C:/Users/ctorrealba/OneDrive - Viña Concha y Toro S.A/Documentos/Doctorado/Artículos/Artículo - Estimación/Codes/STEP 2/HIPPO_result.xlsx"
ROBUST_PATH = r"C:/Users/ctorrealba/OneDrive - Viña Concha y Toro S.A/Documentos/Doctorado/Artículos/Artículo - Estimación/Codes/STEP 3/Zenteno_Final_2023b_WS.xlsx"
PARAM_COLS = ['mu0','betaG0','betaF0','Kn0','Kg0','Kf0','Kig0','Kie0', 'Yxn','Yxg','Yxf','Yeg','Yef']
WEIGHT_SCENARIOS = {
    'No-priority'    : dict(AICc=0.25, MNCI=0.25, RSQ2=0.25, GSS=0.25),
    'Parsimony'      : dict(AICc=0.70, MNCI=0.10, RSQ2=0.10, GSS=0.10),
    'Goodness-of-fit': dict(AICc=0.10, MNCI=0.10, RSQ2=0.70, GSS=0.10),
    'Identifiability': dict(AICc=0.10, MNCI=0.70, RSQ2=0.10, GSS=0.10),
    'Sensitivity'    : dict(AICc=0.10, MNCI=0.10, RSQ2=0.10, GSS=0.70),
}
CRIT_SENSE = dict(AICc='min', MNCI='min', RSQ2='max', GSS='max')

# --- MCDM helper functions (identical to Stage IV script) ---
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

MCDM_FUNCS={'TOPSIS':_topsis,'LINMAP':_linmap,'VIKOR':_vikor,'SAW':_saw,'MEW':_mew,'GRA':_gra,'FUCA':_fuca}

# --- Load data ---
hippo  = pd.read_excel(HIPPO_PATH)
robust = pd.read_excel(ROBUST_PATH)
mask_viable = (hippo['CCc'] == 0) & (hippo['I955'] == 0)
struct_df   = hippo.loc[mask_viable].copy()
struct_df = struct_df.rename(columns={'FFF':'model_id'})
robust    = robust.rename(columns={'FFF':'model_id'})
models = (struct_df.merge(robust, on='model_id', how='inner').set_index('model_id'))

# Complexity and pattern
fix_mat = struct_df.set_index('model_id')[PARAM_COLS].reindex(models.index).fillna(0).astype(int)
models['n_fixed'] = fix_mat.sum(axis=1)
models['n_free']  = len(PARAM_COLS) - models['n_fixed']
models['pattern'] = fix_mat.astype(str).agg(''.join, axis=1)

# Normalised indicators (min–max respecting sense)
crit_cols = ['AICc','MNCI','RSQ2','GSS']
norm_df = _normalise(models[crit_cols], CRIT_SENSE)
norm_df = norm_df.rename(columns={c: f"norm_{c}" for c in crit_cols})
models = models.join(norm_df)

# Rebuild votes by method–scenario
results = []
rank_matrix_blocks = []
combo_names = []
for scen, w_dict in WEIGHT_SCENARIOS.items():
    w = pd.Series(w_dict)
    nrm = _normalise(models[w.index], CRIT_SENSE)
    crit_ranks = nrm.rank(ascending=False, axis=0)
    for m, func in MCDM_FUNCS.items():
        ranks = func(crit_ranks if m=='FUCA' else nrm, w).astype(int)
        combo = f"{m}::{scen}"
        combo_names.append(combo)
        rank_matrix_blocks.append(ranks)
        results.append({'scenario': scen, 'method': m, 'combo': combo, 'ranks': ranks, 'best_model': ranks.idxmin()})

# votes per combination
vote_cols = []
vote_data = pd.DataFrame(index=models.index)
for r in results:
    col = f"vote_{r['method']}::{r['scenario']}"
    vote_cols.append(col)
    winner = r['best_model']
    vote_data[col] = 0
    if pd.notna(winner) and winner in vote_data.index:
        vote_data.loc[winner, col] = 1

# total votes (for consistency check)
vote_data['votes_recalc'] = vote_data[vote_cols].sum(axis=1)
models = models.join(vote_data)

# Load Top-15 ranking from Stage4 output for ordering
ranked = pd.read_csv(os.path.join('salidas','Stage4_top15_selection.csv'))
ranked = ranked.set_index('model_id')

# Build Table S2 for top-15 only
cols_basic = ['n_fixed','n_free','pattern']
# indicator columns
cols_ind = [f"norm_{c}" for c in crit_cols]
# vote matrix
cols_votes = vote_cols

out = (ranked.join(models[cols_basic + cols_ind + cols_votes])
              .reset_index()
              .sort_values('top15_rank'))

# Save
os.makedirs('salidas', exist_ok=True)
out.to_csv(os.path.join('salidas','TableS2.csv'), index=False)
print("TableS2.csv saved in salidas/ with", len(out), "rows and", out.shape[1], "columns")

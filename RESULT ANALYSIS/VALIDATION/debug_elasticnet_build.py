import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegressionCV
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

PARAM_COLS = ["mu0","betaG0","betaF0","Kn0","Kg0","Kf0","Kig0","Kie0","Yxn","Yxg","Yxf","Yeg","Yef"]

def main():
    base = os.path.join(os.path.dirname(__file__), 'salidas')
    metrics_path = os.path.join(base, 'metrics', 'lab_metrics.csv')
    if not os.path.exists(metrics_path):
        print('NO_METRICS')
        return
    lab_df = pd.read_csv(metrics_path)
    r2_col = 'rsq_cv_mean' if 'rsq_cv_mean' in lab_df.columns else ('r2_mean' if 'r2_mean' in lab_df.columns else None)
    if r2_col is None:
        print('NO_R2_COL')
        return
    agg = lab_df.groupby('model_id')[r2_col].mean().rename('r2_mean_model').reset_index()
    q75 = float(agg['r2_mean_model'].quantile(0.75))
    agg['success'] = (agg['r2_mean_model'] >= q75).astype(int)
    print('MODELS:', len(agg), 'Q75:', q75)

    # try HIPPO for flags
    hippo_path = (
        r"C:/Users/ctorrealba/OneDrive - Viña Concha y Toro S.A/Documentos/Doctorado/"
        r"Artículos/Artículo - Estimación/Codes/STEP 2/HIPPO_result.xlsx"
    )
    if not os.path.exists(hippo_path):
        print('NO_HIPPO')
        return
    hippo = pd.read_excel(hippo_path, sheet_name='Sheet1')
    if {'CCc','I955'}.issubset(set(hippo.columns)):
        hippo = hippo[(hippo['CCc']==0) & (hippo['I955']==0)]

    rows = []
    yields_cols = ['Yxn','Yxg','Yxf','Yeg','Yef']
    for mid in agg['model_id'].astype(int).tolist():
        row = hippo.loc[hippo['FFF']==mid]
        if row.empty:
            continue
        r = row.iloc[0]
        def fval(name):
            return float(r.get(name, np.nan))
        yfrac = float(np.nanmean([fval(c) for c in yields_cols]))
        rows.append({
            'model_id': mid,
            'betaG0_fixed': fval('betaG0'),
            'Kg0_fixed': fval('Kg0'),
            'Kie0_fixed': fval('Kie0'),
            'Yields_fixed_frac': yfrac,
        })
    feat_df = pd.DataFrame(rows)
    data = pd.merge(agg[['model_id','r2_mean_model','success']], feat_df, on='model_id', how='inner').dropna()
    print('DATA_ROWS:', len(data))
    if data.empty:
        return

    X = data[['betaG0_fixed','Yields_fixed_frac','Kg0_fixed','Kie0_fixed']].to_numpy(dtype=float)
    y = data['success'].astype(int).to_numpy()
    cv = StratifiedKFold(n_splits=min(5, np.unique(y, return_counts=True)[1].min() if y.size>0 else 5), shuffle=True, random_state=42)
    clf = Pipeline([
        ('scaler', StandardScaler(with_mean=True, with_std=True)),
        ('logit', LogisticRegressionCV(Cs=[0.1,0.5,1.0,2.0,5.0], cv=cv, scoring='roc_auc', penalty='elasticnet', solver='saga', l1_ratios=[0.5], max_iter=5000, class_weight='balanced'))
    ])
    clf.fit(X, y)
    prob_cv = cross_val_predict(clf, X, y, cv=cv, method='predict_proba')[:, 1]
    auroc = float(roc_auc_score(y, prob_cv))
    coef = clf.named_steps['logit'].coef_.ravel()
    print('COEFS:', {
        'betaG0': float(coef[0]),
        'Yields': float(coef[1]),
        'Kg0': float(coef[2]),
        'Kie0': float(coef[3]),
    })
    print('AUROC:', auroc)

if __name__ == '__main__':
    main()

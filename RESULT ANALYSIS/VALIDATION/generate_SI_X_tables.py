#!/usr/bin/env python3
"""
Generate SI-X Tables for manuscript Section on validation diagnostics.

Generates:
- Table SI-X.1: One-at-a-time parameter fixing tests (ΔAICc, ΔR²)
- Table SI-X.2: Cross-scale parameter shifts (Cliff's delta, Mann-Whitney tests)
- Table SI-X.3: Thermal sensitivity (RMSD ratios by temperature terciles)
"""

import os
import pandas as pd
import numpy as np


# Define paths
VALIDATION_DIR = r"c:\Users\ctorrealba\OneDrive - Viña Concha y Toro S.A\Documentos\Doctorado\Artículos\Artículo - Estimación\Codes\VALIDATION"
METRICS_DIR = os.path.join(VALIDATION_DIR, "salidas", "metrics")

# ────────────────────────────────────────────────────────────────────────
# TABLE SI-X.1: One-at-a-time parameter fixing tests
# ────────────────────────────────────────────────────────────────────────

ablation = pd.read_csv(os.path.join(METRICS_DIR, "lab_ablation_summary.csv"))

# Filter for models 1750, 1860, 2264 (Top-3 MCDM winners)
winners = [1750, 1860, 2264]
ablation_winners = ablation[ablation['model_id'].isin(winners)].copy()

print("=" * 80)
print("TABLE SI-X.1: One-at-a-time parameter fixing tests")
print("=" * 80)
print("\nRaw data (filtered for MCDM winners):")
print(ablation_winners.to_string())

# Create formatted table: model, param, ΔAICc, ΔR²
table_x1_rows = []
for _, row in ablation_winners.iterrows():
    table_x1_rows.append({
        'Model': int(row['model_id']),
        'Parameter': row['param_name'],
        'ΔAICc': f"{row['delta_AICc']:+.1f}",
        'ΔR²': f"{row['delta_RSQ']:+.3f}",
    })

df_x1 = pd.DataFrame(table_x1_rows)
print("\nFormatted for manuscript:")
print(df_x1.to_string(index=False))

# Export to CSV
df_x1.to_csv(os.path.join(METRICS_DIR, "SI_X_1_ablation_formatted.csv"), index=False)

# ────────────────────────────────────────────────────────────────────────
# TABLE SI-X.2: Cross-scale parameter shifts
# ────────────────────────────────────────────────────────────────────────

param_tests = pd.read_csv(os.path.join(METRICS_DIR, "transfer_param_tests.csv"))
param_winners = param_tests[param_tests['model_id'].isin(winners)].copy()

print("\n" + "=" * 80)
print("TABLE SI-X.2: Cross-scale parameter shifts (Lab vs Pilot)")
print("=" * 80)
print("\nRaw data (sample):")
print(param_winners.head(10).to_string())

# Create formatted table: model, param, Cliff's delta, significance
table_x2_rows = []
for _, row in param_winners.iterrows():
    delta_val = row['cliffs_delta']
    delta_str = f"{delta_val:+.2f}" if np.isfinite(delta_val) else "NaN"
    
    table_x2_rows.append({
        'Model': int(row['model_id']),
        'Parameter': row['param_name'],
        'Lab Mean': f"{row['lab_mean']:.3g}",
        'Pilot Mean': f"{row['pilot_mean']:.3g}",
        "Cliff's δ": delta_str,
        'Significance': row['significance'],
    })

df_x2 = pd.DataFrame(table_x2_rows)
print("\nFormatted for manuscript:")
print(df_x2.to_string(index=False))

# Export to CSV
df_x2.to_csv(os.path.join(METRICS_DIR, "SI_X_2_param_transfer_formatted.csv"), index=False)

# ────────────────────────────────────────────────────────────────────────
# TABLE SI-X.3: Thermal sensitivity (RMSD by temperature terciles)
# ────────────────────────────────────────────────────────────────────────

stratified_temp = pd.read_csv(os.path.join(METRICS_DIR, "transfer_stratified_temp.csv"))
temp_winners = stratified_temp[stratified_temp['model_id'].isin(winners)].copy()

print("\n" + "=" * 80)
print("TABLE SI-X.3: Thermal sensitivity (RMSD by temperature terciles)")
print("=" * 80)
print("\nRaw data (sample):")
print(temp_winners.head(15).to_string())

# Compute thermal sensitivity ratio (RMSD_hot / RMSD_cool) by model, exper, variable
thermal_ratios = []
for (mid, exp, var), group in temp_winners.groupby(['model_id', 'pilot_exper', 'variable']):
    rmsd_t1 = group[group['temp_group'] == 'T1']['rmsd'].values
    rmsd_t3 = group[group['temp_group'] == 'T3']['rmsd'].values
    
    if len(rmsd_t1) > 0 and len(rmsd_t3) > 0:
        r1 = float(rmsd_t1[0])
        r3 = float(rmsd_t3[0])
        ratio = r3 / r1 if r1 > 0 else np.nan
        thermal_ratios.append({
            'Model': int(mid),
            'Experiment': int(exp),
            'Variable': var,
            'RMSD_Cool(T1)': f"{r1:.3f}",
            'RMSD_Hot(T3)': f"{r3:.3f}",
            'Ratio(Hot/Cool)': f"{ratio:.2f}" if np.isfinite(ratio) else "NaN",
        })

df_x3 = pd.DataFrame(thermal_ratios)
print("\nFormatted (thermal sensitivity ratios):")
print(df_x3.to_string(index=False))

# Export to CSV
df_x3.to_csv(os.path.join(METRICS_DIR, "SI_X_3_thermal_sensitivity_formatted.csv"), index=False)

# ────────────────────────────────────────────────────────────────────────
# Generate LaTeX tables
# ────────────────────────────────────────────────────────────────────────

latex_output = r"""
\section*{SI-X: Validation Diagnostics for Parameter-Fixation Decisions}

\subsection*{Detailed One-at-a-Time Parameter-Fixing Tests}

The following tests evaluate the impact of fixing each currently free parameter on model parsimony (AICc) 
and predictive skill (R$^2$) in the laboratory validation context.

\begin{table}[H]\centering
\small
\caption{One-at-a-time parameter fixing: Changes in AICc and R$^2$ when fixing each free parameter 
in models 1750 and 1860. Negative $\Delta\mathrm{AICc}$ indicates improved parsimony; negative 
$\Delta R^2$ indicates degraded fit. Only parameters that were initially free are shown.}
\label{tab:SI_X_1_ablation}
\begin{tabular}{lllrr}
\toprule
\textbf{Model} & \textbf{Parameter} & \textbf{$\Delta\mathrm{AICc}$} & \textbf{$\Delta R^2$} \\
\midrule
"""

for _, row in df_x1.iterrows():
    latex_output += f"{row['Model']} & {row['Parameter']} & {row['ΔAICc']:>8} & {row['ΔR²']:>8} \\\\\n"

latex_output += r"""\bottomrule
\end{tabular}
\end{table}

\vspace{12pt}

\subsection*{Cross-Scale Parameter Shifts (Lab $\leftrightarrow$ Pilot)}

Mann--Whitney $U$ tests and Cliff's $\delta$ (nonparametric effect size) quantify changes in parameter 
distributions when moving from laboratory to pilot scale. Large effect sizes and low $p$-values 
($p < 0.01$, marked **) indicate significant structural shifts that may affect model transferability.

\begin{table}[H]\centering
\small
\caption{Cross-scale parameter distribution shifts. Cliff's $\delta \in [-1, 1]$ quantifies effect size: 
$\delta \approx 0$ indicates complete overlap; $\delta = \pm 1$ indicates no overlap. 
Significance codes: $**$ = $p < 0.01$, $*$ = $p < 0.05$, ns = not significant.}
\label{tab:SI_X_2_param_transfer}
\begin{tabular}{lllrrll}
\toprule
\textbf{Model} & \textbf{Parameter} & \textbf{Lab Mean} & \textbf{Pilot Mean} & 
\textbf{Cliff's $\delta$} & \textbf{Signif.} \\
\midrule
"""

for _, row in df_x2.iterrows():
    cliffs_col = "Cliff's δ"
    latex_output += (f"{row['Model']} & {row['Parameter']} & "
                    f"{row['Lab Mean']:>12} & {row['Pilot Mean']:>12} & "
                    f"{row[cliffs_col]:>11} & {row['Significance']:>8} \\\\\n")

latex_output += r"""\bottomrule
\end{tabular}
\end{table}

\vspace{12pt}

\subsection*{Thermal Sensitivity: RMSD by Temperature Tercile}

To assess whether prediction errors inflate under thermal stress, we stratify pilot-scale 
RMSD (Root Mean Square Deviation) by temperature terciles: T1 (cool), T2 (mid), T3 (hot). 
The ratio RMSD$_{\mathrm{hot}}$/RMSD$_{\mathrm{cool}}$ quantifies thermal sensitivity. 
Values close to 1 indicate robust performance across the temperature range.

\begin{table}[H]\centering
\small
\caption{Thermal sensitivity indicators: RMSD stratified by temperature tercile. 
Ratio (Hot/Cool) quantifies error inflation under thermal stress; values near 1.0 
are preferred.}
\label{tab:SI_X_3_thermal_sensitivity}
\begin{tabular}{lllrrrr}
\toprule
\textbf{Model} & \textbf{Exper.} & \textbf{Variable} & \textbf{RMSD$_{\mathrm{cool}}$} & 
\textbf{RMSD$_{\mathrm{hot}}$} & \textbf{Ratio} \\
\midrule
"""

for _, row in df_x3.iterrows():
    latex_output += (f"{row['Model']} & {row['Experiment']} & {row['Variable']} & "
                    f"{row['RMSD_Cool(T1)']:>15} & {row['RMSD_Hot(T3)']:>15} & "
                    f"{row['Ratio(Hot/Cool)']:>8} \\\\\n")

latex_output += r"""\bottomrule
\end{tabular}
\end{table}

"""

# Save LaTeX
latex_file = os.path.join(METRICS_DIR, "SI_X_full_tables.tex")
with open(latex_file, 'w', encoding='utf-8') as f:
    f.write(latex_output)

print("\n" + "=" * 80)
print(f"LaTeX output saved to: {latex_file}")
print("=" * 80)

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"\n✓ Table SI-X.1 (Ablation):           {len(df_x1)} rows")
print(f"✓ Table SI-X.2 (Param Transfer):     {len(df_x2)} rows")
print(f"✓ Table SI-X.3 (Thermal Sensitivity): {len(df_x3)} rows")
print(f"\n✓ CSV exports saved to: {METRICS_DIR}/SI_X_*_formatted.csv")
print(f"✓ LaTeX tables saved to: {latex_file}")


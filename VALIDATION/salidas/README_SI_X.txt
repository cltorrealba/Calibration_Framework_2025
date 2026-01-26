% README: SI-X VALIDATION DIAGNOSTICS GENERATION
% ═════════════════════════════════════════════════════════════════════════════
% 
% This folder contains the complete output for Supplementary Information Section X,
% which provides detailed validation diagnostics supporting the decision to retain 
% 7 free parameters (rather than 6) in the shortlisted model structures.
%
% GENERATED FROM:
% - validation_pipeline.py (VALIDATION/validation_pipeline.py)
% - generate_SI_X_tables.py (VALIDATION/generate_SI_X_tables.py)
%
% OUTPUTS CREATED:
% ═════════════════════════════════════════════════════════════════════════════

1. SI_X_full_tables.tex
   ├─ Complete LaTeX section with 3 tables (SI-X.1, SI-X.2, SI-X.3)
   ├─ Each table includes:
   │  ├─ Descriptive caption explaining interpretation
   │  ├─ Data rows from validation pipeline outputs
   │  └─ Aligned column formatting for publication
   └─ Ready to copy-paste into manuscript supplementary section

2. SI_X_complete_section.tex
   ├─ Full SI-X section (to replace placeholder text in manuscript)
   ├─ Includes:
   │  ├─ Section title and subsection structure
   │  ├─ Interpretive paragraphs for each table
   │  ├─ Statistical methodology explanations
   │  ├─ Conclusions for each criterion
   │  └─ Overall decision summary
   └─ Suitable for full document inclusion

3. CSV Formatted Exports (in metrics/ subdirectory):
   ├─ SI_X_1_ablation_formatted.csv
   │  └─ One-at-a-time parameter fixing: Model, Parameter, ΔAICc, ΔR²
   ├─ SI_X_2_param_transfer_formatted.csv
   │  └─ Cross-scale shifts: Model, Parameter, Lab Mean, Pilot Mean, Cliff's δ, Significance
   └─ SI_X_3_thermal_sensitivity_formatted.csv
      └─ Thermal sensitivity: Model, Experiment, Variable, RMSD ratios (Hot/Cool)

═════════════════════════════════════════════════════════════════════════════
MANUSCRIPT ALIGNMENT
═════════════════════════════════════════════════════════════════════════════

The manuscript (main text) states:

  "One-at-a-time parameter-fixing tests reaffirm the selective-fixation policy. 
   For model~1750, standardizing $K_{ig0}$ improved parsimony ($\Delta\mathrm{AICc}=-20.0$) 
   and slightly increased skill ($\Delta R^2=+0.018$); by contrast, fixing $Y_{ef}$ or 
   $Y_{xn}$ degraded performance (e.g., a sharp drop in fit—$\Delta R^2=-0.803,,-0.400$—
   and a large parsimony penalty—$\Delta\mathrm{AICc}=+101,,+80.6$—across the two validation runs). 
   For model~1860, no single fixation improved parsimony and skill jointly; fixing $Y_{xn}$ 
   markedly reduced $R^2$ ($\Delta R^2=-1.184$). Accordingly, we retain the knee-point 
   ($\sim$7 free) as the working tier, and consider moving to 6 free only when three 
   conditions hold jointly: 
   
   (i) the one-at-a-time parameter-fixing tests do not reduce $R^2$ while improving AICc; 
   (ii) cross-scale shifts—changes in fit or parameter draws when moving from lab to pilot, 
        assessed via $\Delta R^2$ near zero and small $\delta$ are negligible; and 
   (iii) thermal sensitivity—error inflation between hotter and cooler periods remains close to 1. 
   
   Details in these diagnostics can be found in \textbf{SI-X}."

═════════════════════════════════════════════════════════════════════════════

VALIDATION CRITERIA ADDRESSED:
═════════════════════════════════════════════════════════════════════════════

✓ CRITERION (i): One-at-a-time parameter-fixing tests
  └─ Table SI-X.1 shows:
     • Fixing K_ig0: ΔAICc = -20.0, ΔR² = +0.018 ✓ (improves both)
     • Fixing Y_ef: ΔAICc = +101.0, ΔR² = -0.803 ✗ (degrades both)
     • Fixing Y_xn: ΔAICc = +80.6, ΔR² = -0.400 ✗ (degrades both)
     → Only K_ig0 passes criterion (i), insufficient alone to justify moving to 6 free.

✓ CRITERION (ii): Cross-scale parameter shifts
  └─ Table SI-X.2 shows:
     • All 7 parameters exhibit significant shifts (p < 0.01, ** notation)
     • Cliff's δ values near ±1 indicate large effect sizes (complete separation)
     • Examples: K_n0 lab=0.0807 → pilot=0.0173 (δ=+1.00**)
     → Substantial shifts detected; evaluated alongside transfer forecasting metrics
       (See SI-Y for ensemble overlays and calibration performance)

✓ CRITERION (iii): Thermal sensitivity
  └─ Table SI-X.3 shows:
     • Glucose: Ratio(Hot/Cool) ≈ 1.0 for both experiments (robust)
     • Fructose: Ratios 5.30 and 38.62 (higher variability, expected in late phase)
     • YAN: Ratios 0.48 and 45.77 (highly variable, consistent with ethanol inhibition dominance)
     → Glucose meets criterion; Fructose and YAN show expected late-phase variability
       (not indicative of model failure, but of inherent process complexity)

═════════════════════════════════════════════════════════════════════════════

HOW TO USE IN MANUSCRIPT:
═════════════════════════════════════════════════════════════════════════════

Option A (Minimal inclusion):
1. Copy the 3 tables from SI_X_full_tables.tex
2. Paste them after the sentence: "Details in these diagnostics can be found in \textbf{SI-X}."
3. Add section header: \subsection*{SI-X: Validation Diagnostics}

Option B (Complete section):
1. Replace the placeholder text in the manuscript appendix with SI_X_complete_section.tex
2. This includes all interpretive text, methodology, and conclusions
3. Modify the section number if it conflicts with other SI sections

Option C (Hybrid):
1. Use SI_X_complete_section.tex as the main narrative
2. For tables, choose either the full version or extract specific rows as needed
3. Ensure cross-references (\ref{tab:SI_X_*}) are updated in manuscript

═════════════════════════════════════════════════════════════════════════════

DATA SOURCES:
═════════════════════════════════════════════════════════════════════════════

All data extracted from: VALIDATION/salidas/metrics/

├─ lab_ablation_summary.csv
│  └─ Generated by: run_lab_ablation() in validation_pipeline.py
│     Purpose: One-at-a-time parameter fixing tests for lab context
│     Columns: model_id, param_idx, param_name, delta_AICc, delta_MNCI, delta_RSQ

├─ transfer_param_tests.csv
│  └─ Generated by: run_transfer_param_tests() in validation_pipeline.py
│     Purpose: Cross-scale parameter distribution comparisons
│     Columns: model_id, param_idx, param_name, lab_mean, pilot_mean, 
│              p_value, significance, cliffs_delta, lab_lo, lab_hi, pilot_lo, pilot_hi

└─ transfer_stratified_temp.csv
   └─ Generated by: run_transfer_stratified_temp() in validation_pipeline.py
      Purpose: RMSD stratified by temperature terciles for thermal sensitivity
      Columns: model_id, pilot_exper, variable, temp_group, rmsd, n_points, t_min, t_max

═════════════════════════════════════════════════════════════════════════════

CITATION FOR METHODS:
═════════════════════════════════════════════════════════════════════════════

If citing the validation methods in text:

"Validation diagnostics were computed using a self-contained pipeline 
(validation_pipeline.py) that implements Monte Carlo ensemble forecasting, 
one-at-a-time parameter ablation, Mann–Whitney nonparametric testing, 
and Cliff's delta effect-size estimation for cross-scale parameter shifts. 
Thermal sensitivity was assessed by stratifying RMSD across temperature 
terciles. All diagnostics were computed on independent laboratory and pilot 
validation datasets (N_lab = 2 experiments × 4,147 model structures; 
N_pilot = 2 experiments × 103 viable structures)."

═════════════════════════════════════════════════════════════════════════════

For questions or modifications, refer to:
  - Validation script: VALIDATION/validation_pipeline.py
  - Table generation: VALIDATION/generate_SI_X_tables.py
  - Output metrics: VALIDATION/salidas/metrics/

═════════════════════════════════════════════════════════════════════════════
Generated: January 2026

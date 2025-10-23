
This folder contains outputs from the new validation pipeline (validation_pipeline.py).

Key files:
- metrics/lab_metrics.csv: Per-variable indicators for lab validation runs.
- metrics/lab_meta.csv: Combo-level metadata (n_free, EDoF, FIM condition, timing, % at CI limits).
- metrics/pilot_lab_raw.csv and metrics/pilot_pilot_raw.csv: Raw per-variable metrics for lab and pilot contexts.
- metrics/pilot_meta.csv: Pilot combo-level metadata analogous to lab_meta.
- metrics/transfer_deltas.csv: Pilot minus Lab deltas in R2_adj and RMSD.
- metrics/transfer_param_tests.csv: Cross-scale parameter distribution comparisons (Mann–Whitney, Cliff's delta).
- metrics/transfer_fidelity.csv: Coverage and band widths for lab-forecasted pilot ensembles (95% and μ±1σ).
- metrics/transfer_effort_stats.csv: Effort proxies (pilot vs lab wall time ratios).
- metrics/transfer_yan_late_summary.csv: Pilot YAN late-phase bias and error aggregation.
- metrics/transfer_robustness_noise.csv: RMSD sensitivity to 5% synthetic noise in observations.
- metrics/transfer_stratified_temp.csv: RMSD stratified by temperature terciles.
- metrics/transfer_calibration.csv: Calibration curves and interval scores across alpha levels.
- metrics/transfer_go_nogo.csv: Simple go/no-go decision table by model.
- figs/ensemble_*.png: Simulation vs experimental panels with 10–90% bands.

Notes:
- Lab indicators implemented: (i)-(v), (vi) ablation, (vii), (viii), (ix via FIM cond proxy and % at CI limits), (x via wall time).
- Transfer indicators implemented: (i) deltas, (ii) raw metrics, (iii) parameter tests, (iv) fidelity (band coverage), (v) effort stats, (vi) YAN late summary, (vii) robustness to noise, (viii) stratification by disturbances (temperature), (ix) calibration curves/interval scores, (x) go/no-go table.

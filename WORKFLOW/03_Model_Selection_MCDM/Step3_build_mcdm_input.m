% Step3_build_mcdm_input.m
% Orchestrates LAB MonteCarlo post-processing and MCDM input generation.

% 1) Compute AICc/R2 metrics over LAB CV outputs
Procesador_AICc_Radj;

% 2) Build CI workbook per model
Process_IC_Corrected_2023b;

% 3) Build final criteria table + model index list for MCDM
Process_MNCI_AICc_CORRECTED_2023B;

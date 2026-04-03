# WORKFLOW — Curated Computational Pipeline

This folder contains all MATLAB scripts required to reproduce the 4-step parameter estimation and model selection workflow described in the paper.

## Directory Structure

```
WORKFLOW/
├── config.m                          # User configuration (paths, solver, settings)
├── run_full_pipeline.m               # Master orchestrator script
├── README.md                         # This file
│
├── 01_HIPPO_Identification/          # Step I: HIPPO algorithm
│   ├── HIPPO.m                       # Main HIPPO algorithm (builds iteration tree)
│   ├── load_problem_zent.m           # Problem definition, bounds, data loading
│   ├── iteration.m                   # Single iteration executor (ESS + statistics)
│   ├── decision.m                    # Fixation decision logic (CC ≥ 2, |Mc| ≥ T)
│   ├── add_it.m                      # Iteration tree node management
│   ├── obj_func.m                    # Objective function for optimizer
│   ├── solve_ODE.m                   # ODE solver wrapper (supports multiple solvers)
│   ├── reg_analysis.m                # Statistical analysis (AICc, BIC, CI, CC)
│   ├── lsq_func.m                    # lsqcurvefit objective wrapper
│   ├── obj_var.m                     # Variable extraction & normalization
│   ├── objf_n2fb.m                   # MEIGO compatibility wrapper
│   ├── plotResults.m                 # Visualization (optional)
│   ├── ssm_startup.p                 # MEIGO compiled function
│   ├── intconfianza.p                # Confidence interval calculation (compiled)
│   ├── identificaBSB.p              # Identifiability analysis (compiled)
│   └── ksensibilidadBSB.p           # Sensitivity analysis (compiled)
│
├── 02_CrossValidation_Calibration/   # Step II: Cross-validation
│   ├── All_CV_Main_5perc_LAB.m       # LAB-scale CV main script (5% noise)
│   ├── All_CV_Main_PIL.m             # PIL-scale CV main script
│   ├── CrossValidationCalibrationZ.m # CV objective function (exact data)
│   ├── CV_Z_Alter_Data.m             # CV objective function (5% noise perturbation)
│   ├── CV_CI_Main.m                  # PIL-scale CV with CI calculation
│   ├── Norm_Alter_Data.m             # Normal noise generator (normrnd-based)
│   └── Process_IC_Corrected.m        # Process results → writes xlsx with CI/AICc
│
├── 03_Model_Selection_MCDM/          # Step III: Multi-criteria decision making
│   ├── Model_Structures_2023b.m      # MCDM orchestrator (5 weight scenarios)
│   └── MCDM_methods/                 # 7 MCDM algorithms
│       ├── TOPSIS.m                  # Technique for Order of Preference
│       ├── LINMAP.m                  # Linear Programming Technique
│       ├── VIKOR.m                   # Compromise Ranking
│       ├── SAW.m                     # Simple Additive Weighting
│       ├── MEW.m                     # Multiplicative Exponent Weighting
│       ├── GRA.m                     # Gray Relational Analysis
│       └── FUCA.m                    # Faire Un Choix Adequat
│
├── 04_Scaleup_Validation/            # Step IV: Scale-up & Monte Carlo CI
│   ├── MonteCarlo_CI_Zent.m          # MC uncertainty quantification (200 samples)
│   ├── MonteCarlo_CI_Zent_Corrected_2023b.m  # 2023b version
│   └── Process_IC_PIL_2023.m         # Process PIL-scale IC results → xlsx
│
├── model/                            # Kinetic model definitions
│   ├── Zenteno_Model_2020_PEVth9.m   # Full ODE model (13 params, Arrhenius T-dep)
│   ├── ReSimulate_Zenteno_Optimal.m  # Re-simulation wrapper (split at DAP time)
│   └── ReSimulate_Zenteno_HIPPO.m    # HIPPO-specific re-simulation wrapper
│
├── data/                             # Experimental data
│   ├── DataLoad.m                    # Master data loading function
│   ├── Experimental_Codes.txt        # Experiment metadata
│   ├── FDA_DATA.txt                  # FDA addition data
│   ├── Stuck_YANs.txt               # Residual YAN corrections
│   ├── Bioreactor 2020 - cinética fermentación.xlsx
│   ├── Bin Automatizado 2020 - cinética fermentación.xlsx
│   └── [individual experiment .xlsx files]
│
└── dependency_generation/            # Scripts for generating/validating dependencies
```

## Prerequisites

- **MATLAB R2020b+** (tested on R2023a)
- **MEIGO/ESS toolbox** — included in `../Toolboxes/MEIGO64/MEIGO/`
  - Loaded automatically by `run_full_pipeline.m` via `config.m`
  - Source: https://github.com/gingproc-IIM-CSIC/MEIGO64
- **Parallel Computing Toolbox** — for `parfor` in cross-validation
- **Statistics and Machine Learning Toolbox** — for `tinv`, `normrnd`
- **Optimization Toolbox** — for `fmincon`

## Quick Start

1. Open MATLAB and `cd` into the `WORKFLOW/` folder
2. Run `run_full_pipeline.m` — it loads `config.m` and adds MEIGO to the path automatically
3. Each step is commented out by default; uncomment one at a time
4. Each step requires output artifacts from the previous step

## Key Artifacts (Input/Output Chain)

```
Step I  → it_2023.mat, VMS_it_2023.txt
Step II → Zenteno_IC_LAB_5PERC_2023b_WSComplete.xlsx
          Zenteno_IC_PIL_5PERC_2023b.xlsx
Step III → Model selection (bar plots, selected ID = 1860)
Step IV → Zenteno_IC_PIL_5PERC_2023.xlsx, MC envelopes
```

## Compiled Files (.p)

Four compiled MATLAB functions are included as `.p` files:
- `ssm_startup.p` — MEIGO initialization
- `intconfianza.p` — Confidence interval computation
- `identificaBSB.p` — Identifiability analysis (BSB method)
- `ksensibilidadBSB.p` — Sensitivity analysis (BSB method)

These require MATLAB R2020b+ to execute. Source code is not redistributable.

## MCDM Methods Reference

All 7 MCDM methods follow the implementation of Ricardo Luna Hernández,
based on: Wang Z. and Rangaiah G.P (2017). *Application and analysis of
Methods for Selecting an Optimal Solution from the Pareto-Optimal Front
obtained by Multiobjective Optimization.* Industrial & Engineering
Chemistry Research.

# Calibration_Framework_2025

Code and step-by-step scripts to reproduce the analysis in Torrealba et al. (2026).

## Repository Layout

```
├── WORKFLOW/                     # Curated MATLAB pipeline (4-step estimation)
│   ├── 01_HIPPO_Identification/  # Step I: HIPPO algorithm (16 files)
│   ├── 02_CrossValidation_Calibration/  # Step II: Cross-validation (7 files)
│   ├── 03_Model_Selection_MCDM/  # Step III: 7 MCDM methods (8 files)
│   ├── 04_Scaleup_Validation/    # Step IV: MC confidence intervals (3 files)
│   ├── model/                    # Kinetic model definitions (3 files)
│   ├── data/                     # Experimental data (20 files)
│   ├── dependency_generation/    # Validation & dependency mapping
│   ├── config.m                  # User configuration
│   ├── run_full_pipeline.m       # Master orchestrator
│   └── README.md                 # Detailed workflow documentation
│
├── Toolboxes/                    # Third-party MATLAB toolboxes
│   └── MEIGO64/                  # MEIGO global optimization (eSS, VNS)
│       └── MEIGO/                # install_MEIGO.m, eSS/, VNS/, examples/
│
├── RESULT ANALYSIS/              # Python analysis of MATLAB outputs
│   ├── STEP 1/                   # HIPPO and model-structure exploration
│   ├── STEP 2/                   # Stage I/II filtering and complexity diagnostics
│   ├── STEP 3/                   # Stage III robustness & MCDM diagnostics
│   ├── STEP 4/                   # Final ranking and integrated figures/tables
│   ├── VALIDATION/               # Laboratory/pilot validation pipeline
│   └── salidas/                  # Consolidated outputs (figures, tables, CSVs)
│
├── requirements.txt              # Python dependencies
└── .gitignore
```

## WORKFLOW — MATLAB Pipeline

The `WORKFLOW/` folder contains all curated MATLAB scripts needed to reproduce the 4-step parameter estimation and model selection workflow from scratch. See `WORKFLOW/README.md` for full documentation.

### Quick start (MATLAB)

```matlab
cd('WORKFLOW')
run('run_full_pipeline.m')   % Loads config.m automatically; adds MEIGO to path
```

`config.m` auto-detects the MEIGO path relative to the repo root (`Toolboxes/MEIGO64/MEIGO`). No manual path editing is needed unless you move files.

### Dependency check

```matlab
cd('WORKFLOW/dependency_generation')
validate_workflow_dependencies
```

## Toolboxes

The `Toolboxes/MEIGO64/` folder contains the [MEIGO64](https://github.com/gingproc-IIM-CSIC/MEIGO64) global optimization toolbox (eSS scatter search). It is loaded automatically by `run_full_pipeline.m`.

## RESULT ANALYSIS — Python Post-Processing

The `RESULT ANALYSIS/` folder contains Python scripts that analyze the MATLAB outputs (`.xlsx`, `.mat` artifacts).

### Python environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested execution order

1. `RESULT ANALYSIS/STEP 2/Analisis_Step_IyII.py`
2. `RESULT ANALYSIS/STEP 3/Analisis Step III.py`
3. `RESULT ANALYSIS/STEP 4/Análisis Step IV.py`
4. `RESULT ANALYSIS/VALIDATION/run_validation_pipeline.py`

Generated outputs are written under each step's `salidas/` directory.

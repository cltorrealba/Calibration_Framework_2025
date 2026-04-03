%% config.m — User configuration for the HIPPO/CV/MCDM pipeline
% Edit this file to match your local environment before running.

%% 1. Toolbox paths (MEIGO/ESS)
% Path is relative to the repo root (one level above WORKFLOW/).
% If you moved the toolbox elsewhere, update this path.
config.meigo_dir = fullfile(fileparts(fileparts(mfilename('fullpath'))), ...
                           'Toolboxes','MEIGO64','MEIGO','eSS');

%% 2. Data paths
config.data_dir   = fullfile(fileparts(mfilename('fullpath')),'data');
config.model_dir  = fullfile(fileparts(mfilename('fullpath')),'model');

%% 3. HIPPO outputs (auto-generated, do not set manually)
% Step I always writes:
%   01_HIPPO_Identification/it.mat
%   01_HIPPO_Identification/VMS_auto.txt
% Stage II consumes those files directly.

%% 4. Cross-validation settings
config.cv_n_iter        = 100;               % Number of MEIGO restarts per model
config.cv_noise_pct     = 0.05;              % Noise level for 5% perturbation (Alter_Data)
config.cv_maxeval       = 100;               % MEIGO max function evaluations
config.cv_maxtime       = 30;                % MEIGO max time per run (s)

%% 5. Model structure IDs used in the 2023 analysis
config.ids_2023         = [1, 1860, 2264, 2305];

%% 6. MCDM settings
config.mcdm_xlsx        = 'Zenteno_Final_2023b_WS.xlsx';
config.mcdm_index_file  = 'Zenteno_Model_Indexes_2023b.txt';
config.mcdm_gamma       = 0.5;              % VIKOR gamma parameter

%% 7. ODE solver
config.ode_solver       = @ode15s;
config.ode_RelTol       = 1e-3;
config.ode_AbsTol       = 1e-3;

%% 8. Scale identifiers
%   1 = LAB (laboratory bioreactor, 2L)
%   2 = PIL (pilot, 500L)
%   4 = IND (industrial)
config.scale_lab = 1;
config.scale_pil = 2;
config.scale_ind = 4;

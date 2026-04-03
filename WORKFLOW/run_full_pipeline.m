%% run_full_pipeline.m — Master orchestrator for the full estimation workflow
%
% This script executes the 4-step pipeline sequentially:
%   Step I:   HIPPO identification (parameter fixation tree)
%   Step II:  Cross-validation calibration (LAB + PIL scales)
%   Step III: MCDM model structure selection
%   Step IV:  Scale-up validation (MonteCarlo confidence intervals)
%
% Prerequisites:
%   - MEIGO/ESS toolbox on MATLAB path
%   - Experimental data in data/ folder
%   - Edit configurate.m to match your environment
%
% NOTE: Each step is computationally intensive.
%       Steps are designed to run independently given the right .mat inputs.

clear; clc; close all;

%% Load configuration
run('configurate.m');
addpath(config.data_dir);
addpath(config.model_dir);

%% Add MEIGO toolbox to path
if ~exist('ess_kernel','file')
    assert(isfolder(config.meigo_dir), ...
        'MEIGO not found at %s — edit configurate.m', config.meigo_dir);
    addpath(genpath(config.meigo_dir));
    fprintf('  MEIGO added to path from: %s\n', config.meigo_dir);
end

%% ======================================================================
%  STEP I — HIPPO Identification
%  Output: it.mat (iteration tree), VMS_auto.txt (auto-selected viable models)
% =======================================================================
fprintf('\n===== STEP I: HIPPO Identification =====\n');
cd('01_HIPPO_Identification');
addpath(pwd);

% Uncomment to run (takes hours):
% HIPPO;
cd('..');

%% ======================================================================
%  STEP II — Viable Structure Selection (LAB)
%  Uses HIPPO output to identify viable structures (VMS_auto.txt)
%  Output: VMS_auto.txt
% =======================================================================
fprintf('\n===== STEP II: Viable Structure Selection =====\n');
cd('01_HIPPO_Identification');
generate_vms_from_it('it.mat','VMS_auto.txt');
fprintf('  VMS generated from Step I: 01_HIPPO_Identification/VMS_auto.txt\n');
cd('..');
%% ======================================================================
%  STEP III — LAB MonteCarlo + Metrics + MCDM Model Structure Selection
%  1) LAB CV nested-MC calibration for VMS models
%  2) Build AICc/R2/CI/Sensitivity criteria table
%  3) Run MCDM structure selection
%  Evaluates via: TOPSIS, LINMAP, VIKOR, SAW, MEW, GRA, FUCA
%  Under 5 weighting scenarios (No priority, Parsimony, Significance, Performance, Sensitivity)
%  Output: Zenteno_Final_2023b_WS.xlsx, bar plots, selected model ID
% =======================================================================
fprintf('\n===== STEP III: LAB Calibration + MCDM =====\n');

cd('02_CrossValidation_Calibration');
addpath(pwd);
% All_CV_Main_5perc_LAB;
cd('..');

cd('03_Model_Selection_MCDM');
addpath(pwd);
addpath('MCDM_methods');

% Step3_build_mcdm_input;

Model_Structures_2023b;

cd('..');

%% ======================================================================
%  STEP IV — Scale-up Validation & MonteCarlo CI
%  Transfers selected LAB model structure to pilot scale and re-calibrates
%  Computes Monte Carlo confidence intervals
%  Output: Zenteno_IC_PIL_5PERC_2023.xlsx, MC simulation envelopes
% =======================================================================
fprintf('\n===== STEP IV: Scale-up Validation =====\n');

cd('04_Scaleup_Validation');
addpath(pwd);
% All_CV_Main_PIL;

addpath(pwd);

% Process PIL-scale IC results
Procesador_AICc_Radj_PIL;
Process_IC_PIL_2023;

% Monte Carlo confidence intervals
% Uncomment to run:
MonteCarlo_CI_PIL;

cd('..');

fprintf('\n===== Pipeline complete =====\n');

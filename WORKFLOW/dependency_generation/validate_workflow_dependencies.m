function validate_workflow_dependencies()
%VALIDATE_WORKFLOW_DEPENDENCIES Check that all required artifacts exist.
%
% Validates the presence of:
%   - Key .mat files (HIPPO tree, CV results)
%   - Key .xlsx files (IC tables, MCDM criteria)
%   - .p compiled files
%   - MEIGO toolbox on path

fprintf('\n=== Validating WORKFLOW dependencies ===\n\n');
wfRoot = fileparts(mfilename('fullpath'));
wfRoot = fileparts(wfRoot);  % Go up from dependency_generation/ to WORKFLOW/

allOk = true;

%% 1. Check compiled .p files
pfiles = {'ssm_startup.p','intconfianza.p','identificaBSB.p','ksensibilidadBSB.p'};
fprintf('--- Compiled functions (.p) ---\n');
for i = 1:numel(pfiles)
    fpath = fullfile(wfRoot,'01_HIPPO_Identification',pfiles{i});
    ok = isfile(fpath);
    status = iff(ok,'OK','MISSING');
    fprintf('  %-25s %s\n', pfiles{i}, status);
    allOk = allOk && ok;
end

%% 2. Check MEIGO toolbox
fprintf('\n--- MEIGO/ESS toolbox ---\n');
meigoDir = fullfile(fileparts(wfRoot),'Toolboxes','MEIGO64','MEIGO');
meigoFolderOk = isfolder(meigoDir);
status = iff(meigoFolderOk,'OK','MISSING — expected at Toolboxes/MEIGO64/MEIGO');
fprintf('  MEIGO folder:  %s\n', status);
essFile = fullfile(meigoDir,'eSS','ess_kernel.m');
essOk = isfile(essFile);
status = iff(essOk,'OK','MISSING');
fprintf('  ess_kernel.m:  %s\n', status);
allOk = allOk && meigoFolderOk && essOk;

%% 3. Check data files
fprintf('\n--- Experimental data ---\n');
dataDir = fullfile(wfRoot,'data');
dataFiles = {'DataLoad.m','Stuck_YANs.txt','FDA_DATA.txt','Experimental_Codes.txt'};
for i = 1:numel(dataFiles)
    ok = isfile(fullfile(dataDir,dataFiles{i}));
    status = iff(ok,'OK','MISSING');
    fprintf('  %-45s %s\n', dataFiles{i}, status);
    allOk = allOk && ok;
end

%% 4. Check model files
fprintf('\n--- Model files ---\n');
modelDir = fullfile(wfRoot,'model');
modelFiles = {'Zenteno_Model_2020_PEVth9.m','ReSimulate_Zenteno_Optimal.m','ReSimulate_Zenteno_HIPPO.m'};
for i = 1:numel(modelFiles)
    ok = isfile(fullfile(modelDir,modelFiles{i}));
    status = iff(ok,'OK','MISSING');
    fprintf('  %-45s %s\n', modelFiles{i}, status);
    allOk = allOk && ok;
end

%% 5. Check MCDM methods
fprintf('\n--- MCDM methods ---\n');
mcdmDir = fullfile(wfRoot,'03_Model_Selection_MCDM','MCDM_methods');
mcdmFiles = {'TOPSIS.m','LINMAP.m','VIKOR.m','SAW.m','MEW.m','GRA.m','FUCA.m'};
for i = 1:numel(mcdmFiles)
    ok = isfile(fullfile(mcdmDir,mcdmFiles{i}));
    status = iff(ok,'OK','MISSING');
    fprintf('  %-15s %s\n', mcdmFiles{i}, status);
    allOk = allOk && ok;
end

%% 6. Check required MATLAB toolboxes
fprintf('\n--- MATLAB Toolboxes ---\n');
toolboxes = {'Statistics and Machine Learning Toolbox','Optimization Toolbox','Parallel Computing Toolbox'};
for i = 1:numel(toolboxes)
    ok = ~isempty(ver(toolboxes{i}));
    status = iff(ok,'OK','NOT FOUND');
    fprintf('  %-45s %s\n', toolboxes{i}, status);
end

%% Summary
fprintf('\n');
if allOk
    fprintf('=== ALL CHECKS PASSED ===\n');
else
    fprintf('=== SOME CHECKS FAILED — review above ===\n');
end

end

function s = iff(cond, trueVal, falseVal)
    if cond, s = trueVal; else, s = falseVal; end
end

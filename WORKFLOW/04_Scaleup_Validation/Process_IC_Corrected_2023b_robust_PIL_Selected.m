% Process_IC_Corrected_2023b_robust_PIL_Selected.m
% Build per-model confidence-interval workbook from PIL_WS_metrics.mat
% Uses the selected model IDs and writes Zenteno_IC_PIL_5PERC.xlsx

clearvars -except All_Result ids it

if ~exist('All_Result','var') || ~exist('ids','var')
    load('PIL_WS_metrics.mat','All_Result','ids');
end

if ~exist('it','var')
    load(fullfile('..','01_HIPPO_Identification','it.mat'),'it');
end

filename = 'Zenteno_IC_PIL_5PERC.xlsx';

if exist(filename,'file')
    delete(filename);
end

A = fields(All_Result);

% IDs realmente existentes en el .mat cargado
ids_exist = [];
for i = 1:length(A)
    Model_N = sscanf(A{i}, 'Model_%d');
    ids_exist = [ids_exist Model_N];
end

% Guardar también trazabilidad de IDs presentes en este workspace
writematrix(ids_exist(:), 'ids_exist_PIL.txt');

for i = 1:length(A)
    B = fields(All_Result.(A{i}));

    f = [];
    g = [];
    m = [];
    x = [];

    for n = 1:length(B)
        if isfield(All_Result.(A{i}).(B{n}),'mRsq2') && ...
           isfield(All_Result.(A{i}).(B{n}),'mAICc') && ...
           isfield(All_Result.(A{i}).(B{n}),'pars')  && ...
           ~isnan(All_Result.(A{i}).(B{n}).mRsq2)

            f = [f; All_Result.(A{i}).(B{n}).mRsq2];
            g = [g; All_Result.(A{i}).(B{n}).mAICc];
            m = [m; All_Result.(A{i}).(B{n}).pars];
            x = [x; n];
        end
    end

    if isempty(m)
        warning('Model %s has no valid summary statistics. Skipping sheet.', A{i});
        continue
    end

    % Params
    MEAN = mean(m,1);
    STD  = std(m,0,1);

    % CI
    SEM = STD/sqrt(size(m,1));

    if size(m,1) > 1
        ts = tinv([0.025 0.975], size(m,1)-1);
        CI = MEAN + ts'.*SEM;
    else
        CI = [MEAN; MEAN];
    end

    N_Model = ids_exist(i);
    idxs_unfixed = find(isnan(it.codes{N_Model,2}.kfixed));

    % Cell
    bottom = [0 MEAN mean(f) mean(g); ...
              0 STD  std(f,0,1) std(g,0,1); ...
              zeros(2,1) CI zeros(2,2)];

    Ar = num2cell([x m f g; bottom]);

    Ar{end-3,1} = 'MEAN';
    Ar{end-2,1} = 'STD';
    Ar{end-1,1} = 'CI-';
    Ar{end,1}   = 'CI+';

    b = size(m,2);
    names = cell(1,b+3);
    names{1,1}   = 'N° Iteration';
    names{1,b+2} = 'mRsq';
    names{1,b+3} = 'AICc';

    for u = 1:length(idxs_unfixed)
        names{u+1} = strcat('th_',num2str(idxs_unfixed(u)));
    end

    T = cell2table(Ar,'VariableNames',names);
    sheet_name = strcat('Z_',num2str(N_Model));
    writetable(T,filename,'Sheet',sheet_name);
end
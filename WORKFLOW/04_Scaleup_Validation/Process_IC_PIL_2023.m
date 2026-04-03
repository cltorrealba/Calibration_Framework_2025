% Process_IC_Corrected_2023b_robust.m
% Build per-model confidence-interval workbook from LAB_WS_metrics.mat

clc
clear

if ~exist('All_Result','var') || ~exist('ids','var')
    load('PIL_WS_metrics.mat','All_Result','ids');
end

if ~exist('it','var')
    load(fullfile('..','01_HIPPO_Identification','it.mat'),'it');
end

if ~exist('ids','var')
    ids = load(fullfile('..','03_Model_Selection_MCDM','Selected_Model_ID.txt'));
end

modelNames = fields(All_Result);
filename = 'Zenteno_IC_PIL_5PERC.xlsx';

A = fields(All_Result);

for i = 1:length(A)
    B = fields(All_Result.(A{i}));
    f = [];
    g = [];
    m = [];
    x = [];
    for n = 1:length(B)
       if  ~isnan(All_Result.(A{i}).(B{n}).mRsq2)
           f = [f; All_Result.(A{i}).(B{n}).mRsq2];
           g = [g; All_Result.(A{i}).(B{n}).mAICc];
           m = [m; All_Result.(A{i}).(B{n}).pars];
           x = [x; n];
       else
           continue
       end
    end
    
    %Params
    MEAN = mean(m);
    STD  = std(m,0,1);
    
    %CI
    SEM = STD/sqrt(length(m));                  % Standard Error
    ts = tinv([0.025  0.975],length(m)-1);      % T-Score
    CI = MEAN + ts'.*SEM;                       % Confidence Intervals

    N_Model = ids(i);
    idxs_unfixed = find(isnan(it.codes{N_Model,2}.kfixed));

    %Cell
    bottom = [0 MEAN mean(f) mean(g); 0 STD std(f,0,1) std(g,0,1); zeros(2,1) CI zeros(2,2)];
    Ar   = num2cell([x m f g; bottom]);
    Ar{end-3,1} = 'MEAN'; Ar{end-2,1} = 'STD'; Ar{end-1,1} = 'CI-'; Ar{end,1} = 'CI+';  
    b = size(m,2);
    names = cell(1,b+3); names{1,1} = 'N° Iteration'; names{1,b+2} = 'mRsq'; names{1,b+3} = 'AICc'; 
    
    for u = 1:length(idxs_unfixed)
        names{u+1} = strcat('th_',num2str(idxs_unfixed(u)));
    end
    
    B=cell2table(Ar,'VariableNames',names);
    sheet_name = strcat('Z_',num2str(N_Model));
    writetable(B,filename,'sheet',sheet_name);
end

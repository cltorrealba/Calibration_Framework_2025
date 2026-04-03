% Process_MNCI_AICc_CORRECTED_2023B.m
% Generate final criteria table for MCDM: Zenteno_Final_2023b_WS.xlsx
global it
clearvars -except ids_exist it

if ~exist('ids','var')
    ids = load(fullfile('..','01_HIPPO_Identification','VMS_auto.txt'));
end
if ~exist('it','var')
    load(fullfile('..','01_HIPPO_Identification','it.mat'),'it');
end
if ~exist('ids_exist','var')
    ids_exist = load(fullfile('..','03_Model_Selection_MCDM','ids_exist.txt'));
end

src_xlsx = 'Zenteno_IC_LAB_5PERC.xlsx';
out_xlsx = 'Zenteno_Final.xlsx';
out_idx = 'Zenteno_Model_Indexes.txt';

NORM_I = [];
AICc   = [];
MNCI   = [];
RSQ2   = [];

for i = 1:length(ids_exist)
    try
        Model_N     = ids_exist(i);
        sheet       = strcat('Z_',num2str(Model_N));
        T           = readtable(src_xlsx,'sheet',sheet);
        means       = table2array(T(end-3,:));
        AICc(i)     = means(end);
        RSQ2(i)     = means(end-1);
        CV_PARAMS   = means(2:end-2);
        disp(i); pause(2)
        [~,I]       = HaoSensitivityZenteno_2023(Model_N,CV_PARAMS);
        [~,col]     = size(I);
        NORM_I(i,:) = (sum(I,2)/col)';
        ICs         =  table2array(T(end-1:end,2:end-2));
        IC_w        =  abs(abs(ICs(1,:))-abs(ICs(2,:)));
        Rat         =  abs(IC_w./CV_PARAMS);
        MNCI(i)     =  sum(Rat)/length(CV_PARAMS);
    end
end

PARSIMONY = AICc';
SIGNFICANCE = MNCI';
PERF = RSQ2';
SENS = sum(NORM_I,2);

keep = isfinite(PARSIMONY);
ModelID = ids_exist(keep);
criteria = [PARSIMONY(keep), SIGNFICANCE(keep), PERF(keep), SENS(keep)];

Tout = table(ModelID, criteria(:,1), criteria(:,2), criteria(:,3), criteria(:,4), ...
    'VariableNames', {'ModelID','PARSIMONY','SIGNFICANCE','PERF','SENS'});

writetable(Tout, out_xlsx, 'Sheet', 'Criteria');
writematrix(ModelID, out_idx, 'Delimiter', 'tab');

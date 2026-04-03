% Procesador_AICc_Radj.m
% Enrich LAB CV MonteCarlo outputs with AICc, adjusted R2 and parameter stats.

clearvars -except All_Result it ids

if ~exist('All_Result','var')
    load(fullfile('..','02_CrossValidation_Calibration','5_perc_Models_Z_LAB.mat'),'All_Result');
end
if ~exist('it','var')
    load(fullfile('..','01_HIPPO_Identification','it.mat'),'it');
end
if ~exist('ids','var')
    ids = load(fullfile('..','01_HIPPO_Identification','VMS_auto.txt'));
end

%% Build global data containers used by R2_AICc/HaoSensitivity.
global Measure_Inds time_daps FDA_add_idxs Kinetic_Matrixes x0s int_times exp_temps 
n = 0;
for j = 1
    for i = 1:5
        if j == 1 && i == 1
            continue
        end
        
        %Experiment Selection
        exper_id    =   i;
        scale_id    =   j;
        ifplot      =   false;
        
        %Operational/Kinetic information structures construction using the previous information
        [Kinetic_Matrix,Time_Temp_Pairs,Measure_Ind,FDA_Rho_Time_Pair] = DataLoad(scale_id,exper_id,ifplot);

        Measure_Inds{i,j} = Measure_Ind;

        % Operational Parameter Definition

        %Intermidiate DAP addition related information
        rho_dap      = FDA_Rho_Time_Pair(1);      % Density at which DAP was added (kg/m3)
        time_dap     = FDA_Rho_Time_Pair(2);      % Experimental time where DAP was added (h)
        dap          = 20;                        % DAP dosis g/hL

        time_daps{i,j} = time_dap;

        %Residual YAN corrections
        FDA_add_idx  = find(ismember(Time_Temp_Pairs(Measure_Ind),time_dap));

        FDA_add_idxs{i,j} = FDA_add_idx;
        
        Stuck_YANs = load('Stuck_YANs.txt'); Stuck_YAN = Stuck_YANs(exper_id,scale_id);
        
        Kinetic_Matrix(:,4) = Kinetic_Matrix(:,4) - ones(size(Kinetic_Matrix(:,4))).*Stuck_YAN;
        Kinetic_Matrix((Kinetic_Matrix(:,4)<0),4) = 0;

        Kinetic_Matrixes{i,j} = Kinetic_Matrix;

        %Initial conditions information
        X0       = 0.2;                         %Yeast dosis   (g/L)
        N0       = Kinetic_Matrix(1,4)/1000;    %Initial YAN   (g/L)
        G0       = Kinetic_Matrix(1,1);         %Initial Glu   (g/L)
        F0       = Kinetic_Matrix(1,2);         %Initial Fru   (g/L)
        E0       = 0;                           %Initial Eth   (g/L)
        CO20     = 0;                           %Initial CO2   (g/L)
        T0       = Time_Temp_Pairs(1,2)+273.15; %Initial Must T (K)
        x0       = [X0, N0, G0, F0, E0];

        x0s{i,j}   = x0;

        %Temperature and integration time information
        int_time = Time_Temp_Pairs(:,1);      %Experimental times for integration (h)
        exp_temp = Time_Temp_Pairs(:,2);      %Experimental temperatures for integration (C°)

        %Eliminate repeated times
        [int_time,IA,~] = unique(int_time);
        exp_temp        = exp_temp(IA);

        int_times{i,j}    = int_time;
        exp_temps{i,j}    = exp_temp;
        
        n   =   n + size(Kinetic_Matrix,1);
    end
end
%% Compute GOF indices and parameters average
scale_id = 1;
A = fields(All_Result);
u= 1;
for i = 1:length(ids)
    if strcmp(A{u},strcat('Model_',num2str(ids(i)))) %We add a check step in case any models are missing from MC calibration step
        kfixed = it.codes{ids(i), 2}.kfixed;
        B = fields(All_Result.(A{u}));
        for j = 1:length(B)
            DATA = All_Result.(A{u}).(B{j}).data;
            C = fields(All_Result.(A{u}).(B{j}));
            AICS = zeros(length(C)-1,1);
            MRSQ = zeros(length(C)-1,1);
            pars = zeros(length(C)-1,length(kfixed(isnan(kfixed))));
            for k = 1:length(C)-2
                if  isfield(All_Result.(A{u}).(B{j}).(C{k}),'xbest')
                    pars(k,:) = All_Result.(A{u}).(B{j}).(C{k}).xbest;
                    p = All_Result.(A{u}).(B{j}).(C{k}).xbest;
                    Valid_set = All_Result.(A{u}).(B{j}).(C{k}).Valid_set;
                    data = DATA{Valid_set};
                    [Rsq2,AICc] =  R2_AICc(p,Valid_set,data,scale_id,kfixed);
                    All_Result.(A{u}).(B{j}).(C{k}).AICc  = AICc; AICS(k) = AICc;
                    All_Result.(A{u}).(B{j}).(C{k}).Rsq2  = Rsq2;
                    All_Result.(A{u}).(B{j}).(C{k}).mRsq2 = mean(Rsq2); MRSQ(k) = mean(Rsq2);
                else
                    AICS(k)     = [];
                    MRSQ(k)     = [];
                    pars(k,:)   = [];
                    continue
                end
            end
            All_Result.(A{u}).(B{j}).mAICc = mean(AICS);
            All_Result.(A{u}).(B{j}).mRsq2 = mean(MRSQ);
            All_Result.(A{u}).(B{j}).pars  = mean(pars);
        end
        u = u+1;
    else
        continue
    end
end
save('LAB_WS_metrics.mat','All_Result','ids');

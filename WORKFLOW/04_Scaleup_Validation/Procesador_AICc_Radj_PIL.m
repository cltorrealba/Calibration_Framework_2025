% Procesador_AICc_Radj_PIL_Selected.m
% Enrich PIL CV MonteCarlo outputs with AICc, adjusted R2 and parameter stats.
% Uses only the model IDs listed in Selected_Model_ID.txt

clc
clear

if ~exist('All_Result','var')
    load(fullfile('..','04_Scaleup_Validation','5_perc_Models_Z_PIL.mat'),'All_Result');
end
if ~exist('it','var')
    load(fullfile('..','01_HIPPO_Identification','it.mat'),'it');
end
if ~exist('ids','var')
    ids = load(fullfile('..','03_Model_Selection_MCDM','Selected_Model_ID.txt'));
end

ids = ids(:)';  % asegurar vector fila

%% Build global data containers used by R2_AICc/HaoSensitivity
global Measure_Inds time_daps FDA_add_idxs Kinetic_Matrixes x0s int_times exp_temps
n = 0;

for j = 2   % PIL scale
    for i = 1:4
        if j == 1 && i == 1
            continue
        end

        % Experiment selection
        exper_id = i;
        scale_id = j;
        ifplot   = false;

        % Operational/Kinetic information structures construction
        [Kinetic_Matrix,Time_Temp_Pairs,Measure_Ind,FDA_Rho_Time_Pair] = DataLoad(scale_id,exper_id,ifplot);

        Measure_Inds{i,j} = Measure_Ind;

        % Intermediate DAP addition related information
        rho_dap  = FDA_Rho_Time_Pair(1); 
        time_dap = FDA_Rho_Time_Pair(2);
        dap      = 20; 

        time_daps{i,j} = time_dap;

        % Residual YAN corrections
        FDA_add_idx = find(ismember(Time_Temp_Pairs(Measure_Ind),time_dap));
        FDA_add_idxs{i,j} = FDA_add_idx;

        Stuck_YANs = load('Stuck_YANs.txt');
        Stuck_YAN  = Stuck_YANs(exper_id,scale_id);

        Kinetic_Matrix(:,4) = Kinetic_Matrix(:,4) - ones(size(Kinetic_Matrix(:,4))).*Stuck_YAN;
        Kinetic_Matrix((Kinetic_Matrix(:,4)<0),4) = 0;

        Kinetic_Matrixes{i,j} = Kinetic_Matrix;

        % Initial conditions information
        X0   = 0.2;                          % Yeast dosis (g/L)
        N0   = Kinetic_Matrix(1,4)/1000;     % Initial YAN (g/L)
        G0   = Kinetic_Matrix(1,1);          % Initial Glu (g/L)
        F0   = Kinetic_Matrix(1,2);          % Initial Fru (g/L)
        E0   = 0;                            % Initial Eth (g/L)
        CO20 = 0;
        T0   = Time_Temp_Pairs(1,2)+273.15; 
        x0   = [X0, N0, G0, F0, E0];

        x0s{i,j} = x0;

        % Temperature and integration time information
        int_time = Time_Temp_Pairs(:,1);
        exp_temp = Time_Temp_Pairs(:,2);

        [int_time,IA,~] = unique(int_time);
        exp_temp = exp_temp(IA);

        int_times{i,j} = int_time;
        exp_temps{i,j} = exp_temp;

        n = n + size(Kinetic_Matrix,1);
    end
end

%% Compute GOF indices and parameters average
scale_id = 2;   % PIL
A = fields(All_Result);
u = 1;

for i = 1:length(ids)

    target_field = strcat('Model_', num2str(ids(i)));

    % avanzar en A hasta encontrar el modelo, por robustez
    while u <= length(A) && ~strcmp(A{u}, target_field)
        u = u + 1;
    end

    if u > length(A)
        warning('Model %d not found in All_Result. Skipping.', ids(i));
        continue
    end

    kfixed = it.codes{ids(i),2}.kfixed;
    B = fields(All_Result.(A{u}));

    for j = 1:length(B)

        if ~isstruct(All_Result.(A{u}).(B{j}))
            continue
        end

        if ~isfield(All_Result.(A{u}).(B{j}),'data')
            warning('Model %d, block %s has no field "data". Skipping block.', ids(i), B{j});
            continue
        end

        DATA = All_Result.(A{u}).(B{j}).data;
        C = fields(All_Result.(A{u}).(B{j}));

        AICS = [];
        MRSQ = [];
        pars = [];

        for k = 1:length(C)

            if strcmp(C{k},'data')
                continue
            end

            if isstruct(All_Result.(A{u}).(B{j}).(C{k})) && ...
               isfield(All_Result.(A{u}).(B{j}).(C{k}),'xbest') && ...
               isfield(All_Result.(A{u}).(B{j}).(C{k}),'Valid_set')

                p = All_Result.(A{u}).(B{j}).(C{k}).xbest;
                Valid_set = All_Result.(A{u}).(B{j}).(C{k}).Valid_set;
                data = DATA{Valid_set};

                pars = [pars; p(:)'];

                [Rsq2,AICc] = R2_AICc(p,Valid_set,data,scale_id,kfixed);

                All_Result.(A{u}).(B{j}).(C{k}).AICc  = AICc;
                All_Result.(A{u}).(B{j}).(C{k}).Rsq2  = Rsq2;
                All_Result.(A{u}).(B{j}).(C{k}).mRsq2 = mean(Rsq2);

                AICS = [AICS; AICc];
                MRSQ = [MRSQ; mean(Rsq2)];
            end
        end

        if ~isempty(AICS)
            All_Result.(A{u}).(B{j}).mAICc = mean(AICS);
        else
            All_Result.(A{u}).(B{j}).mAICc = NaN;
        end

        if ~isempty(MRSQ)
            All_Result.(A{u}).(B{j}).mRsq2 = mean(MRSQ);
        else
            All_Result.(A{u}).(B{j}).mRsq2 = NaN;
        end

        if ~isempty(pars)
            All_Result.(A{u}).(B{j}).pars = mean(pars,1);
        else
            All_Result.(A{u}).(B{j}).pars = NaN(1,length(kfixed(isnan(kfixed))));
        end
    end

    u = u + 1;
end

save('PIL_WS_metrics.mat','All_Result','ids');
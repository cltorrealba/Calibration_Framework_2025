%--------------------Cross-Validation Optimization Problem------------------%
% LAB scale cross-validation calibration with 5% noise perturbation
% Iterates over viable model structures, running MEIGO/ESS optimization
% with leave-one-out cross-validation on LAB experiments.
%
% Requires: DataLoad.m, ../01_HIPPO_Identification/it.mat,
%           ../01_HIPPO_Identification/VMS_auto.txt,
%           CrossValidationCalibrationZ_Alter_Data.m, ess_kernel (MEIGO)
%
% Outputs:  2023_5_perc_Models_Z_LAB_Corrected.mat

%% Data Loading

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
        
        [Kinetic_Matrix,Time_Temp_Pairs,Measure_Ind,FDA_Rho_Time_Pair] = DataLoad(scale_id,exper_id,ifplot);

        Measure_Inds{i,j} = Measure_Ind;

        % Operational Parameter Definition
        rho_dap      = FDA_Rho_Time_Pair(1);
        time_dap     = FDA_Rho_Time_Pair(2);
        dap          = 20;

        time_daps{i,j} = time_dap;

        FDA_add_idx  = find(ismember(Time_Temp_Pairs(Measure_Ind),time_dap));
        if isempty(FDA_add_idx)
            measure_times = Time_Temp_Pairs(Measure_Ind);
            [~,FDA_add_idx] = min(abs(measure_times - time_dap));
            warning('FDA_add_idx not exact for LAB exp %d; using nearest index %d.', exper_id, FDA_add_idx);
        end
        FDA_add_idxs{i,j} = FDA_add_idx;
        
        Stuck_YANs = load('Stuck_YANs.txt'); Stuck_YAN = Stuck_YANs(exper_id,scale_id);
        
        Kinetic_Matrix(:,4) = Kinetic_Matrix(:,4) - ones(size(Kinetic_Matrix(:,4))).*Stuck_YAN;
        Kinetic_Matrix((Kinetic_Matrix(:,4)<0),4) = 0;

        Kinetic_Matrixes{i,j} = Kinetic_Matrix;

        X0       = 0.2;
        N0       = Kinetic_Matrix(1,4)/1000;
        G0       = Kinetic_Matrix(1,1);
        F0       = Kinetic_Matrix(1,2);
        E0       = 0;
        x0       = [X0, N0, G0, F0, E0];

        x0s{i,j}   = x0;

        int_time = Time_Temp_Pairs(:,1);
        exp_temp = Time_Temp_Pairs(:,2);

        [int_time,IA,~] = unique(int_time);
        exp_temp        = exp_temp(IA);

        int_times{i,j}    = int_time;
        exp_temps{i,j}    = exp_temp;
        
        n   =   n + size(Kinetic_Matrix,1);
    end
end

%% CV setup
scale_id = 1;
calib_experiments = 2:5;
NExp = 100;

%% MEIGO

opts_SSm.maxeval      = 100;
opts_SSm.local.n2     = 1;
opts_SSm.local.n1     = 1;
opts_SSm.maxtime      = 30;
opts_SSm.strategy     = 3;
opts_SSm.local.solver = 'fmincon';
opts_SSm.local.finish = 'fmincon';
opts_SSm.combination  = 1;  
opts_SSm.local.tol    = 1;  
opts_SSm.local.iterprint    = 1;  
opts_SSm.iterprint    = 1;  

%% HIPPO Results
hippo_dir = fullfile('..','01_HIPPO_Identification');
load(fullfile(hippo_dir,'it.mat'),'it')
ids = load(fullfile(hippo_dir,'VMS_auto.txt')); ids = ids(:,1);
scale_id = 1;

problem.f = 'CrossValidationCalibrationZ_Alter_Data';

for n = 1:length(ids)
    N_Model = ids(n);
    [kfixed, free_idx, x0_free] = build_cv_seed_from_it(it, N_Model);
    str_m = strcat('Model_', num2str(N_Model));

    kL = max(1e-8, x0_free * 0.5);
    kU = max(kL * 1.05, x0_free * 2.0);

    problem.x_L = [];
    problem.x_0 = [];
    problem.x_U = [];

    j = 1;
    for p = 1:numel(free_idx)
        lb = min(kL(p), kU(p));
        ub = max(kL(p), kU(p));
        x0p = x0_free(p);

        if ~isfinite(x0p) || x0p <= 0
            x0p = max(abs(x0p), 1e-6);
        end

        x0p = min(max(x0p, lb), ub);

        problem.x_L(j) = lb;
        problem.x_0(j) = x0p;
        problem.x_U(j) = ub;
        j = j + 1;
    end

    RESULTS = struct();
    n_success = 0;
    last_err_msg = '';

    for i = 1:NExp
        disp('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
        disp('N of iteration:')
        disp(i)
        disp('N of Model:')
        disp(N_Model)
        disp('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')

        data = cell(max(calib_experiments),1);
        for jj = calib_experiments
            if i == 1
                data{jj,1} = Kinetic_Matrixes{jj,scale_id};
            else
                data{jj,1} = Norm_Alter_Data(Kinetic_Matrixes{jj,scale_id},0.05);
            end
        end

        Results = struct();
        Results.data = data;

        aux = 1;
        cv_success = 0;

        for v = calib_experiments
            Calib_set = calib_experiments(calib_experiments ~= v);

            try
                Result = ess_kernel(problem, opts_SSm, Calib_set, data, scale_id, kfixed);
                Result.Calib_set = Calib_set;
                Result.Valid_set = v;

                str_cv = strcat('CV', num2str(aux));
                Results.(str_cv) = Result;

                aux = aux + 1;
                cv_success = cv_success + 1;

            catch ME
                last_err_msg = ME.message;
                warning('Model %d, iteration %d, valid set %d failed: %s', N_Model, i, v, ME.message);
            end
        end

        if cv_success > 0
            str_it = strcat('Iteration_', num2str(i));
            RESULTS.(str_it) = Results;
            n_success = n_success + 1;
        end
    end

    if n_success == 0
        error('All CV runs failed for model %d. Last error: %s', N_Model, last_err_msg);
    end

    All_Result.(str_m) = RESULTS;
    save('5_perc_Models_Z_LAB.mat', 'All_Result')
end
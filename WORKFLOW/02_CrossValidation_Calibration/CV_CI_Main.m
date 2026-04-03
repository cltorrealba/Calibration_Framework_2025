%--------------------Cross-Validation Optimization Problem------------------%
% Pilot-scale cross-validation with confidence interval calculation
% Uses CrossValidationCalibrationZ_Alter_Data (5% noise) + MEIGO/ESS
%
% Requires: DataLoad.m, ../01_HIPPO_Identification/it.mat,
%           CrossValidationCalibrationZ_Alter_Data.m,
%           ess_kernel (MEIGO)

%% Data Loading

global Measure_Inds time_daps FDA_add_idxs Kinetic_Matrixes x0s int_times exp_temps
n = 0;
for j = 2
    for i = 1:4
        if j == 1 && i == 1
            continue
        end

        %Experiment Selection
        exper_id    =   i;
        scale_id    =   j;
        ifplot      =   false;

        %Operational/Kinetic information structures construction
        [Kinetic_Matrix,Time_Temp_Pairs,Measure_Ind,FDA_Rho_Time_Pair] = DataLoad(scale_id,exper_id,ifplot);

        Measure_Inds{i,j} = Measure_Ind;

        % Operational Parameter Definition

        %Intermidiate DAP addition related information
        rho_dap      = FDA_Rho_Time_Pair(1);      % Density at which DAP was added (kg/m3)
        time_dap     = FDA_Rho_Time_Pair(2);       % Experimental time where DAP was added (h)
        dap          = 20;                         % DAP dosis g/hL

        time_daps{i,j} = time_dap;

        %Residual YAN corrections
        FDA_add_idx  = find(ismember(Time_Temp_Pairs(Measure_Ind),time_dap));
        if isempty(FDA_add_idx)
            measure_times = Time_Temp_Pairs(Measure_Ind);
            [~,FDA_add_idx] = min(abs(measure_times - time_dap));
            warning('FDA_add_idx not exact for PIL exp %d; using nearest index %d.', exper_id, FDA_add_idx);
        end
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
        x0       = [X0, N0, G0, F0, E0];

        x0s{i,j}   = x0;

        %Temperature and integration time information
        int_time = Time_Temp_Pairs(:,1);       %Experimental times for integration (h)
        exp_temp = Time_Temp_Pairs(:,2);       %Experimental temperatures for integration (C)

        %Eliminate repeated times
        [int_time,IA,~] = unique(int_time);
        exp_temp        = exp_temp(IA);

        int_times{i,j}    = int_time;
        exp_temps{i,j}    = exp_temp;

        n   =   n + size(Kinetic_Matrix,1);
    end
end

%% Select experiments for validation

Validation_Scale    = 2;
Scale_Experiments   = 6;
Combinations        = cell(1,Scale_Experiments-2);

for i = 1:Scale_Experiments-2
    Combinations{i} = nchoosek([1 2 3 4],i);
end

%% MEIGO + HIPPO Results

% Bounds and initial guess definition
hippo_dir = fullfile('..','01_HIPPO_Identification');
load(fullfile(hippo_dir,'it.mat'),'it')
sel_file = fullfile('..','03_Model_Selection_MCDM','Selected_Model_ID.txt');
if isfile(sel_file)
    N_Model = load(sel_file);
    N_Model = N_Model(1);
else
    N_Model = 1860;  % Fallback when MCDM output is not available yet.
end
[kfixed, free_idx, x0_free] = build_cv_seed_from_it(it, N_Model);
scale_id = 2;

%Initial Guess definition (free-parameter space)
kL      = max(1e-8, x0_free*0.5);
kU      = max(kL*1.05, x0_free*2.0);

%Meigo stuff
problem.f = 'CrossValidationCalibrationZ_Alter_Data';

%Decide the parameters to be estimated depending on kfixed:
m = length(kfixed);
j = 1;
for i = 1:numel(free_idx)
        lb = min(kL(i),kU(i));
        ub = max(kL(i),kU(i));
        x0p = x0_free(i);
        if ~isfinite(x0p) || x0p <= 0
            x0p = max(abs(x0p),1e-6);
        end
        x0p = min(max(x0p,lb),ub);
        problem.x_L(j) = lb;
        problem.x_0(j) = x0p;
        problem.x_U(j) = ub;
        j = j+1;
end

%SSm options:
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

%% Run optimization problem
load('ids.mat')

RESULTS = struct();
n_success = 0;
last_err_msg = '';

for i = 1:100

    disp('N of iteration:')
    disp(i)
    try

        Results         = ess_kernel(problem,opts_SSm,Combinations,Scale_Experiments,scale_id,kfixed);
        X(i,:)          = Results.xbest;
        F(i)            = Results.fbest;
        str             = strcat('Iteration_',num2str(i));
        disp(strcat(str,' Ready!')); pause(1)
        RESULTS.(str)   = Results;
        n_success       = n_success + 1;

    catch ME
        last_err_msg = ME.message;
        warning('CV_CI model %d, iteration %d failed in ess_kernel: %s', N_Model, i, ME.message);

    end
end

if n_success == 0
    error('All ess_kernel runs failed for CV_CI model %d. Last error: %s', N_Model, last_err_msg);
end

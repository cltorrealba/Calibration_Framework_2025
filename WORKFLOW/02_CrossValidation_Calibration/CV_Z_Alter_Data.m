%------------------------Cross-Validation problem-----------------%
% Cross-validation objective function with external perturbed data input.
% Compatible with:
%   ess_kernel(problem, opts_SSm, Calib_set, data, scale_id, kfixed)
%
% Inputs:
%   p         : free-parameter vector
%   Calib_set : vector of calibration experiment indices
%   data      : cell array with perturbed experimental datasets
%   scale_id  : 1 = LAB, 2 = PIL
%   kfixed    : full fixed/free parameter mask used by the model

function Total_Error = CV_Z_Alter_Data(p,Calib_set,data,scale_id,kfixed)

global Measure_Inds time_daps FDA_add_idxs Kinetic_Matrixes x0s int_times exp_temps

error = nan(max(Calib_set),1);

for i = Calib_set
    try
        % Experimental dataset for this calibration experiment
        This_it_KM = data{i,1};

        if isempty(This_it_KM)
            error(i) = 1e9;
            continue
        end

        % Integration times split at DAP addition
        t_all = int_times{i,scale_id};
        t1 = t_all(t_all <  time_daps{i,scale_id});
        t2 = t_all(t_all >= time_daps{i,scale_id});

        % Integration options
        options = odeset('RelTol',1e-3,'AbsTol',1e-3);

        % ---------- Pre DAP ----------
        T1 = [];
        X1 = [];

        if numel(t1) >= 2
            [T1,X1] = ode15s(@Zenteno_Model_2020_PEVth9, ...
                             t1, ...
                             x0s{i,scale_id}, ...
                             options, ...
                             p, ...
                             int_times{i,scale_id}, ...
                             exp_temps{i,scale_id}, ...
                             kfixed);
        elseif numel(t1) == 1
            T1 = t1(:);
            X1 = x0s{i,scale_id};
        end

        % ---------- DAP state update ----------
        idx_dap = FDA_add_idxs{i,scale_id};
        if isempty(idx_dap) || idx_dap < 1 || idx_dap > size(This_it_KM,1)
            error(i) = 1e9;
            continue
        end

        if isempty(X1)
            x02 = x0s{i,scale_id};
        else
            x02 = X1(end,:);
        end

        x02(2) = max(This_it_KM(idx_dap,4),0)/1000;

        % ---------- Post DAP ----------
        T2 = [];
        X2 = [];

        if numel(t2) >= 2
            [T2,X2] = ode15s(@Zenteno_Model_2020_PEVth9, ...
                             t2, ...
                             x02, ...
                             options, ...
                             p, ...
                             int_times{i,scale_id}, ...
                             exp_temps{i,scale_id}, ...
                             kfixed);
        elseif numel(t2) == 1
            T2 = t2(:);
            X2 = x02;
        end

        if isempty(X1) && isempty(X2)
            error(i) = 1e9;
            continue
        end

        % Consolidate trajectories
        T = [T1; T2];
        X = [X1; X2];

        % Keep only target experimental integration times
        X = X(ismember(T, int_times{i,scale_id}), :);

        total_idx = (1:size(X,1))';
        X_sim = X(ismember(total_idx, Measure_Inds{i,scale_id}), :);

        % Validate dimensions against experimental matrix
        if size(X_sim,1) ~= size(Kinetic_Matrixes{i,scale_id},1)
            error(i) = 1e9;
            continue
        end

        % Data definition
        N_data = max(This_it_KM(:,4),0);
        N_sim  = X_sim(:,2) * 1000;

        G_data = This_it_KM(:,1);
        G_sim  = X_sim(:,3);

        F_data = This_it_KM(:,2);
        F_sim  = X_sim(:,4);

        % Robust denominators
        denN = max(max(N_data), eps);
        denG = max(max(G_data), eps);
        denF = max(max(F_data), eps);

        % Weighted normalized SSE
        err_i = ...
            sum(((N_data - N_sim)./denN).^2) / length(N_data) + ...
            sum(((G_data - G_sim)./denG).^2) / length(G_data) + ...
            sum(((F_data - F_sim)./denF).^2) / length(F_data);

        if ~isfinite(err_i)
            error(i) = 1e9;
        else
            error(i) = err_i;
        end

    catch
        error(i) = 1e9;
    end
end

Total_Error = sum(error,'omitnan');

if ~isfinite(Total_Error)
    Total_Error = 1e9;
end

end
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Validation simulations on PIL validation experiments using selected models
% Includes Monte Carlo prediction band + mean simulation for each model
% - Legend uses only line handles
% - Shaded bands excluded from legend
% - Uncertainty bands shown as 5th-95th percentiles
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

clc
clear
close all

if ~exist('it','var')
    load(fullfile('..','01_HIPPO_Identification','it.mat'),'it');
end

%% User settings
scale_id = 2;
valid_experiments = [5 6];
ic_file = 'Zenteno_IC_PIL_5PERC.xlsx';
mc_iterations = 200;

%% Load selected model IDs and force baseline model 1
sel_file = fullfile('..','03_Model_Selection_MCDM','Selected_Model_ID.txt');
if isfile(sel_file)
    selected_models = load(sel_file);
    selected_models = selected_models(:)';
else
    warning('Selected_Model_ID.txt not found. Using only baseline model 1.');
    selected_models = 1;
end

model_ids = unique([1, selected_models], 'stable');

%% Load HIPPO structure info
hippo_dir = fullfile('..','01_HIPPO_Identification');
load(fullfile(hippo_dir,'it.mat'),'it')

%% Colors
n_models = numel(model_ids);
clr = lines(n_models);
clr(1,:) = [0 0 0];   % baseline model 1 in black

%% Loop over validation experiments
for ee = 1:numel(valid_experiments)

    exper_id = valid_experiments(ee);
    ifplot = false;

    fprintf('\n==============================\n');
    fprintf('Processing validation experiment %d\n', exper_id);
    fprintf('==============================\n');

    %% Experimental data loading
    try
        [Kinetic_Matrix,Time_Temp_Pairs,Measure_Ind,FDA_Rho_Time_Pair] = DataLoad(scale_id,exper_id,ifplot);
    catch ME
        warning('DataLoad failed for PIL experiment %d: %s', exper_id, ME.message);
        continue
    end

    if isempty(Kinetic_Matrix) || isempty(Time_Temp_Pairs)
        warning('Empty data for PIL experiment %d. Skipping.', exper_id);
        continue
    end

    %% Operational parameter definition
    global FDA_add_idx
    time_dap = FDA_Rho_Time_Pair(2);

    FDA_add_idx = find(ismember(Time_Temp_Pairs(Measure_Ind),time_dap));
    if isempty(FDA_add_idx)
        measure_times = Time_Temp_Pairs(Measure_Ind);
        [~,FDA_add_idx] = min(abs(measure_times - time_dap));
        warning('FDA_add_idx not exact for PIL exp %d; using nearest index %d.', exper_id, FDA_add_idx);
    end

    % Residual YAN correction
    Stuck_YANs = load('Stuck_YANs.txt');
    Stuck_YAN = Stuck_YANs(exper_id,scale_id);
    Kinetic_Matrix(:,4) = Kinetic_Matrix(:,4) - ones(size(Kinetic_Matrix(:,4))).*Stuck_YAN;
    Kinetic_Matrix((Kinetic_Matrix(:,4)<0),4) = 0;

    %% Initial conditions
    X0 = 0.2;
    N0 = Kinetic_Matrix(1,4)/1000;
    G0 = Kinetic_Matrix(1,1);
    F0 = Kinetic_Matrix(1,2);
    E0 = 0;
    x0 = [X0, N0, G0, F0, E0];

    %% Temperature and integration time information
    int_time = Time_Temp_Pairs(:,1);
    exp_temp = Time_Temp_Pairs(:,2);

    [int_time,IA,~] = unique(int_time);
    exp_temp = exp_temp(IA);

    %% Figure for this validation experiment
    fig = figure('Name',sprintf('PIL validation exp %d', exper_id), ...
                 'Color','w', ...
                 'Visible','on');

    plotted_labels = {};
    hLines = gobjects(n_models,6);
    valid_line_mask = false(n_models,1);

    for mm = 1:n_models

        Model_N = model_ids(mm);
        sheet = sprintf('Z_%d', Model_N);

        fprintf('  Trying model %d...\n', Model_N);

        % Load model structure
        try
            kfixed = it.codes{Model_N,2}.kfixed;
        catch
            warning('Could not access kfixed for model %d. Skipping.', Model_N);
            continue
        end

        % Read calibrated parameters from workbook
        try
            Ttab = readtable(ic_file,'Sheet',sheet);
        catch
            warning('Sheet %s not found in %s. Skipping model %d.', sheet, ic_file, Model_N);
            continue
        end

        if isempty(Ttab)
            warning('Sheet %s is empty. Skipping model %d.', sheet, Model_N);
            continue
        end

        Array = table2array(Ttab);
        if size(Array,1) < 4 || size(Array,2) < 4
            warning('Sheet %s has unexpected dimensions. Skipping model %d.', sheet, Model_N);
            continue
        end

        p_optim = Array(end-3,2:end-2);
        IC_95   = Array(end-1:end,2:end-2);

        if any(isnan(p_optim))
            warning('NaN parameters found for model %d. Skipping.', Model_N);
            continue
        end

        %% Monte Carlo simulation
        nT = numel(int_time);
        Bioms = nan(nT, mc_iterations);
        Nitrs = nan(nT, mc_iterations);
        Glucs = nan(nT, mc_iterations);
        Frucs = nan(nT, mc_iterations);
        Etans = nan(nT, mc_iterations);
        Sugas = nan(nT, mc_iterations);

        valid_count = 0;
        Tsim_ref = [];

        for ii = 1:mc_iterations
            try
                if ii == 1
                    p_use = p_optim;
                else
                    p_use = IC_95(2,:) + (IC_95(1,:) - IC_95(2,:)).*rand(size(IC_95(2,:)));
                    p_use(p_use < 0) = p_optim(p_use < 0);
                end

                [Tsim,Xf] = ReSimulate_Zenteno_Optimal(p_use,x0,time_dap,int_time,exp_temp,Kinetic_Matrix,kfixed);

                if isempty(Xf) || any(isnan(Xf(:))) || size(Xf,1) ~= nT || size(Xf,2) < 5
                    continue
                end

                valid_count = valid_count + 1;
                Tsim_ref = Tsim;

                Bioms(:,valid_count) = Xf(:,1);
                Nitrs(:,valid_count) = Xf(:,2);
                Glucs(:,valid_count) = Xf(:,3);
                Frucs(:,valid_count) = Xf(:,4);
                Etans(:,valid_count) = Xf(:,5);
                Sugas(:,valid_count) = Xf(:,3) + Xf(:,4);

            catch
                continue
            end
        end

        if valid_count == 0
            warning('No valid Monte Carlo simulations for model %d on validation exp %d.', Model_N, exper_id);
            continue
        end

        % Trim to valid simulations only
        Bioms = Bioms(:,1:valid_count);
        Nitrs = Nitrs(:,1:valid_count);
        Glucs = Glucs(:,1:valid_count);
        Frucs = Frucs(:,1:valid_count);
        Etans = Etans(:,1:valid_count);
        Sugas = Sugas(:,1:valid_count);

        % Mean trajectories
        Biom_mean = mean(Bioms,2,'omitnan');
        Nitr_mean = mean(Nitrs,2,'omitnan');
        Gluc_mean = mean(Glucs,2,'omitnan');
        Fruc_mean = mean(Frucs,2,'omitnan');
        Etan_mean = mean(Etans,2,'omitnan');
        Suga_mean = mean(Sugas,2,'omitnan');

        % Percentile bands
        Biom_lo = prctile(Bioms,5,2);
        Biom_hi = prctile(Bioms,95,2);

        Nitr_lo = prctile(Nitrs,5,2);
        Nitr_hi = prctile(Nitrs,95,2);

        Gluc_lo = prctile(Glucs,5,2);
        Gluc_hi = prctile(Glucs,95,2);

        Fruc_lo = prctile(Frucs,5,2);
        Fruc_hi = prctile(Frucs,95,2);

        Etan_lo = prctile(Etans,5,2);
        Etan_hi = prctile(Etans,95,2);

        Suga_lo = prctile(Sugas,5,2);
        Suga_hi = prctile(Sugas,95,2);

        plotted_labels{end+1} = sprintf('ZM-%d', Model_N);
        valid_line_mask(mm) = true;

        %% Biomass
        subplot(3,2,1)
        hold on
        plot_shaded_band(Tsim_ref, Biom_lo, Biom_hi, clr(mm,:));
        hLines(mm,1) = plot(Tsim_ref, Biom_mean, 'LineWidth', 1.8, 'Color', clr(mm,:));
        xlabel('Time (h)')
        ylabel('Biomass (g/L)')
        title(sprintf('PIL exp %d - Biomass', exper_id))

        %% YAN
        subplot(3,2,2)
        hold on
        plot_shaded_band(Tsim_ref, Nitr_lo, Nitr_hi, clr(mm,:));
        hLines(mm,2) = plot(Tsim_ref, Nitr_mean, 'LineWidth', 1.8, 'Color', clr(mm,:));
        xlabel('Time (h)')
        ylabel('YAN (g/L)')
        title(sprintf('PIL exp %d - YAN', exper_id))

        %% Glucose
        subplot(3,2,3)
        hold on
        plot_shaded_band(Tsim_ref, Gluc_lo, Gluc_hi, clr(mm,:));
        hLines(mm,3) = plot(Tsim_ref, Gluc_mean, 'LineWidth', 1.8, 'Color', clr(mm,:));
        xlabel('Time (h)')
        ylabel('Glucose (g/L)')
        title(sprintf('PIL exp %d - Glucose', exper_id))

        %% Fructose
        subplot(3,2,4)
        hold on
        plot_shaded_band(Tsim_ref, Fruc_lo, Fruc_hi, clr(mm,:));
        hLines(mm,4) = plot(Tsim_ref, Fruc_mean, 'LineWidth', 1.8, 'Color', clr(mm,:));
        xlabel('Time (h)')
        ylabel('Fructose (g/L)')
        title(sprintf('PIL exp %d - Fructose', exper_id))

        %% Ethanol
        subplot(3,2,5)
        hold on
        plot_shaded_band(Tsim_ref, Etan_lo, Etan_hi, clr(mm,:));
        hLines(mm,5) = plot(Tsim_ref, Etan_mean, 'LineWidth', 1.8, 'Color', clr(mm,:));
        xlabel('Time (h)')
        ylabel('Ethanol (g/L)')
        title(sprintf('PIL exp %d - Ethanol', exper_id))

        %% Total sugar
        subplot(3,2,6)
        hold on
        plot_shaded_band(Tsim_ref, Suga_lo, Suga_hi, clr(mm,:));
        hLines(mm,6) = plot(Tsim_ref, Suga_mean, 'LineWidth', 1.8, 'Color', clr(mm,:));
        xlabel('Time (h)')
        ylabel('Sugar (g/L)')
        title(sprintf('PIL exp %d - Total Sugar', exper_id))
    end

    if isempty(plotted_labels)
        warning('No model could be plotted for validation experiment %d.', exper_id);
        close(fig)
        continue
    end

    %% Valid handles for legends
    valid_handles_1 = hLines(valid_line_mask,1);
    valid_handles_2 = hLines(valid_line_mask,2);
    valid_handles_3 = hLines(valid_line_mask,3);
    valid_handles_4 = hLines(valid_line_mask,4);
    valid_handles_5 = hLines(valid_line_mask,5);
    valid_handles_6 = hLines(valid_line_mask,6);

    %% Add measured data + legends
    subplot(3,2,1)
    legend(valid_handles_1, plotted_labels, 'Location','best')

    subplot(3,2,2)
    hold on
    hMeas2 = plot(int_time(Measure_Ind),Kinetic_Matrix(:,4)./1000,'ko', ...
        'LineWidth',1.2,'MarkerFaceColor','k','MarkerSize',5);
    legend([valid_handles_2; hMeas2], [plotted_labels, {'Measured'}], 'Location','best')

    subplot(3,2,3)
    hold on
    hMeas3 = plot(int_time(Measure_Ind),Kinetic_Matrix(:,1),'ko', ...
        'LineWidth',1.2,'MarkerFaceColor','k','MarkerSize',5);
    legend([valid_handles_3; hMeas3], [plotted_labels, {'Measured'}], 'Location','best')

    subplot(3,2,4)
    hold on
    hMeas4 = plot(int_time(Measure_Ind),Kinetic_Matrix(:,2),'ko', ...
        'LineWidth',1.2,'MarkerFaceColor','k','MarkerSize',5);
    legend([valid_handles_4; hMeas4], [plotted_labels, {'Measured'}], 'Location','best')

    subplot(3,2,5)
    legend(valid_handles_5, plotted_labels, 'Location','best')

    subplot(3,2,6)
    hold on
    hMeas6 = plot(int_time(Measure_Ind),Kinetic_Matrix(:,3),'ko', ...
        'LineWidth',1.2,'MarkerFaceColor','k','MarkerSize',5);
    legend([valid_handles_6; hMeas6], [plotted_labels, {'Measured'}], 'Location','best')

    sgtitle(sprintf('Pilot-scale validation experiment %d', exper_id))
    drawnow
    fprintf('  Figure generated for validation experiment %d.\n', exper_id);
end

%% Local helper
function h = plot_shaded_band(t, ylow, yhigh, c)
    xx = [t(:); flipud(t(:))];
    yy = [ylow(:); flipud(yhigh(:))];
    h = patch(xx, yy, c, ...
        'FaceAlpha', 0.06, ...
        'EdgeColor', 'none', ...
        'HandleVisibility', 'off');
end
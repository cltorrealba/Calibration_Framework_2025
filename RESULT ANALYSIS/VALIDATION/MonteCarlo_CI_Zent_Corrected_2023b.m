%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Main Script for parameter adjustment using only 1 experiment data                                     %
% Ultimo cambio: 18/5/2020                                                                              %
% Modelo Zenteno                                                        Cristobal Torrealba Vasquez     %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% Experimental data loading
clc
%clear
%close all
%Experiment selection 

scale_id    =   1;      % Experiment Scale :   (1) Biorreactor (2) Bin Automatizado (3) Industrial
exper_id    =   5;      % N° of experiments:            5                  5                7       -> Use only 1,2,4,6,7 Industrial scale
ifplot      =   false;  % True if we need to plot the operational data points

%Operational/Kinetic information structures construction using the previous information

[Kinetic_Matrix,Time_Temp_Pairs,Measure_Ind,FDA_Rho_Time_Pair] = DataLoad(scale_id,exper_id,ifplot);

%% Operational Parameter Definition
global dap  FDA_add_idx
 
%Intermidiate DAP addition related information
rho_dap  = FDA_Rho_Time_Pair(1);      % Density at which DAP was added (kg/m3)
time_dap = FDA_Rho_Time_Pair(2);      % Experimental time where DAP was added (h)
dap      = 20;                        % DAP dosis g/hL

%Residual YAN corrections
FDA_add_idx  = find(ismember(Time_Temp_Pairs(Measure_Ind),time_dap));
Stuck_YANs = load('Stuck_YANs.txt'); Stuck_YAN = Stuck_YANs(exper_id,scale_id);
Kinetic_Matrix(:,4) = Kinetic_Matrix(:,4) - ones(size(Kinetic_Matrix(:,4))).*Stuck_YAN;
Kinetic_Matrix((Kinetic_Matrix(:,4)<0),4) = 0;    
    
%Initial conditions information
X0       = 0.2;                         %Yeast dosis   (g/L)
N0       = Kinetic_Matrix(1,4)/1000;    %Initial YAN   (g/L)
G0       = Kinetic_Matrix(1,1);         %Initial Glu   (g/L)
F0       = Kinetic_Matrix(1,2);         %Initial Fru   (g/L)
E0       = 0;                           %Initial Eth   (g/L)
%CO20     = 0;                           %Initial CO2   (g/L)
%T0       = Time_Temp_Pairs(1,2)+273.15; %Initial Must T (K)
x0       = [X0, N0, G0, F0, E0];

%Temperature and integration time information
int_time = Time_Temp_Pairs(:,1);      %Experimental times for integration (h)
exp_temp = Time_Temp_Pairs(:,2);      %Experimental temperatures for integration (C°)

%% Model Structure Selection

%Selected Model Structure Data
load('it_2023.mat')

Model_N = 1860; %1 1750, 1860, 1966, 2245, 2247, 2264, 2305, 2324
kfixed  = it.codes{Model_N,2}.kfixed; 

%% Optimal parameter settings and confidence Intervals 

%Cal
sheet               = strcat('Z_',num2str(Model_N));

if scale_id == 1
    T                   = readtable('Zenteno_IC_LAB_5PERC_2023b_WSComplete.xlsx','sheet',sheet); 
elseif scale_id == 2
    T                   = readtable('Zenteno_IC_PIL_5PERC_2023b.xlsx','sheet',sheet);
end

Array               = table2array(T);
p_optim             = Array(end-3,2:end-2);
IC_95               = Array(end-1:end,2:end-2);

%% MonteCarlo con CI
iterations  = 200;

Bioms = zeros(size(int_time,1),iterations);
Nitrs = zeros(size(int_time,1),iterations);
Glucs = zeros(size(int_time,1),iterations);
Frucs = zeros(size(int_time,1),iterations);
Etans = zeros(size(int_time,1),iterations);
Sugas = zeros(size(int_time,1),iterations);
contador = 1;

for i=1:iterations
    
    disp(i)
    it_params = IC_95(2,:)+(IC_95(1,:)-IC_95(2,:)).*rand(size(IC_95(2,:)));
    it_params(it_params<0) = p_optim(it_params<0);
    
    % Re-simulation using optimal parameters
    if i == 1
        [~,Xf] = ReSimulate_Zenteno_Optimal(p_optim,x0,time_dap,int_time,exp_temp,Kinetic_Matrix,kfixed);
    else
        [~,Xf] = ReSimulate_Zenteno_Optimal(it_params,x0,time_dap,int_time,exp_temp,Kinetic_Matrix,kfixed);
    end
    
    if  find(isnan(Xf))
        continue
    else
        Bioms(:,contador) = Xf(:,1);
        Nitrs(:,contador) = Xf(:,2);
        Glucs(:,contador) = Xf(:,3);
        Frucs(:,contador) = Xf(:,4);
        Etans(:,contador) = Xf(:,5);
        Sugas(:,contador) = Xf(:,3)+Xf(:,4);
        contador          = contador+1;
    end
end
%% Results Plotting

% Re-simulation using optimal parameters
[T,Xf] = ReSimulate_Zenteno_Optimal(p_optim,x0,time_dap,int_time,exp_temp,Kinetic_Matrix,kfixed);

%Color          %1 1750, 1860, 1966, 2245, 2247, 2264, 2305, 2324
%                k  r     b      g     y    c      m  "#D95319"   "#A2142F"
color = 'r';

% Biomass related plots
subplot(3,2,1)
shadedplot(T, min(Bioms,[],2)', max(Bioms,[],2)','none',color)
hold on
plot(T,Xf(:,1),'LineWidth',1.5,'Color',color)
legend('95% CI Prediction Interval','Simulated Data','Location','best')
xlabel('Time (h)')
ylabel('Biomass (g/L)')

% Nitrogen related plots
subplot(3,2,2)
shadedplot(T, min(Nitrs,[],2)', max(Nitrs,[],2)','none',color)
hold on
plot(T,Xf(:,2),'LineWidth',1.5,'Color',color)
plot(int_time(Measure_Ind),Kinetic_Matrix(:,4)./1000,'ko','LineWidth',2,'MarkerFaceColor','r','MarkerSize',6)
legend('95% CI Prediction Interval','Simulated Data','Measured Data','Location','best')
xlabel('Time (h)')
ylabel('YAN (g/L)')

% Glucose related plots
subplot(3,2,3)
shadedplot(T, min(Glucs,[],2)', max(Glucs,[],2)','none',color)
hold on
plot(T,Xf(:,3),'LineWidth',1.5,'Color',color)
plot(int_time(Measure_Ind),Kinetic_Matrix(:,1),'ko','LineWidth',1.5,'MarkerFaceColor','r','MarkerSize',6)
legend('95% CI Prediction Interval','Simulated Data','Measured Data','Location','best')
xlabel('Time (h)')
ylabel('Glucose (g/L)')

% Fructose related plots
subplot(3,2,4)
shadedplot(T, min(Frucs,[],2)', max(Frucs,[],2)','none',color)
hold on
plot(T,Xf(:,4),'LineWidth',1.5,'Color',color)
plot(int_time(Measure_Ind),Kinetic_Matrix(:,2),'ko','LineWidth',1.5,'MarkerFaceColor','r','MarkerSize',6)
legend('95% CI Prediction Interval','Simulated Data','Measured Data','Location','best')
xlabel('Time (h)')
ylabel('Fructose (g/L)')

% Ethanol related plots
subplot(3,2,5)
shadedplot(T, min(Etans,[],2)', max(Etans,[],2)','none',color)
hold on
plot(T,Xf(:,5),'LineWidth',1.5,'Color',color)
legend('95% CI Prediction Interval','Simulated Data','Location','best')
xlabel('Time (h)')
ylabel('Ethanol (g/L)')

% Total Sugar related plots
subplot(3,2,6)
shadedplot(T, min(Sugas,[],2)', max(Sugas,[],2)','none',color)
hold on
plot(T,(Xf(:,3)+Xf(:,4)),'LineWidth',1.5,'Color',color)
plot(int_time(Measure_Ind),Kinetic_Matrix(:,3),'ko','LineWidth',1.5,'MarkerFaceColor','r','MarkerSize',6)
legend('95% CI Prediction Interval','Simulated Data','Measured Data','Location','best')
xlabel('Time (h)')
ylabel('Sugar (g/L)')


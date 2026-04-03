%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% load_problem
% Define all the needed data and options to solve the problem
%
% OUTPUTS:
% kL            Row vector with the parameter lower bounds for SSm.
% k0            Row vector with the parameter initial values for SSm.
% kU            Row vector with the parameter upper bounds for SSm.
% opts_SSm      Options for the SSm procedure
% texp          Experimental times for the integration.
% ydata         Experimental data. Be consistent with obj_var.
% x0            Initial state variable vaues for the integration.
% solver_ODE    Solver for the dynamic model integration
% opts_ODE      Options for the dynamic model integration (odeset)
% T             Threshold for correlation values.
%
% Benjamín J. Sánchez: 2014-07-17
% Javiera Pérez: 17-05-2018
% Cristobal Torrealba: 30-06-2020
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function [kL,k0,kU,opts_SSm,texp,ydata,x0,solver_ODE,opts_ODE,T,U,int_time,time_dap,exp_temp,Kinetic_Matrix,FDA_add_idx,Measure_Ind] = load_problem_zent

%SSm options:
opts_SSm.maxeval      = 100;
opts_SSm.local.n2     = 1;
opts_SSm.local.n1     = 2;
opts_SSm.maxtime      = 30;
opts_SSm.strategy     = 3;
opts_SSm.local.solver = 'fmincon';
opts_SSm.local.finish = 'fmincon';
opts_SSm.combination  = 1;  
opts_SSm.local.tol    = 1;  
opts_SSm.local.iterprint    = 1;  
opts_SSm.iterprint    = 1;  
%% Experimental Data:

%Experimental name
scale_id    = 1;
exper_id    = 2;
ifplot      = false;

%Data load
[Kinetic_Matrix,Time_Temp_Pairs,Measure_Ind,FDA_Rho_Time_Pair] = DataLoad(scale_id,exper_id,ifplot);

%Intermidiate DAP addition related information
time_dap = FDA_Rho_Time_Pair(2);      % Experimental time where DAP was added (h)

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
CO20     = 0;                           %Initial CO2   (g/L)



%Lower, initial and upper values for each parameter in SSm:%

k0 = [0.18                      %mu0
      0.225                     %betaG0
      0.225                     %betaF0
      0.01                      %Kn0
      7.5                       %Kg0
      7.5                       %Kf0
      Kinetic_Matrix(1,3)/4     %Kig0
      40                        %Kie0
%       0.00044                   %Kd0
      19.69                     %Yxn
      1.60                      %Yxg
      1.60                      %Yxf
      0.49                      %Yeg
      0.49]';                   %Yef

kU = [0.18                      %mu0
      0.225                     %betaG0
      0.225                     %betaF0
      0.01                      %Kn0
      7.5                       %Kg0
      7.5                       %Kf0
      Kinetic_Matrix(1,3)/4     %Kig0
      40                        %Kie0
%       0.00044                   %Kd0
      19.69                     %Yxn
      1.60                      %Yxg
      1.60                      %Yxf
      0.49                      %Yeg
      0.49]*1.2;                %Yef

kL = [0.18                      %mu0
      0.225                     %betaG0
      0.225                     %betaF0
      0.01                      %Kn0
      7.5                       %Kg0
      7.5                       %Kf0
      Kinetic_Matrix(1,3)/4     %Kig0
      40                        %Kie0
%       0.00044                   %Kd0
      19.69                     %Yxn
      1.60                      %Yxg
      1.60                      %Yxf
      0.49                      %Yeg
      0.49]*0.8;                %Yef

    



%Temperature and integration time information
int_time = Time_Temp_Pairs(:,1);      %Experimental times for integration (h)
exp_temp = Time_Temp_Pairs(:,2);      %Experimental temperatures for integration (C°)

%% Hippo stuff
data  = [int_time(Measure_Ind) Kinetic_Matrix(:,4)./1000 Kinetic_Matrix(:,1) Kinetic_Matrix(:,2)]; 

[~,n] = size(data); 
texp  = data(:,1)';
ydata = data(:,2:n);

%Initial conditions for integration:
x0       = [X0, N0, G0, F0, E0];

%ODE options:
solver_ODE = 'ode45';
opts_ODE   = odeset('RelTol',1e-3,'AbsTol',1e-3);

%Threshold for correlations (any couple of parameters with a correlation
%higher than this value will be fixed):
T = 0.90;

%Threshold for iterations (criterion III):
U = 1.2; %Original 1.5

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
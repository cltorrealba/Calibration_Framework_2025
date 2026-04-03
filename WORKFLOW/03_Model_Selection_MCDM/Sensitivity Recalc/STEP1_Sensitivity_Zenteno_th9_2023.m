% prepare computation for Coleman model

function thetaNom = STEP1_Sensitivity_Zenteno_th9_2023(kfixed,p_optim)
global Time_Temp_Pairs ModelName nth nx NExp Tf Nt Kinetic_Matrix int_time exp_temp FDA_add_idx time_dap x0

%% Initialization and Model data definition
tic
ModelName='Zenteno';

%Data load
scale_id = 1; exper_id = 2; ifplot= false;
[Kinetic_Matrix,Time_Temp_Pairs,Measure_Ind,FDA_Rho_Time_Pair] = DataLoad(scale_id,exper_id,ifplot);

%Intermidiate DAP addition related information
rho_dap  = FDA_Rho_Time_Pair(1);      % Density at which DAP was added (kg/m3)
time_dap = FDA_Rho_Time_Pair(2);      % Experimental time where DAP was added (h)
dap      = 20;                        % DAP dosis g/hL

%Residual YAN corrections
FDA_add_idx  = find(ismember(Time_Temp_Pairs(Measure_Ind),time_dap));
Kinetic_Matrix(:,4) = Kinetic_Matrix(:,4) - ones(size(Kinetic_Matrix(:,4))).*mean(Kinetic_Matrix(FDA_add_idx+1:end,4));
Kinetic_Matrix((Kinetic_Matrix(:,4)<0),4) = 0;    
 
%Initial conditions information
N0       = Kinetic_Matrix(1,4)/1000;  %Initial YAN   (g/L)
X0       = 0.2;                       %Yeast dosis   (g/L)
E0       = 0;                         %Initial Eth   (g/L)
G0       = Kinetic_Matrix(1,1);       %Initial Glucose (g/L)
F0       = Kinetic_Matrix(1,2);       %Initial Fructose (g/L)

x0       = [X0, N0, G0, F0, E0];

%Temperature and integration time information
int_time = Time_Temp_Pairs(:,1);      %Experimental times for integration (h)
exp_temp = Time_Temp_Pairs(:,2);      %Experimental temperatures for integration (C°)

%% Symbolic variables creation

for i=1:5
    syms(sprintf('x%d',i),'real');
end
% th=sym(zeros(nth,1)); % system parameters
for i=1:14
    syms(sprintf('th%d',i),'real');
end


syms t real% time
syms U1 U2 real % input

statesSym   = [x1 x2 x3 x4 x5]';
%thetaSym0   = [th1 th2 th3 th4 th5 th6 th7 th8 th9 th10 th11 th12 th13 th14]';
thetaSym0   = [th1 th2 th3 th4 th5 th6 th7 th8 th10 th11 th12 th13 th14]';

thetaSym  = [];

for i = 1:13
    if isnan(kfixed(i))
        thetaSym = [thetaSym; thetaSym0(i)];
    end
end
      
    
        
nx=length(statesSym);
thIC=sym(x0); % initial conditions

x0Sym=thIC';
%outputsSym=statesSym; % possible sensors for data collection

amountpar = length(thetaSym);
amountstate = length(x0);

%thetaSym=[thetaSym];

% nominal value parameters

% thetaNom = [   -3.92      7.82e-2               ...     %mu_max_0 mu_max_1 
%                -1.8476                          ...     %Kn_0
%                -9.81     -1.08e-1      4.78e-3  ...     %Kd_0 Kd_1 Kd_2
%                 3.50     -3.6362*N0             ...     %Yxn_0 Yxn_1
%                -0.4082                          ...     %Yes0
%                -2.30      7.71e-2               ...     %b_max_0 b_max_1
%                 4.2318]';                               %Ks_0

thetaNom0 = p_optim;

thetaNom = [];

for i = 1:13
    if isnan(kfixed(i))
        thetaNom = [thetaNom thetaNom0(i)];
    end
end

         

nth=length(thetaSym);

Tf=Time_Temp_Pairs(end,1); Nt=length(Time_Temp_Pairs(:,1)); % final time, time grid, number of points

NExp=1; % number of experiments

% MODEL DEFINITION
% state equations
%T = 26;

Xdot =  [
             th1*exp(59453*(U1-300)/(300*8.314*U1))*(x2/(x2+th4*exp(46055*(U1-293.15)/(293.15*8.314*U1))))*x1-U2*0.00044*exp((0.0415*x5)+(130000*(U1-305.65))/(305.65*8.314*U1))*x1;                          
            -th1*exp(59453*(U1-300)/(300*8.314*U1))*(x2/(x2+th4*exp(46055*(U1-293.15)/(293.15*8.314*U1))))*(x1/th10);                              
            -((th1*exp(59453*(U1-300)/(300*8.314*U1))*(x2/(x2+th4*exp(46055*(U1-293.15)/(293.15*8.314*U1))))/th11)+(th2*exp(11000*(U1-296.15)/(296.15*8.314*U1))*(x3/(x3+th5*exp(46055*(U1-293.15)/(293.15*8.314*U1))))*(th8*exp(46055*(U1-293.15)/(293.15*8.314*U1))/(x5+th8*exp(46055*(U1-293.15)/(293.15*8.314*U1))))/th13)+0.01*exp(37681*(U1-293.3)/(293.3*8.314*U1))*(x3/(x3+x4)))*x1;    % Glucose
            -((th1*exp(59453*(U1-300)/(300*8.314*U1))*(x2/(x2+th4*exp(46055*(U1-293.15)/(293.15*8.314*U1))))/th12)+(th3*exp(11000*(U1-296.15)/(296.15*8.314*U1))*(x4/(x4+th6*exp(46055*(U1-293.15)/(293.15*8.314*U1))))*(th7*exp(46055*(U1-293.15)/(293.15*8.314*U1))/(x3+th8*exp(46055*(U1-293.15)/(293.15*8.314*U1))))*(th8*exp(46055*(U1-293.15)/(293.15*8.314*U1))/(x5+th8*exp(46055*(U1-293.15)/(293.15*8.314*U1))))/th14)+0.01*exp(37681*(U1-293.3)/(293.3*8.314*U1))*(x4/(x3+x4)))*x1;    
            (th2*exp(11000*(U1-296.15)/(296.15*8.314*U1))*(x3/(x3+th5*exp(46055*(U1-293.15)/(293.15*8.314*U1))))*(th8*exp(46055*(U1-293.15)/(293.15*8.314*U1))/(x5+th8*exp(46055*(U1-293.15)/(293.15*8.314*U1))))+th3*exp(11000*(U1-296.15)/(296.15*8.314*U1))*(x4/(x4+th6*exp(46055*(U1-293.15)/(293.15*8.314*U1))))*(th7*exp(46055*(U1-293.15)/(293.15*8.314*U1))/(x3+th8*exp(46055*(U1-293.15)/(293.15*8.314*U1))))*(th8*exp(46055*(U1-293.15)/(293.15*8.314*U1))/(x5+th8*exp(46055*(U1-293.15)/(293.15*8.314*U1)))))*x1];                       

params = [1:8 10:14];
for i = 1:13
    if ~isnan(kfixed(i))
        Xdot = subs(Xdot,strcat('th',num2str(params(i))),kfixed(i));
    end
end

% output equations
% Yobs=[PN];
% ny=length(Yobs);

% END MODEL DEFINITION

%% Generate necessary files
dfdxSym=simplify(jacobian(Xdot,statesSym));
dfdthSym=simplify(jacobian(Xdot,thetaSym));

% dhdxSym=simplify(jacobian(Yobs,statesSym));
% dhdthSym=simplify(jacobian(Yobs,thetaSym));
 dx0dthSym=simplify(jacobian(x0Sym,thetaSym));

f = matlabFunction(Xdot,'vars',{t,statesSym,U1,U2,thetaSym},'file',ModelName);
dfdx = matlabFunction(dfdxSym,'vars',{t,statesSym,U1,U2,thetaSym},'file',['dfdx',ModelName]);
dfdth = matlabFunction(dfdthSym,'vars',{t,statesSym,U1,U2,thetaSym},'file',['dfdth',ModelName]);

% h = matlabFunction(Yobs,'vars',{t,statesSym,thetaSym},'file',['Y',ModelName]);
% dhdx = matlabFunction(dhdxSym,'vars',{t,statesSym,thetaSym},'file',['dhdx',ModelName]);
% dhdth = matlabFunction(dhdthSym,'vars',{t,statesSym,thetaSym},'file',['dhdth',ModelName]);

IC = matlabFunction(x0Sym,'vars',{thetaSym},'file',['x0',ModelName]);
dICdth = matlabFunction(dx0dthSym,'vars',{statesSym,thetaSym},'file',['dICdth',ModelName]);


time1=toc



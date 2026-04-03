%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% iteration
% Performs a whole iteration of the procedure: Parameter estimation using
% Scatter Search (SSm) and regression analyisis. Saves all the results in
% an appropiate folder, and decides wich parameters should be fix in the
% next iteration. Returns the parameters to be fixed (ktofix) and the
% iteration results (it_results).
%
% Benjamín J. Sánchez
% Last Update: 2014-07-10
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function [ktofix,results_it] = iteration(kfixed,it_name)

close all

%=================== PROBLEM SPECIFICATIONS ===========================
problem.f = 'obj_func'; %mfile containing the objective function

kL = evalin('base','kL');
k0 = evalin('base','k0');
kU = evalin('base','kU');

%Decide the parameters to be estimated depending on kfixed:
m = length(kfixed);
j = 1;
for i = 1:m
    if isnan(kfixed(i))
        problem.x_L(j) = kL(i);
        problem.x_0(j) = k0(i);
        problem.x_U(j) = kU(i);
        j = j+1;
    end    
end

%Load and modify if required the SSm options
opts = evalin('base','opts_SSm');
if strcmp(it_name,'it_0')
    opts.maxeval      = opts.maxeval*10;
    opts.local.n1     = opts.local.n1*10;
end

%================================ DATA ================================

texp      = evalin('base','texp');
ydata     = evalin('base','ydata');

%============================ OPTIMIZATION ============================

assignin('base','kfixed',kfixed);
% Results=ssm_kernel(problem,opts,texp,ydata);
Results=ess_kernel(problem,opts,texp,ydata);
%============================= RESULTS ================================

k_SSm    = Results.xbest;
CPU_time = Results.cpu_time;

[J_SSm,~,~] = obj_func(k_SSm,texp,ydata);
%========================= REGRESSION ANALYSIS ========================

close all
[AICc,BIC,CI,CC,Mc,~,diff] = reg_analysis(k_SSm);

%========================= SAVE RESULTS ===============================

%Adjust the results to easier integration with Excel:
ktemp  = zeros(m,1);
CItemp = zeros(m,1);
CCtemp = zeros(m,1);
j = 1;
for i = 1:m
    if isnan(kfixed(i))
        ktemp(i,1)  = k_SSm(j);
        CItemp(i,1) = CI(j);
        CCtemp(i,1) = CC(j);
        j = j+1;
    end    
end
k_SSm = ktemp;
CI    = CItemp;
CC    = CCtemp;

%Decision
ktofix = decision(CC,Mc,[]);

%Save iteration results:
results_it.kfixed = kfixed;
results_it.k_SSm  = k_SSm;
results_it.CPU_time = CPU_time;
results_it.J_SSm = J_SSm;
results_it.AICc = AICc;
results_it.BIC = BIC;
results_it.CI = CI;
results_it.CC = CC;
results_it.Mc = Mc;
% results_it.Ms = Ms;
results_it.diff = diff;
results_it.ktofix = ktofix;
results_it.Results = Results;

%Delete unnecesary files:
delete('Sensib*')
delete('ssm_report.mat')
delete('Mc.txt')
delete('GraficoBarra.txt')
set(0,'ShowHiddenHandles','on');delete(get(0,'Children'))

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
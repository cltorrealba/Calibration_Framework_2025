%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% lsq_func
% Integrates the dynamic model and returns the model predictions. To be
% used for lsqcurvefit.
%
% Benjamín J. Sánchez
% Last Update: 2013-06-07
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function ymod = lsq_func(k,~)
global Measure_Ind

%Load experimental data:
ydata = evalin('base','ydata');

%Resolution of ODEs:
[~,xmod] = ReSimulate_Zenteno_HIPPO(k);
xmod     = xmod(Measure_Ind,:);

%Return de normalized measured variables:
[ymod,~] = obj_var(xmod,ydata);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
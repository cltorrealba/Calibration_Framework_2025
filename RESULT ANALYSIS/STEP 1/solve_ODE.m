%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% solve_ODE
% Integrates the dynamic model according to the indicated options.
%
% Benjamín J. Sánchez
% Last Update: 2013-06-07
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function [tmod,xmod] = solve_ODE(k,texp)

x0      = evalin('base','x0');
solver  = evalin('base','solver_ODE');
options = evalin('base','opts_ODE');

% Integration of ODEs:
if strcmp(solver,'ode23')
    [tmod,xmod] = ode23(@model,texp,x0,options,k);
elseif strcmp(solver,'ode45')
    [tmod,xmod] = ode45(@model,texp,x0,options,k);
elseif strcmp(solver,'ode113')
    [tmod,xmod] = ode113(@model,texp,x0,options,k);
elseif strcmp(solver,'ode15s')
    [tmod,xmod] = ode15s(@model,texp,x0,options,k);
elseif strcmp(solver,'ode23s')
    [tmod,xmod] = ode23s(@model,texp,x0,options,k);
elseif strcmp(solver,'ode23t')
    [tmod,xmod] = ode23t(@model,texp,x0,options,k);
elseif strcmp(solver,'ode23tb')
    [tmod,xmod] = ode23tb(@model,texp,x0,options,k);
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
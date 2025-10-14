%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% plotResults
% Plot the achieved parameter calibration (optional).
%
% INPUTS:
% k         Estimated parameters from the last iteration.
% texp      Vector with the experimental times (as loaded by the user).
% ydata     Matrix with the experimental data (as loaded by the user).
%
% Benjamín J. Sánchez
% Last Update: 2014-07-10
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function plotResults(k,texp,ydata)

t0          = texp(1);
tf          = texp(length(texp));
[tmod,xmod] = solve_ODE(k,[t0 tf]);
ymod=xmod;
yexp        = ydata;

figure()
subplot(4,1,1); % Biomass
plot(tmod,ymod(:,1),'-r',texp,yexp(:,1),'*b','LineWidth',1,'MarkerSize',3);
xlabel('Time (h)'); ylabel('Biomass (g/L)');
        
subplot(4,1,2); % Glucose
plot(tmod,ymod(:,2),'-r',texp,yexp(:,2),'*b','LineWidth',1,'MarkerSize',3);
xlabel('Time (h)'); ylabel('Glucose (g/L)');

subplot(4,1,3); % Etanol
plot(tmod,ymod(:,3),'-r',texp,yexp(:,3),'*b','LineWidth',1,'MarkerSize',3);
xlabel('Time (h)'); ylabel('Ethanol (g/L)');

subplot(4,1,4); % b-Carotene
plot(tmod,ymod(:,4),'-r',texp,yexp(:,4),'*b','LineWidth',1,'MarkerSize',3);
xlabel('Time (h)'); ylabel('Betacarotene(mg/L)');

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
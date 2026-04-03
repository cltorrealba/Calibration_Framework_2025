%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% obj_var
% Generates the measured variables, experimental and from the model.
%
% INPUTS:
% xmod      Matrix containing the output from the integration of the
%           dynamic model.
% ydata     Matrix containing the experimental data (as loaded by the
%           user).
% 
% OUTPUTS:
% ymod      Matrix containing the measured variables predicted by the
%           dynamic model.
% yexp      Matrix containing the experimental measured variables.
% 
% NOTE: Perform any normalization or weighting here (to ymod and yexp).
%
% Benjamín J. Sánchez
% Last Update: 2013-06-07
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function [ymod,yexp] = obj_var(xmod,ydata)

%Construction of the measured variables from the model:

ymod=xmod;

%Construction of measured experimental variables:
[N,n] = size(ydata);
yexp  = zeros(N,n);
for i = 1:n
    %Normalization using maximum measure:
    yexp(:,i) = ydata(:,i)./max(ydata(:,i));
    ymod(:,i) = ymod(:,i)./max(ydata(:,i));
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
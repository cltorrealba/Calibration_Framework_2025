function dxdt   = meta(ModelName,t,x,TU,theta,dim)

%This is an auxiliary function for simulation using the provided Zenteno
% model in symbolical format.

%Dont change these
nx  =   dim(1); 
nth =   dim(2);

%Model states
X   = x(1:nx);

%This conditional loop is to correctly use model inputs, where the main
% objective is to indicate if yeast is or not on thermal death.

if ~isempty(TU)
    %First we interpolate operational conditions with current integration
    % time "t"
    U1=interp1(TU(:,1),TU(:,2),t,'nearest');
    %The following equation is the thermal death yeast loss
    % (Zenteno et al., 2010)
    Td = -0.0001*x(5)^3+0.0049*x(5)^2-0.1279*x(5)+315.89;
    %The following conditional communicate the model if yeast death
    % should be accounted
    if U1 >= Td
        U2 = 1;
    else
        U2 = 0;
    end
    
else
    U   = [];
end

%Construction of d(x_theta)/dt from eq. 3 (Stigter & Molenaar, 2015)
% (Dont change unless inputs (Ui) must be modified)
f=eval(['@' ModelName]);
xdot=f(t,X,U1,U2,theta);

dxdth=reshape(x((nx+1):end),nx,nth);

dfdxModel=eval(['@dfdx' ModelName]);
dfdx=dfdxModel(t,X,U1,U2,theta);

dfdthModel=eval(['@dfdth' ModelName]);
dfdth=dfdthModel(t,X,U1,U2,theta);

dxdthdot=dfdx*dxdth+dfdth;

dxdt=[xdot; dxdthdot(:)];
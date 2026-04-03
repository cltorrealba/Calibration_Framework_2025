%start timing step 2
function [Xstate,dxdth,thetaNom] = STEP2_Sensitivity_Zenteno_th9_2023(kfixed,p_optim)
global Time_Temp_Pairs ModelName nth nx NExp Tf Nt T

tic
%Generate Symbolic Jacobian files

thetaNom = STEP1_Sensitivity_Zenteno_th9_2023(kfixed,p_optim);

% Randomly draw new theta's from a uniform distribution
thetaLow=log(0.8*exp(thetaNom)); 
thetaHigh=log(1.2*exp(thetaNom));

THETAReal=zeros(NExp,nth);
for i=1:nth
    THETAReal(:,i)=random('unif',thetaLow(i),thetaHigh(i),NExp,1);
end
% first draw is nominal value
THETAReal(1,:)=thetaNom';

time=linspace(0,Tf,Nt);

dxdth=cell(NExp,1);
Xstate=cell(NExp,1);
dxdthRel=cell(NExp,1);

options=odeset('RelTol',1e-6,'AbsTol',1e-8);

X0Model=eval(['@x0' ModelName]);
dxdth0=eval(['@dICdth',ModelName]);

for k=1:NExp
    theta=THETAReal(k,:)';
   
    x0=X0Model(theta);
    
    dxdthIC=dxdth0(x0,theta);


timeU=linspace(0,Tf,Nt)';
TU=Time_Temp_Pairs;
TU(:,2) = TU(:,2)+273.15;
    %numerical ntegration to obtian model dynamics
    [T,Xst]=ode15s(@(t,x) meta(ModelName,t,x,TU,theta,[nx nth]),time,...
       [x0; dxdthIC(:)],options);
    Xstate{k}=Xst(:,1:nx);
    dxdth{k}=Xst(:,(nx+1):end); 
    fprintf('\n Simulation %s done!',num2str(k))
end

% for k=1:NExp 
%     if size(Xstate{k},1) == 1
%         k_rep{k} = true;
%     else
%         k_rep{k} = false;
%     end
% end




%stop timer
step2 = toc
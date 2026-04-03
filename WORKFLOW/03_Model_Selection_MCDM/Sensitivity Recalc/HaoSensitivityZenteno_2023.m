%Sensitivity Calculation Script
function [S,I] = HaoSensitivityZenteno_2023(Model_N,CV_PARAMS)
global T Kinetic_Matrix int_time exp_temp FDA_add_idx time_dap x0 it

%Model Structure data
kfixed  = it.codes{Model_N,2}.kfixed; estim_param = length(find(isnan(it.codes{Model_N,2}.kfixed)));
p_optim = it.codes{1,2}.k_SSm; p_optim(isnan(kfixed)) = CV_PARAMS;

%Generate sensitivity matrix
nx = 5;
S = zeros(nx,estim_param);
[Xstate,dxdth,thetaNom] = STEP2_Sensitivity_Zenteno_th9_2023(kfixed,p_optim);

for i = 1:nx
    for p = 1:estim_param
        name = strcat('f',num2str(i),'_','p',num2str(p));
        col  = nx*p+(i-1)-4;
        sens.(name) = (thetaNom(p)./max(Xstate{1, 1}(:,i))).*dxdth{1,1}(:,col);  
        f    = fit(T(~isnan(sens.(name))),sens.(name)(~isnan(sens.(name))),'smoothingspline','SmoothingParam',0.01);
        sens.(name) = f(T);
        
        %Plot
%         figure(1)
%         n = (i-1)*estim_param+p;
%         subplot(nx,estim_param,n)
%         plot(T,sens.(name))
        
        %Integral of normalized sensitivity 
        A = sens.(name); t = T(~isnan(A));
        F = griddedInterpolant(t,A(~isnan(A))); fun = @(t) abs(F(t));
        I(i,p) = integral(fun, t(1), t(end));
        
        %Sensitivity Score
        %figure(2)
        if i==1 && p==1
            [~,Xf]  = ReSimulate_Zenteno_Optimal_SENS_2023(thetaNom,x0,time_dap,int_time,exp_temp,Kinetic_Matrix,FDA_add_idx,kfixed);
            %plot(T,Xf(:,2))
            %hold on
        end
        rands      = [0.8 0.9 1.1 1.2];
        for r = 1:length(rands)
            theta_it    = thetaNom;
            theta_it(p) = theta_it(p)*rands(r);
            [~,Xit]     = ReSimulate_Zenteno_Optimal_SENS_2023(theta_it,x0,time_dap,int_time,exp_temp,Kinetic_Matrix,FDA_add_idx,kfixed);
            s(r)        = sum(Xit(:,i)-Xf(:,i))/sum(Xf(:,i))*((theta_it(p)-thetaNom(p))/theta_it(p))^(-1);
            if i == 2
                %plot(T,Xit(:,2))
            end
        end
        S(i,p) = mean(abs(s),'omitnan');        
    end
end

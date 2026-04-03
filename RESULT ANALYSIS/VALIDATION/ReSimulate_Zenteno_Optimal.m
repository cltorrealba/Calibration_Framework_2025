function [T,Xf] = ReSimulate_Zenteno_Optimal(p,x0,time_dap,int_time,exp_temp,Kinetic_Matrix,kfixed)    
global FDA_add_idx

%Error function definition for parameters estimation
t1        = int_time(int_time<time_dap);
t2        = int_time(int_time>=time_dap);

%Pre DAP addition section
[T1,X1]   = ode23s(@Zenteno_Model_2020_PEVth9,t1,x0,[],p,int_time,exp_temp,kfixed);
x02       = X1(end,:);  x02(2) = Kinetic_Matrix(FDA_add_idx,4)/1000; %x02(2) + 50/1000; %

%After DAP addition section
[T2,X2]   = ode23s(@Zenteno_Model_2020_PEVth9,t2,x02,[],p,int_time,exp_temp,kfixed);

%Resulting data consolidation
T         = [T1;T2];
Xf        = [X1;X2];
end
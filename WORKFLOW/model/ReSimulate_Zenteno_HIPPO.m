function [T,Xf] = ReSimulate_Zenteno_HIPPO(k)
% Re-simulates the Zenteno model for HIPPO algorithm.
% Uses global variables set by load_problem_zent.m / iteration.m
%
% Input:  k - full parameter vector (13 elements)
% Output: T - time vector, Xf - simulated states [N, G, F]

global int_time time_dap  Kinetic_Matrix x0 FDA_add_idx

%Pre DAP addition section
t1        = int_time(int_time<time_dap);
t2        = int_time(int_time>=time_dap);

[T1,X1]   = ode15s(@model,t1,x0,[],k);
x02       = X1(end,:);  x02(2) = Kinetic_Matrix(FDA_add_idx,4)./1000;

%After DAP addition section
[T2,X2]   = ode15s(@model,t2,x02,[],k);

%Resulting data consolidation
T         = [T1;T2];
Xf        = [X1;X2];
Xf        = Xf(:,[2 3 4]);
end

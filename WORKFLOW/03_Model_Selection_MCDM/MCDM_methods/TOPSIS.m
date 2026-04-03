function ID = TOPSIS(f,w,max_obj,min_obj)
%% Technique for order of preference by similarity to ideal solution (TOPSIS)
% Autor: Ricardo Luna Hernandez
% Reference: Wang Z. and Rangaiah G.P (2017).
% Application and analysis of Methods for Selecting an Optimal Solution
% from the Pareto-Optimal Front obtained by Multiobjective Optimization.
% Journal: Industrial & Engineering Chemistry Research.
% inputs
% f:       objective matrix (number of solutions [n] x number of objectives [m])
% w:       weigth of objectives (1,m)
% max_obj: column indices of maximization objectives
% min_obj: column indices of minimization objectives
% outputs
% ID:      location of optimal solution selected

f = abs(f);
[n_sol,n_obj]=size(f);  % number of solutions and objectives
F = zeros(n_sol,n_obj); % normalized objective matrix
w = diag(w);            % weight of objectives

%%  step 1. Construct normalized objective matrix
Fw = sqrt(sum(f.^2));
for j=1:n_obj
    F(:,j) = f(:,j)/Fw(j);
end
%%  step 2. Construct weighted normalized objective matrix
v = F*w;
%%  step 3. Determine the ideal Solution A+, and negative ideal solution A-
% ideal Solution A+
A_best  = zeros(1,n_obj);
A_best(1,max_obj)  = max(v(:,max_obj));
A_best(1,min_obj)  = min(v(:,min_obj));
% negative ideal Solution A-
A_worst = zeros(1,n_obj);
A_worst(1,max_obj) = min(v(:,max_obj));
A_worst(1,min_obj) = max(v(:,min_obj));
%% step 4. Calculate the Euclidean distance
S_best  = zeros(n_sol,n_obj);
S_worst = zeros(n_sol,n_obj);
for i  = 1:n_sol
    S_best(i,:)  = (v(i,:)-A_best).^2;
    S_worst(i,:) = (v(i,:)-A_worst).^2;
end
S_best  = sqrt(sum(S_best,2));
S_worst = sqrt(sum(S_worst,2));
%% step 5. Calculate the closeness of each optimal solution
C = S_worst./(S_worst+S_best);
[~,ID] = max(C);
end

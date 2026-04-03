function ID = FUCA(f,w,max_obj,min_obj)
%% Faire Un Choix Adequat (FUCA)
% Autor: Ricardo Luna Hernandez
% Reference: Wang Z. and Rangaiah G.P (2017).
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

%%  step 1. For each objective make a ranking from 1 to n_sol
% maximization objectives: largest value rank 1
for i=1:length(max_obj)
    [fmax(:,i), i_max]=sort(f(:,max_obj(i)), 'descend');
    for j = 1:n_sol
        F(i_max(j),max_obj(i)) = j;
    end
end
% minimization objectives: smallest value rank 1
for i=1:length(min_obj)
    [fmin(:,i), i_min]=sort(f(:,min_obj(i)));
    for j = 1:n_sol
        F(i_min(j),min_obj(i)) = j;
    end
end
%% Step 2. Construct weighted normalized objective matrix
v = sum(F*w,2);
%% Step 3. The solution with the smallest v is the recommended optimal solution
[~,ID] = min(v);
end

function ID = LINMAP(f,w,max_obj,min_obj)
%% Linear Programming Technique for Multidimensional Analysis of Preferences (LINMAP)
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
%% step 1. Construct normalized objective matrix
Fw = sqrt(sum(f.^2));
for j=1:n_obj
    F(:,j) = f(:,j)/Fw(j);
end
%% step 2. Construct weighted normalized objective matrix
v = F*w;
%% step 3. Determine the ideal Solution A+
A_best  = zeros(1,n_obj);
A_best(1,max_obj)  = max(v(:,max_obj));
A_best(1,min_obj)  = min(v(:,min_obj));
%% step 4. Calculate the Euclidean distance to ideal solution
S_best  = zeros(n_sol,n_obj);
for i  = 1:n_sol
    S_best(i,:)  = (v(i,:)-A_best).^2;
end
S_best  = sqrt(sum(S_best,2));
%% step 5. Calculate the minimum distance from ideal solution
[~,ID] = min(S_best);
end

function ID = GRA(f,max_obj,min_obj)
%% Gray Relational Analysis (GRA)
% Autor: Ricardo Luna Hernandez
% Reference: Wang Z. and Rangaiah G.P (2017).
% Journal: Industrial & Engineering Chemistry Research.
% inputs
% f:       objective matrix (number of solutions [n] x number of objectives [m])
% max_obj: column indices of maximization objectives
% min_obj: column indices of minimization objectives
% outputs
% ID:      location of optimal solution selected

f = abs(f);
[n_sol,n_obj]=size(f);  % number of solutions and objectives
F = zeros(n_sol,n_obj); % normalized objective matrix

%% step 1. Normalization of objectives matrix
% maximization criterion
for k = 1:length(max_obj)
    F(:,max_obj(k))=(f(:,max_obj(k))-min(f(:,max_obj(k))))/...
        (max(f(:,max_obj(k)))-min(f(:,max_obj(k))));
end
% minimization criterion
for k = 1:length(min_obj)
    F(:,min_obj(k))=(max(f(:,min_obj(k)))-f(:,min_obj(k)))/...
        (max(f(:,min_obj(k)))-min(f(:,min_obj(k))));
end

F_max = zeros(1,n_obj);
Delta = zeros(n_sol,n_obj);
D_max = zeros(1,n_obj);
D_min = zeros(1,n_obj);
const = zeros(n_sol,n_obj);

for j=1:n_obj
    %% step 2. Find the reference network points
    F_max(1,j)   = max(F(:,j));
    %% step 3. Find the difference
    Delta(:,j)   = abs(F_max(1,j)-F(:,j));
    D_max(1,j)   = max(Delta(:,j));
    D_min(1,j)   = min(Delta(:,j));
    const(:,j)   = (D_min(1,j)+D_max(1,j))./(Delta(:,j)+D_max(1,j));
end
%% step 4. Find the value of GRC of each optimal point
GRC = (1/n_sol)*sum(const,2);
[~,ID] = max(GRC);
end

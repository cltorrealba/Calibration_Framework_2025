function ID = MEW(f,w,max_obj,min_obj)
%% Multiplicative Exponent Weighting (MEW)
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

%% step 1. Construct the normalized objective matrix
% maximization criterion
for k = 1:length(max_obj)
    F(:,max_obj(k))=f(:,max_obj(k))/max(f(:,max_obj(k)));
end
% minimization criterion
for k = 1:length(min_obj)
    F(:,min_obj(k))=min(f(:,min_obj(k)))*(1./f(:,min_obj(k)));
end
%% step 2. Construct the weighted normalized objective matrix
v = ones(n_sol,n_obj);
A = ones(n_sol,1);
for i = 1:n_obj
    v(:,i) = F(:,i).^w(i);
    A(:,1) = v(:,i).*A(:,1);
end
%% step 3. Find the score of each optimal solution (largest value)
[~,ID] = max(A);
end

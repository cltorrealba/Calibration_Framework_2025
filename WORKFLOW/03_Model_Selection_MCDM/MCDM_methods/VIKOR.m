function ID = VIKOR(f,w,gamma,max_obj,min_obj)
%% Viekriterijumsko Kompromisno Rangiranje (VIKOR)
% Autor: Ricardo Luna Hernandez
% Reference: Wang Z. and Rangaiah G.P (2017).
% Journal: Industrial & Engineering Chemistry Research.
% inputs
% f:       objective matrix (number of solutions [n] x number of objectives [m])
% w:       weigth of objectives (1,m)
% gamma:   weigth of the decision making strategy
% max_obj: column indices of maximization objectives
% min_obj: column indices of minimization objectives
% outputs
% ID:      location of optimal solution selected

f = abs(f);
[n_sol,n_obj]=size(f);  % number of solutions and objectives

%% Step 1. Determine the best and worst values
F_best  = zeros(1,n_obj);
F_worst = zeros(1,n_obj);
F_best(1,max_obj)  = max(f(:,max_obj));
F_best(1,min_obj)  = min(f(:,min_obj));
F_worst(1,max_obj) = min(f(:,max_obj));
F_worst(1,min_obj) = max(f(:,min_obj));

%% step 2. Compute weighted fractional distances (S) and maximum (R)
for j = 1:n_obj
    K(:,j)=(F_best(1,j)-f(:,j)/(F_best(1,j)-F_worst(1,j)))*w(j);
end
S = sum(K,2);
R = max(K,[],2);

%% step 3. Compute Q
S_best  = min(S);
S_worst = max(S);
R_best  = min(R);
R_worst = max(R);
Q = gamma*((S-S_best)/(S_worst-S_best))+(1-gamma)*((R-S_best)/(R_worst-R_best));

%% step 4. Sorting Q in decreasing order
[Q,IQ] = sort(Q);
[S,IS] = sort(S);
[R,IR] = sort(R);
% condition 1: acceptable advantage
DQ    = 1/(n_sol-1);
cond1 = Q(2)-Q(1)>= DQ;
% condition 2: acceptable stability in decision making
cond2 = IQ(1) == IS(1) || IQ(1) == IR(1);

%% step 5. Make the selection
if cond1 == true && cond2 == true
    ID = IQ(1);
elseif cond1 == true && cond2 == false
    ID = IQ(1:2);
elseif cond1 == false && cond2 == true
    counter = 2;
    while counter > 1
        if Q(counter)-Q(IQ(1))<DQ
            ID = IQ(1:counter);
            counter = 0;
        else
            counter = counter+1;
        end
    end
elseif cond1 == false && cond2 == false
    counter = 2;
    while counter > 1
        if Q(counter)-Q(IQ(1))<DQ
            ID = IQ(1:counter);
            counter = 0;
        else
            counter = counter+1;
        end
    end
end
end

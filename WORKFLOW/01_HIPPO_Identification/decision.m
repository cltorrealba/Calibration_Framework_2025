%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% decision
% Constrcts ktofix; a vector indicating which parameters should be fixed
% according to sensitivity, identifiability and significance analysis.
% Returns a vector with the parameters to be fixed.
%
% Benjamín J. Sánchez
% Last Update: 2014-07-10
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function ktofix = decision(CC,Mc,~)

kfixed = evalin('base','kfixed');
T      = evalin('base','T');
m      = length(kfixed);
% [~,n]  = size(Ms);
Mc2    = zeros(m,m);
% Ms2    = ones(m,n);

%Construct kf (row vector with 1 if parameter is fixed and 0 otherwise).
kf = zeros(1,m);
for i = 1:m
    if ~isnan(kfixed(i))
        kf(i)=1;
    end    
end

%Modify correlation matrix (Mc) and sensitivity matrix (Ms) to include
%zeros and ones in the fixed parameters position, respectively.
for i = 1:m
    if kf(i) == 0
        for j = 1:m
            if kf(j) == 0
                Mc2(i,j) = Mc(i-sum(kf(1:i)),j-sum(kf(1:j)));
            end
        end
%         Ms2(i,:) = Ms(i-sum(kf(1:i)),:);
    end    
end

%Construct ktofix (1 if analized parameter should be fixed and 0 otherwise).
ktofix = zeros(1,m);
for i = 1:m
%     %Sensitivity:
%     sensitive = false;
%     for j = 1:n
%         if Ms2(i,j) >= 0.01
%             sensitive = true;
%         end
%     end
%     if ~sensitive
%         ktofix(i) = 1;
%     end
    
    %Identifiability:
    for j = 1:m
        if abs(Mc2(i,j)) >= T && i ~= j
            ktofix(i) = 1;
            ktofix(j) = 1;
        end
    end
    
    %Significance:
    if CC(i) >= 2
        ktofix(i) = 1;
    end
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
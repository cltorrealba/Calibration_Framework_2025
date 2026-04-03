function Altered_Data = Norm_Alter_Data(Kinetic_Matrix,Percentage_STD)
% Adds normally distributed noise to kinetic data
% Percentage_STD: fraction of each value used as standard deviation (e.g. 0.05 = 5%)

[rows,cols]  = size(Kinetic_Matrix);
STD          = Percentage_STD*Kinetic_Matrix;
Altered_Data = zeros(rows,cols);

for i = 1:rows
    for j = 1:cols
        Altered_Data(i,j) = normrnd(Kinetic_Matrix(i,j),STD(i,j));
    end
end

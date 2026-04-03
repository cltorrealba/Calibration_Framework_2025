%% load the objective matrix from excel. 
% The excel file contain the examples used in Wang and Rangaiah 2017.
% Example of chemical engineering problem dividing-wall column design.
f_zent = xlsread('Zenteno_Final.xlsx', 'B2:E105');
vote_id = [];

%% define the priority or weigth of each objective
% the sum of weight must be equal 1

%No priority
w  = [0.25,0.25,0.25,0.25; ...   %No priority
      0.70,0.10,0.10,0.10; ...   %Parsimony
      0.10,0.70,0.10,0.10; ...   %Significance
      0.10,0.10,0.70,0.10; ...   %Performance
      0.10,0.10,0.10,0.70];      %Sensitivity
  
MZ = cell(size(w,1),1);
%% define the criterion for each objective
max_obj = [3,4]; % there is not maximization criterion
min_obj = [1,2]; % column indices for each criterion (columns)
gamma    = 0.5; % aditional parameter for VIKOR algorithm.

%% Labels
indxs_z = load('ids_exist.txt');
indxs_z = sort(indxs_z);

for n = 1:length(indxs_z)
    xlabelsz{n} = strcat('ZM-',num2str(indxs_z(n)));
end

%% Use the MCDM algorithms package
for i = 1:size(w,1)
    
    MZ{i} = zeros(size(f_zent,1),7);

    IDZ1 = TOPSIS(f_zent,w(i,:),max_obj,min_obj);
    IDZ2 = LINMAP(f_zent,w(i,:),max_obj,min_obj);
    IDZ3 = VIKOR(f_zent,w(i,:),gamma,max_obj,min_obj);
    IDZ4 = SAW(f_zent,w(i,:),max_obj,min_obj);
    IDZ5 = MEW(f_zent,w(i,:),max_obj,min_obj);
    IDZ6 = GRA(f_zent,max_obj,min_obj); % GRA does not require weigth.
    IDZ7 = FUCA(f_zent,w(i,:),max_obj,min_obj);
    IDZ  = {IDZ1,IDZ2,IDZ3,IDZ4,IDZ5,IDZ6,IDZ7};
    IDZZ = [IDZ1;IDZ2;IDZ3;IDZ4;IDZ5;IDZ6;IDZ7];

    for n = 1:7
        for j = 1:size(f_zent,1)
            if ismember(j,IDZ{n})
                MZ{i}(j,n) = 1;
            else
                MZ{i}(j,n) = 0;
            end
        end
    end

    vote_id = [find(any(MZ{i},2));vote_id];
end

%% plot the results
for i = 1:size(w,1)
    figure(1)
    subplot(5,1,i)
    bar(MZ{i}(unique(vote_id),:),'stacked')
    legend('TOPSIS','LINMAP','VIKOR','SAW','MEW','GRA','FUCA');
    ylim([0 7])
    xlabel('Model Structure ID')
    ylabel('Number of hits')
    set(gca, 'XTick', 1:length(unique(vote_id)))
    set(gca, 'XTickLabel', xlabelsz(unique(vote_id)))
    xtickangle(45)

    switch i
        case 1
            title('Zenteno Model No Priority Scenario')
        case 2
            title('Zenteno Model Parsimony Scenario')
        case 3
            title('Zenteno Model Significance Scenario')
        case 4 
            title('Zenteno Model Performance Scenario')
        case 5 
            title('Zenteno Model Sensitivty Scenario')
    end
end

%% Select top-voted model in each scenario + include model 1
selected_model_ids = [];

for i = 1:size(w,1)
    votes_per_model = sum(MZ{i},2);      % total votes in scenario i
    max_votes = max(votes_per_model);    % highest vote count
    best_rows = find(votes_per_model == max_votes); % handle ties if any
    
    % Convert row indices to actual model IDs
    selected_model_ids = [selected_model_ids; indxs_z(best_rows)];
end

% Include model 1 explicitly
selected_model_ids = [selected_model_ids; 1];

% Remove duplicates and sort
selected_model_ids = unique(selected_model_ids);

% Save to txt
writematrix(selected_model_ids, 'Selected_Model_ID.txt', 'Delimiter', 'tab');

fprintf('Selected model IDs saved to Selected_Model_ID.txt:\n');
disp(selected_model_ids);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% HIPPO
% Heuristic Iterative Procedure for Parameter Optimization
%
% Benjamín J. Sánchez
% Last update: 2014-07-17
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


function it = HIPPO

clear all
close all
clc

global int_time time_dap exp_temp Kinetic_Matrix x0 FDA_add_idx Measure_Ind

set(0,'DefaultFigureVisible','off');

% matlabpool close force local
% matlabpool

%Inicializar SSm
% load SSm
% ssm_startup
% cd ..

%Load problem especifications:
[kL,k0,kU,opts_SSm,texp,ydata,x0,solver_ODE,opts_ODE,T,U,int_time,time_dap,exp_temp,Kinetic_Matrix,FDA_add_idx,Measure_Ind] = load_problem_zent;

%Load to workspace all needed variables for the procedure:
assignin('base','kL',kL);
assignin('base','k0',k0);
assignin('base','kU',kU);
assignin('base','opts_SSm',opts_SSm);
assignin('base','texp',texp);
assignin('base','ydata',ydata);
assignin('base','x0',x0);
assignin('base','solver_ODE',solver_ODE);
assignin('base','opts_ODE',opts_ODE);
assignin('base','T',T);
assignin('base','U',U);

%Initialize procedure with first iteration:
size_k = size(k0);
[ktofix,last_results] = iteration(NaN(size_k),'it_0');

fixed_values  = last_results.k_SSm';
it.last       = zeros(size_k);  %Last iteration performed
it.past       = zeros(size_k);  %All past iterations (including it.last)
it.pending    = [];             %All pending iterations
it.tree       = zeros(1,1);     %Iteration tree
it.codes      = cell(1,2);      %Position in it_tree - iterations - results
it.codes{1,1} = it.last;        %First iteration has code #1
it.codes{1,2} = last_results;   %First iteration results
it.remaining  = true;           %True if an iteration still remains

while it.remaining
    
    %1. Create new iteration vectors from previous one:
    for i = 1:length(ktofix)
        if ktofix(i) == 1
            it.new    = it.last;
            it.new(i) = 1;
            it        = add_it(it,last_results);
        end
    end
    
    %2. Analize a remaining iteration:
    if isempty(it.pending)
        it.remaining = false;   %Finish HIPPO
    else
        %Get a pending iteration:
        it.next = it.pending(1,:);  %OBS: Tree is analized from the top down
        
        %Construct kfixed and folder_name:
        kfixed      = NaN(size_k);
        it_name = 'it';
        for i = 1:length(it.next)
            if it.next(i) == 1
                kfixed(i) = fixed_values(i);
                it_name = [it_name '_' num2str(i)];
            end
        end
        %Perform new iteration:
        [ktofix,last_results] = iteration(kfixed,it_name);
        
        %Update it.last, it.past and it.pending
        it.last = it.next;
        it.past = [it.past;it.next];
        it.pending(1,:) = [];
        
        %Find iteration in it.codes and save the iteration results
        for i = 1:length(it.codes(:,1))
            R    = it.next - it.codes{i,1};
            diff = sum(R.^2);
            if diff ==0
                it.codes{i,2} = last_results;
            end
        end
    end
    save('it.mat','it');
end

set(0,'DefaultFigureVisible','on');
% matlabpool close

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
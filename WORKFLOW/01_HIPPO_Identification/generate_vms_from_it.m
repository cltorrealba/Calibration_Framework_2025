function vms_ids = generate_vms_from_it(it_mat_file, vms_txt_file)
%GENERATE_VMS_FROM_IT Build viable model index list from HIPPO results.
% VMS criterion used for Stage II:
%   1) CCc == 0  (no non-significant parameters, CC >= 2)
%   2) I955 == 0 (no identifiability issues, |Mc_ij| > 0.95 off-diagonal)

if nargin < 1 || isempty(it_mat_file)
    it_mat_file = 'it.mat';
end
if nargin < 2 || isempty(vms_txt_file)
    vms_txt_file = 'VMS_auto.txt';
end

assert(isfile(it_mat_file), 'HIPPO result file not found: %s', it_mat_file);

S = load(it_mat_file, 'it');
assert(isfield(S, 'it'), 'File %s does not contain variable "it".', it_mat_file);
it = S.it;

n_models = size(it.codes, 1);
is_vms = false(n_models, 1);

for i = 1:n_models
    r = it.codes{i,2};
    if ~isstruct(r)
        continue
    end
    if ~isfield(r, 'CC') || ~isfield(r, 'Mc')
        continue
    end

    cc = r.CC(:);
    CCc = sum(cc >= 2);

    Mc = r.Mc;
    if isempty(Mc) || ~ismatrix(Mc)
        continue
    end
    mask_off_diag = ~eye(size(Mc,1));
    has_ident_problem = any(abs(Mc(mask_off_diag)) > 0.95);
    I955 = double(has_ident_problem);

    n_params = sum(isnan(it.codes{i,2}.kfixed));

        % — Flags de parámetros (1=fijado, 0=libre)
    A = cell2mat(it.codes(i,1));
    
    % — Filtrado de modelos no admisibles
    answ = true;
    if A(1)+A(4)==2                                   % Biomasa
        answ = false;
    elseif A(1)+A(4)+A(9)==3                          % Nitrógeno
        answ = false;
    elseif A(1)+A(4)+A(10)+A(2)+A(5)+A(12)+A(8)==7     % Glucosa
        answ = false;
    elseif A(1)+A(4)+A(11)+A(3)+A(6)+A(13)+A(7)+A(8)==8 % Fructosa
        answ = false;
    elseif A(2)+A(5)+A(3)+A(6)+A(7)+A(8)==6            % Etanol
        answ = false;
    end

    is_vms(i) = (CCc == 0) && (I955 == 0) && (n_params == 13 || (n_params<=9 && n_params>=7)) && answ == true;
end

%Add original model
is_vms(1) = 1;

vms_ids = find(is_vms);
if isempty(vms_ids)
    warning('No VMS models found with criteria CCc==0 and I955==0.');
end

writematrix(vms_ids, vms_txt_file, 'Delimiter', 'tab');
fprintf('VMS auto-generated: %d models -> %s\n', numel(vms_ids), vms_txt_file);

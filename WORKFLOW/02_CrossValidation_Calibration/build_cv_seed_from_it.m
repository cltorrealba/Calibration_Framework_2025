function [kfixed, free_idx, x0_free] = build_cv_seed_from_it(it, model_id)
%BUILD_CV_SEED_FROM_IT Build consistent free-parameter initial seed.
% Supports two formats for it.codes{model_id,2}.k_SSm:
%   - full-length vector (fixed positions often as 0)
%   - compressed vector with only free parameters

r = it.codes{model_id,2};
kfixed = r.kfixed(:)';
free_idx = find(isnan(kfixed));
m = numel(kfixed);
nfree = numel(free_idx);

kssm = r.k_SSm(:)';
theta_full = kfixed;

if numel(kssm) == m
    theta_full(free_idx) = kssm(free_idx);
elseif numel(kssm) == nfree
    theta_full(free_idx) = kssm;
else
    error('Model %d: unexpected k_SSm length (%d). Expected %d or %d.', ...
        model_id, numel(kssm), m, nfree);
end

% Fallback for invalid free seeds using model 1 as reference.
ref = it.codes{1,2}.k_SSm(:)';
if numel(ref) == m
    ref_free = ref(free_idx);
elseif numel(ref) == nfree
    ref_free = ref;
else
    ref_free = ones(1,nfree)*1e-3;
end

x0_free = theta_full(free_idx);
bad = ~isfinite(x0_free) | (x0_free <= 0);
x0_free(bad) = max(abs(ref_free(bad)), 1e-6);

end

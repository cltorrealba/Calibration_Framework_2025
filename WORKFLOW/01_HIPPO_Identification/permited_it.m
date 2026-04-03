%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% permited_it
% Legacy gate function for adding new pending iterations in HIPPO.
% Note: The original name is intentionally kept as "permited" for
% compatibility with add_it.m.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function ok = permited_it(~, last_results)

U = evalin('base','U');
ok = true;

% Criterion III: if regression refinement deviates too much, do not branch.
if isstruct(last_results) && isfield(last_results,'diff')
    d = last_results.diff;
    if ~isempty(d) && isfinite(d)
        ok = d <= U;
    end
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

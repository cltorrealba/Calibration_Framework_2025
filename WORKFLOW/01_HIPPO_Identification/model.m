function dxdt = model(t, x, k)
%MODEL Compatibility wrapper expected by legacy HIPPO scripts.
% Routes ODE evaluations to the curated Zenteno model implementation.

global int_time exp_temp

if evalin('base', 'exist(''kfixed'',''var'')')
    kfixed = evalin('base', 'kfixed');
else
    % Fallback for ad-hoc calls outside HIPPO iteration context.
    kfixed = NaN(size(k));
end

dxdt = Zenteno_Model_2020_PEVth9(t, x, k, int_time, exp_temp, kfixed);

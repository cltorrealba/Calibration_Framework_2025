%------------------------Cross-Validation problem-----------------%
% Compatibility wrapper for MEIGO/ESS.
% Expected call:
%   ess_kernel(problem, opts_SSm, Calib_set, data, scale_id, kfixed)
%
% Therefore the signature must be:
%   f(p, Calib_set, data, scale_id, kfixed)

function Total_Error = CrossValidationCalibrationZ_Alter_Data(p,Calib_set,data,scale_id,kfixed)

Total_Error = CV_Z_Alter_Data(p,Calib_set,data,scale_id,kfixed);

end
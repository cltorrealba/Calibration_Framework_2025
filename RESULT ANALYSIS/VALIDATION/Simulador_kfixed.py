import os
import numpy as np
from scipy.integrate import solve_ivp

def is_quiet() -> bool:
    return str(os.getenv('PIPELINE_QUIET', '0')).lower() in ('1', 'true', 'yes')

# ---------------------------------------------------------------
# re_simulate_zenteno with vectorized p_all reconstruction
# ---------------------------------------------------------------
def zenteno_rhs(t, x, k_free, int_time, exp_temp, kfixed):
    """
    RHS of the Zenteno model (5-state ODE) with vectorized parameter fill
    """
    # 1) mask of free parameters
    mask_free = np.isnan(kfixed)
    n_free = mask_free.sum()
    if n_free != len(k_free):
        raise ValueError(f"Mismatch in free parameters: {n_free} slots but k_free has length {len(k_free)}")
    # 2) construct full parameter vector p_all
    p_all = kfixed.copy()
    p_all[mask_free] = k_free

    # 3) interpolate temp (°C -> K)
    T_K = float(np.interp(t, int_time, exp_temp)) + 273.15

    # 4) enforce non-negativity
    X, N, G, F, E = np.maximum(x, 0)

    # 5) unpack
    (mu0, betaG0, betaF0, Kn0, Kg0, Kf0, Kig0, Kie0,
     Yxn, Yxg, Yxf, Yeg, Yef) = p_all[:13]

    # 6) constants
    Cde, Etd = 0.0415, 130000.0
    R = 8.314
    Eac, Eafe = 59453.0, 11000.0
    EaK = 46055.0
    Eam = 37681.0
    m0 = 0.01

    # 7) constitutive rates
    eps = 1e-12
    mu_max = mu0 * np.exp(Eac * (T_K - 300) / (300 * R * T_K))
    betaG_max = betaG0 * np.exp(Eafe * (T_K - 296.15) / (296.15 * R * T_K))
    betaF_max = betaF0 * np.exp(Eafe * (T_K - 296.15) / (296.15 * R * T_K))
    Kn = Kn0 * np.exp(EaK * (T_K - 293.15) / (293.15 * R * T_K))
    Kg = Kg0 * np.exp(EaK * (T_K - 293.15) / (293.15 * R * T_K))
    Kf = Kf0 * np.exp(EaK * (T_K - 293.15) / (293.15 * R * T_K))
    Kig = Kig0 * np.exp(EaK * (T_K - 293.15) / (293.15 * R * T_K))
    Kie = Kie0 * np.exp(EaK * (T_K - 293.15) / (293.15 * R * T_K))
    m = m0 * np.exp(Eam * (T_K - 293.3) / (293.3 * R * T_K))

    # Safe denominators to avoid division by zero
    mu = mu_max * (N / (N + Kn + eps))
    beta_G = betaG_max * (G / (G + Kg + eps)) * (Kie / (E + Kie + eps))
    beta_F = betaF_max * (F / (F + Kf + eps)) * (Kig / (G + Kig + eps)) * (Kie / (E + Kie + eps))

    Td = -0.0001 * E**3 + 0.0049 * E**2 - 0.1279 * E + 315.89
    Kd0 = 0.00044
    Kd = (Kd0 * np.exp((Cde * E) + (Etd * (T_K - 305.65)) / (305.65 * R * T_K))
          if T_K >= Td else 0)

    # 8) ODEs (epsilon-safe divisions)
    # Clip yields to avoid division by zero
    Yxn = max(Yxn, eps)
    Yxg = max(Yxg, eps)
    Yxf = max(Yxf, eps)
    Yeg = max(Yeg, eps)
    Yef = max(Yef, eps)

    dXdt = mu * X - Kd * X
    dNdt = -mu * (X / Yxn)
    denom_GF = max(G + F, eps)
    ratioG = G / denom_GF
    ratioF = F / denom_GF
    dGdt = -((mu / Yxg) + (beta_G / Yeg) + m * ratioG) * X
    dFdt = -((mu / Yxf) + (beta_F / Yef) + m * ratioF) * X
    dEdt = (beta_G + beta_F) * X

    return [dXdt, dNdt, dGdt, dFdt, dEdt]

def resimulate_optimal(k_free, x0, time_dap, int_time, exp_temp,
                       Kinetic_Matrix, kfixed, FDA_add_idx):
    """Two-stage around DAP using stiff BDF solver, with exp_temp cleaned"""
    # clean exp_temp: linear interpolation over non-nan values
    mask_valid = ~np.isnan(exp_temp)
    if not mask_valid.any():
        raise ValueError("All temperature data are NaN; cannot integrate.")
    exp_temp = np.interp(int_time, int_time[mask_valid], exp_temp[mask_valid])

    # split times before and after addition
    t1 = int_time[int_time < time_dap]
    t2 = int_time[int_time >= time_dap]
    if t1.size == 0 or t2.size == 0:
        raise ValueError(f"Invalid DAP split: t1={t1.size}, t2={t2.size}")

    # Stage 1: before DAP
    if not is_quiet():
        print(f"\n>> DEBUG resimulate_optimal:")
        print(f"   t1[0] = {t1[0]:.3f}, t1[-1] = {t1[-1]:.3f}, len(t1) = {len(t1)}")
    sol1 = solve_ivp(
        lambda t, y: zenteno_rhs(t, y, k_free, int_time, exp_temp, kfixed),
        (t1[0], t1[-1]), x0,
        method='BDF', dense_output=True
    )
    if not is_quiet():
        print(f"   sol1.y.shape = {sol1.y.shape}")

    y1 = sol1.sol(t1).T

    # inject FDA addition
    x02 = y1[-1].copy()
    # dosis a partir de la fila cinética correcta
    dose_mgL = Kinetic_Matrix[FDA_add_idx, 3]     # mg/L
    dose_gL  = dose_mgL / 1000.0
    if not is_quiet():
        print(f"   >> Inyectando {dose_gL:.3f} g/L YAN en fila {FDA_add_idx}")
    x02[1] += dose_gL
    if not is_quiet():
        print(f"   >> DEBUG después de inyección, x02 (YAN) = {x02[1]:.4f}")
    
    # Stage 2: after DAP
    sol2 = solve_ivp(
        lambda t, y: zenteno_rhs(t, y, k_free, int_time, exp_temp, kfixed),
        (t2[0], t2[-1]), x02,
        method='BDF', dense_output=True
    )
    if not is_quiet():
        print(f"   sol2.y.shape = {sol2.y.shape}")
    y2 = sol2.sol(t2).T

    # concatenate on original grid
    T = np.concatenate([t1, t2])
    Xf = np.vstack([y1, y2])
    return T, Xf
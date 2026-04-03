import os
import numpy as np
# from Carga_datos_v1 import DataLoad
from Carga_datos import DataLoad
from model_ci_loader import load_model_params
from Simulador_kfixed import resimulate_optimal

def is_quiet() -> bool:
    return str(os.getenv('PIPELINE_QUIET', '0')).lower() in ('1', 'true', 'yes')

def simulate_kfixed_model(model_id: int,
                            scale_id: int,
                            exper_id: int,
                            kfixed_0: np.ndarray):

     # 1) Cargar datos experimentales
    Km, Tpair, Measure_idx, fda_pair, _ = DataLoad(scale_id, exper_id)
    if not is_quiet():
        print(f"\n>> DEBUG simulate_kfixed_model:")
        print(f"   fda_pair      = {fda_pair}")
        print(f"   Tpair.shape   = {Tpair.shape}")
        print(f"   Measure_idx   = {Measure_idx} (len={len(Measure_idx)})")
    
    # 2) Parámetros operacionales: densidad y tiempo de adición

    rho_dap, time_dap = fda_pair
    sample_times = Tpair[Measure_idx, 0]
    if not is_quiet():
        print(f"   sample_times  = {sample_times}")
        print(f"   time_dap      = {time_dap:.3f}")
    
    diffs = np.abs(sample_times - time_dap)
    FDA_add_idx = np.argmin(diffs)
    if not is_quiet():
        print(f"   >> DEBUG: FDA_add_idx = {FDA_add_idx}, "
              f"sample_times[{FDA_add_idx}] = {sample_times[FDA_add_idx]:.3f}, "
          f"Δ = {diffs[FDA_add_idx]:.3f}")
    int_time, exp_temp = Tpair[:,0], Tpair[:,1]


    # 3) Determinar FDA_add_idx sobre los tiempos cinéticos
    sample_times = Tpair[Measure_idx, 0]   # == k_time
    if diffs[FDA_add_idx] > 1e-6:
        if not is_quiet():
            print(
                f"Warning: DAP time {time_dap:.3f} h matched to "
                f"kinetics time {sample_times[FDA_add_idx]:.3f} h "
                f"(Δ={diffs[FDA_add_idx]:.3f} h)"
            )

    # 4) Corrección de YAN "estancada"
    Stuck_YANs = np.loadtxt('Stuck_YANs.txt')
    stuck_yan = Stuck_YANs[exper_id-1, scale_id-1]
    Km[:,3] = np.maximum(Km[:,3] - stuck_yan, 0)

    # 4) Determinar FDA_add_idx
    sample_times = int_time[Measure_idx]
    diffs        = np.abs(sample_times - time_dap)
    idx_closest  = np.argmin(diffs)
    FDA_add_idx  = idx_closest   # <-- ¡índice relativo a Km!
    if diffs[idx_closest] > 0.1 and not is_quiet():
        print(
            f"Warning: DAP time {time_dap:.3f}h matched to measurement time "
            f"{sample_times[idx_closest]:.3f}h (Δ={diffs[idx_closest]:.3f}h)"
        )
        
     # 5) Condición inicial
    x0 = np.array([
         0.2,
         Km[0,3] / 1000.0,  # YAN mg/L -> g/L
         Km[0,0],          # Glucosa
         Km[0,1],          # Fructosa
         0.0               # Etanol
     ])

     # 6) Cargar parámetros de calibración
    flags, p_opt, CI_95 = load_model_params(model_id, scale_id)

    # ───── DEBUG ────────────────────────────────────────────────────────────────
    if not is_quiet():
        print(f"[DEBUG simulate] model_id={model_id}, scale_id={scale_id}")
        print("  flags:", flags, type(flags), flags.dtype if hasattr(flags, 'dtype') else None)
        print("  p_opt:", p_opt, type(p_opt), p_opt.dtype if hasattr(p_opt, 'dtype') else None)
        print("  CI_95:", CI_95, type(CI_95))
    # ─────────────────────────────────────────────────────────────────────────────
     # 7) Construir kfixed y k_free
    kfixed = np.where(flags==1, kfixed_0, np.nan)
    k_free = p_opt[flags==0]

# 8) Ejecutar simulación en dos etapas con keywords para evitar errores de ordenamiento
    T, Xf = resimulate_optimal(
        k_free         = k_free,
        x0             = x0,
        time_dap       = time_dap,
        int_time       = int_time,
        exp_temp       = exp_temp,
        Kinetic_Matrix = Km,
        kfixed         = kfixed,
        FDA_add_idx    = FDA_add_idx
        )

    # 9) Empaquetar contexto **incluyendo** FDA_add_idx
    context = {
        'flags':       flags,
        'p_opt':       p_opt,
        'CI_95':       CI_95,
        'Km':          Km,
        'Tpair':       Tpair,
        'Measure_idx': Measure_idx,
        'fda_pair':    fda_pair,
        'FDA_add_idx': FDA_add_idx,   # <–– aquí
    }
    return T, Xf, context

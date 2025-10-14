import numpy as np
# from Carga_datos_v1 import DataLoad
from Carga_datos import DataLoad
from model_ci_loader import load_model_params
from Simulador_kfixed import resimulate_optimal

def simulate_kfixed_model(model_id: int,
                            scale_id: int,
                            exper_id: int,
                            kfixed_0: np.ndarray):
     """
     Wrapper to run the two-stage Zenteno simulation given calibration and experimental settings,
     incluyendo corrección de YAN estancada y cálculo de FDA_add_idx aproximado.
     """
     # 1) Cargar datos experimentales
     Km, Tpair, Measure_idx, fda_pair, _ = DataLoad(scale_id, exper_id)
     int_time, exp_temp = Tpair[:,0], Tpair[:,1]

     # 2) Parámetros operacionales: densidad y tiempo de adición
     rho_dap, time_dap = fda_pair

     # 3) Corrección de YAN "estancada"
     Stuck_YANs = np.loadtxt('Stuck_YANs.txt')
     stuck_yan = Stuck_YANs[exper_id-1, scale_id-1]
     Km[:,3] = np.maximum(Km[:,3] - stuck_yan, 0)

    # 4) Determinar FDA_add_idx
     sample_times = int_time[Measure_idx]
     diffs        = np.abs(sample_times - time_dap)
     idx_closest  = np.argmin(diffs)
     FDA_add_idx  = idx_closest   # <-- ¡índice relativo a Km!
     if diffs[idx_closest] > 0.1:
        print(f"Warning: DAP time {time_dap:.3f}h matched to measurement time " f"{sample_times[idx_closest]:.3f}h (Δ={diffs[idx_closest]:.3f}h)")
        
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

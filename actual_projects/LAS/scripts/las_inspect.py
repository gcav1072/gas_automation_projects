import lasio
import pandas as pd
import numpy as np
import os

# --- CONFIGURACIÓN DE ALIAS ---
# Se agregó DRHO para control de calidad avanzado
ALIAS_CFG = {
    'GR':   ['GR', 'GAPI', 'GAM', 'GR_EDTC', 'CGR', 'NGAP', 'SGR', 'GRR'],
    'RDEP': ['RDEP', 'RT', 'ILD', 'LLD', 'AT90', 'RES_DEEP', 'HDRS', 'RES_DEP', 'HRLD'],
    'RMED': ['RMED', 'ILM', 'LLS', 'AT30', 'AT20', 'RES_MED', 'IMPH', 'HRLS'],
    'NPHI': ['NPHI', 'TNPH', 'NPOR', 'CNPOR', 'CNC', 'NPSS', 'NPLS', 'CNL'],
    'RHOB': ['RHOB', 'RHOZ', 'DEN', 'ZDEN', 'BDEN', 'RHOM'], 
    'DPHI': ['DPLS', 'DPHI', 'DPHZ', 'DPOR'], 
    'DT':   ['DT', 'DTCO', 'DTC', 'DT4P', 'AC'],
    # --- CURVAS DE CALIDAD ---
    'CALI': ['CALI', 'CAL', 'CALS', 'HCAL', 'DCAL', 'CLDC', 'C1'],
    'BS':   ['BS', 'BIT', 'BIT_SIZE', 'BSZ'],
    'DRHO': ['DRHO', 'DCAL', 'CORR', 'ZCOR', 'HDRA', 'RHOC'] # Corrección de Densidad
}

def obtener_curva(df, mnemonico_objetivo):
    """Busca la curva usando alias y devuelve una Serie limpia."""
    cols_upper = {col.upper(): col for col in df.columns}
    candidatos = ALIAS_CFG.get(mnemonico_objetivo, [mnemonico_objetivo])
    
    for alias in candidatos:
        if alias in cols_upper:
            return df[cols_upper[alias]]
            
    return pd.Series(np.nan, index=df.index)

def normalizar_unidades_profundidad(las, df):
    unidad = ""
    if 'STRT' in las.well:
        unidad = str(las.well['STRT'].unit).upper()
    elif 'DEPT' in las.curves:
        unidad = str(las.curves['DEPT'].unit).upper()
        
    es_pies = any(x in unidad for x in ['F', 'FT', 'FEET'])
    
    if es_pies:
        # 1 ft = 0,3048 m
        df.index = df.index * 0.3048
        return df, True
    else:
        return df, False

def inspeccionar_las(las_file):
    try:
        las = lasio.read(las_file)
        df = las.df()

        val_nulo = las.well.NULL.value if 'NULL' in las.well else -999.25
        df.replace([val_nulo, -999.25], np.nan, inplace=True)
        df.dropna(how='all', inplace=True)
        
        df, _ = normalizar_unidades_profundidad(las, df)
        return df

    except Exception as e:
        print(f"Error leyendo {os.path.basename(las_file)}: {e}")
        return None

def calcular_vsh(df, gr_sand=None, gr_shale=None):
    gr = obtener_curva(df, 'GR')
    if gr.isna().all(): return df 

    gr_clean = gr.dropna()
    if gr_clean.empty: return df

    # Normalización: Usar parámetros de campo (Si se dan) o estadística del pozo
    if gr_sand is not None and gr_shale is not None:
        gr_min = float(gr_sand)
        gr_max = float(gr_shale)
    else:
        # Usamos percentiles para evitar picos ruidosos (spikes)
        gr_min = np.percentile(gr_clean, 5)
        gr_max = np.percentile(gr_clean, 95)
    
    # CRITERIO DE ROBUSTEZ:
    # Si la diferencia es ridícula (y no fue forzada por usuario), asumimos log plano
    if (gr_sand is None) and (gr_max - gr_min < 20):
         # Asumir que es Arcilla (No Pay) por seguridad si el log es plano/muerto
         vsh = pd.Series(1.0, index=df.index) 
    else:
         # Evitar división por cero
         denom = gr_max - gr_min
         if denom == 0: denom = 0.001
         vsh = (gr - gr_min) / denom
    
    df['VSH'] = np.clip(vsh, 0, 1) 
    return df

def aplicar_filtro_calidad(df, bit_size=8.5, tol_cal=2.5, tol_drho=0.15):
    """
    QC Robusto - Estrategia 'Hard Kill' (Muerte Súbita)
    1. Filtro Mecánico (Caliper > BS + Tol).
    2. Filtro de Contacto (DRHO > 0,15).
    3. Filtro Físico (Densidades imposibles < 1,95).
    4. Techo estricto de Porosidad (32% - Hard Kill).
    """
    
    mask_bad_data = pd.Series(False, index=df.index)
    
    # --- 1. FILTRO MECÁNICO (CALIPER) ---
    cal = obtener_curva(df, 'CALI')
    has_cal = not cal.isna().all()
    
    if has_cal:
        # Detectar Washouts
        mask_cal_bad = cal > (bit_size + tol_cal)
        mask_bad_data = mask_bad_data | mask_cal_bad
    
    # --- 2. FILTRO DE CONTACTO (DRHO) ---
    drho = obtener_curva(df, 'DRHO')
    if not drho.isna().all():
        # DRHO > 0,15 o < -0,15 g/cc es inaceptable
        mask_drho_bad = drho.abs() > tol_drho
        mask_bad_data = mask_bad_data | mask_drho_bad

    # --- APLICACIÓN DE MÁSCARA DE MALA CALIDAD ---
    cols_afectadas = ['RHOB', 'DPHI_FINAL', 'NPHI_FINAL', 'PEF']
    for col in cols_afectadas:
        if col in df.columns:
            df.loc[mask_bad_data, col] = np.nan
            
    df['BAD_HOLE'] = mask_bad_data 

    # --- 3. FILTRO FÍSICO (DENSIDAD MÍNIMA) ---
    if 'RHOB' in df.columns:
        limite_fisico = 1.95 # Densidad mínima creíble para roca
        mask_rho_lodo = df['RHOB'] < limite_fisico
        
        if mask_rho_lodo.any():
            df.loc[mask_rho_lodo, 'RHOB'] = np.nan
            if 'DPHI_FINAL' in df.columns:
                df.loc[mask_rho_lodo, 'DPHI_FINAL'] = np.nan

    # --- 4. TECHO DE POROSIDAD (EL "MATAGIGANTES") ---
    # Aquí cambiamos .clip() por asignación de NaN.
    # Si es > 35% (o 32% si no hay QC), se ELIMINA.
    
    techo_tolerante = 35.0
    techo_estricto = 30.0 # Muy estricto si no tenemos Caliper/DRHO
    
    techo_aplicar = techo_tolerante if (has_cal or not drho.isna().all()) else techo_estricto
    
    for col in ['DPHI_FINAL', 'NPHI_FINAL']:
        if col in df.columns:
            # HARD KILL: Si supera el techo, es NaN. No se recorta a 35, se BORRA.
            mask_irreal = df[col] > techo_aplicar
            df.loc[mask_irreal, col] = np.nan 

    # Re-limpieza de Sw derivada
    if 'SW' in df.columns:
        mask_no_phi = False
        if 'DPHI_FINAL' in df.columns: mask_no_phi |= df['DPHI_FINAL'].isna()
        if 'NPHI_FINAL' in df.columns: mask_no_phi |= df['NPHI_FINAL'].isna()
        df.loc[mask_no_phi, 'SW'] = np.nan
            
    return df

def normalizar_porosidad(df, rho_matrix=2.65, rho_fluid=1.0, usar_pef=True):
    den = obtener_curva(df, 'RHOB') 
    if den.isna().all(): den = obtener_curva(df, 'DPHI')
    neu = obtener_curva(df, 'NPHI') 
    pef = obtener_curva(df, 'PEF')

    # --- Lógica de Matriz Variable basada en PEF (Punto a Punto) ---
    # Si activado, recalculamos una curva de rho_matrix en lugar de usar un escalar
    use_variable_matrix = False
    rho_ma_curve = rho_matrix # Default escalar

    if usar_pef and not pef.isna().all() and not den.isna().all():
        use_variable_matrix = True
        # Crear curva de Matriz Dinámica
        # Si PEF < 2.5 -> Arenisca (2.65)
        # Si PEF > 4.5 -> Caliza (2.71)
        # Interpolación o Bloques simple:
        conditions = [
            (pef < 2.5),
            (pef >= 2.5) & (pef < 4.0),
            (pef >= 4.0)
        ]
        choices = [2.65, 2.75, 2.71] # 2.75 asume mezcla calcárea/arcillosa en transición
        rho_ma_curve = np.select(conditions, choices, default=2.65)
        df['RHOMA_AUTO'] = rho_ma_curve # Guardamos para debug


    if not den.isna().all():
        valid = den[den > 0]
        # Detectar si la curva viene en g/cc o en %
        if not valid.empty and valid.mean() > 1.5: 
            # Está en g/cc, calculamos porosidad
            if use_variable_matrix:
                df['DPHI_FINAL'] = ((rho_ma_curve - den) / (rho_ma_curve - rho_fluid)) * 100
            else:
                df['DPHI_FINAL'] = ((rho_matrix - den) / (rho_matrix - rho_fluid)) * 100
        elif not valid.empty and valid.max() <= 1.0: 
            # Está en V/V
            df['DPHI_FINAL'] = den * 100
        else: 
            # Está en porcentaje
            df['DPHI_FINAL'] = den

    if not neu.isna().all():
        valid_neu = neu[(neu > -10) & (neu.notna())]
        if not valid_neu.empty and valid_neu.max() <= 1.0:
            df['NPHI_FINAL'] = neu * 100
        else:
            df['NPHI_FINAL'] = neu
    
    # Nota: Los límites de -5 a 60 aquí son solo para evitar errores matemáticos,
    # el filtro de calidad real ocurre en 'aplicar_filtro_calidad'
            
    # --- CÁLCULO DE SEPARACIÓN D-N (SHALE INDICATOR) ---
    if 'DPHI_FINAL' in df.columns and 'NPHI_FINAL' in df.columns:
        df['DN_SEP'] = df['NPHI_FINAL'] - df['DPHI_FINAL']
    else:
        df['DN_SEP'] = 0.0
            
    return df

def calcular_sw(df, a=1, m=2, n=2, rw=0.05, modelo='simandoux', r_shale=2.0):
    """
    Calcula Sw usando Archie (Clean) o Simandoux (Shaly).
    modelo: 'archie' o 'simandoux'
    r_shale: Resistividad de la arcilla (ohm.m)
    """
    rt = obtener_curva(df, 'RDEP')
    
    if 'DPHI_FINAL' in df.columns and 'NPHI_FINAL' in df.columns:
        phi_pct = (df['DPHI_FINAL'] + df['NPHI_FINAL']) / 2
    elif 'DPHI_FINAL' in df.columns:
        phi_pct = df['DPHI_FINAL']
    elif 'NPHI_FINAL' in df.columns:
        phi_pct = df['NPHI_FINAL']
    else:
        return df

    phi = phi_pct / 100
    vsh = df['VSH'] if 'VSH' in df.columns else pd.Series(0, index=df.index)
    
    # Mask de validez general
    mask_valid = (phi > 0.001) & (rt > 0.1)
    sw = pd.Series(1.0, index=df.index)
    
    # --- Modelo ARCHIE ---
    if modelo == 'archie':
        try:
            term = (a * rw) / (np.power(phi[mask_valid], m) * rt[mask_valid])
            sw_calc = np.power(term, (1/n))
            sw.loc[mask_valid] = np.clip(sw_calc, 0, 1)
        except:
            pass

    # --- Modelo SIMANDOUX (Modified) ---
    elif modelo == 'simandoux':
        try:
            idx = mask_valid
            phi_z = phi[idx]
            rt_z = rt[idx]
            vsh_z = vsh[idx]
            
            # --- CORRECCIÓN: SIMANDOUX MODIFICADO ---
            # El término de arena debe penalizarse por (1 - Vsh)
            # Evitamos división por cero en (1-Vsh) con un clip suave
            factor_vsh = 1 - vsh_z
            factor_vsh = factor_vsh.clip(lower=0.01) # Seguridad numérica
            
            # Coeficiente A (Término cuadrático: Arena)
            # Modified Simandoux: Phi^m / (a * Rw * (1-Vsh))
            coef_a = (np.power(phi_z, m)) / (a * rw * factor_vsh)
            
            # Coeficiente B (Término lineal: Arcilla)
            safe_r_shale = r_shale if r_shale > 0 else 0.1
            coef_b = vsh_z / safe_r_shale
            
            # Coeficiente C (Constante)
            coef_c = - (1 / rt_z)
            
            # Resolución Cuadrática
            discriminante = coef_b**2 - (4 * coef_a * coef_c)
            discriminante[discriminante < 0] = 0
            
            sw_calc = (-coef_b + np.sqrt(discriminante)) / (2 * coef_a)
            sw.loc[idx] = np.clip(sw_calc, 0, 1)
            
        except Exception as e:
            print(f"Error en Simandoux: {e}")
            pass

    df['SW'] = sw
    return df
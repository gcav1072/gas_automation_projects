import lasio
import pandas as pd
import numpy as np
import os

# --- CONFIGURACIÓN DE ALIAS ---
ALIAS_CFG = {
    'GR':   ['GR', 'GAPI', 'GAM', 'GR_EDTC', 'CGR', 'NGAP', 'SGR'],
    'RDEP': ['RDEP', 'RT', 'ILD', 'LLD', 'AT90', 'RES_DEEP', 'HDRS', 'RES_DEP'],
    'RMED': ['RMED', 'ILM', 'LLS', 'AT30', 'AT20', 'RES_MED', 'IMPH'],
    'NPHI': ['NPHI', 'TNPH', 'NPOR', 'CNPOR', 'CNC', 'NPSS', 'NPLS', 'CNL'],
    'RHOB': ['RHOB', 'RHOZ', 'DEN', 'ZDEN', 'BDEN', 'RHOM'], 
    'DPHI': ['DPLS', 'DPHI', 'DPHZ', 'DPOR'], 
    'DT':   ['DT', 'DTCO', 'DTC', 'DT4P', 'AC'],
    # NUEVOS ALIAS PARA CALIDAD
    'CALI': ['CALI', 'CAL', 'CALS', 'HCAL', 'DCAL', 'CLDC'],
    'BS':   ['BS', 'BIT', 'BIT_SIZE', 'BSZ']
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
        # 1 ft = 0.3048 m
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

def calcular_vsh(df):
    gr = obtener_curva(df, 'GR')
    if gr.isna().all(): return df 

    gr_clean = gr.dropna()
    if gr_clean.empty: return df

    gr_min = np.percentile(gr_clean, 5)
    gr_max = np.percentile(gr_clean, 95)
    
    if gr_max - gr_min < 10:
         vsh = pd.Series(0, index=df.index)
    else:
         vsh = (gr - gr_min) / (gr_max - gr_min)
    
    df['VSH'] = np.clip(vsh, 0, 1) 
    return df

def normalizar_porosidad(df, rho_matrix=2.65, rho_fluid=1.0):
    den = obtener_curva(df, 'RHOB') 
    if den.isna().all(): den = obtener_curva(df, 'DPHI')
    neu = obtener_curva(df, 'NPHI') 

    if not den.isna().all():
        valid = den[den > 0]
        if not valid.empty and valid.mean() > 1.5: 
            df['DPHI_FINAL'] = ((rho_matrix - den) / (rho_matrix - rho_fluid)) * 100
        elif not valid.empty and valid.max() <= 1.0: 
            df['DPHI_FINAL'] = den * 100
        else: 
            df['DPHI_FINAL'] = den

    if not neu.isna().all():
        valid_neu = neu[(neu > -10) & (neu.notna())]
        if not valid_neu.empty and valid_neu.max() <= 1.0:
            df['NPHI_FINAL'] = neu * 100
        else:
            df['NPHI_FINAL'] = neu
            
    for col in ['DPHI_FINAL', 'NPHI_FINAL']:
        if col in df.columns: df[col] = df[col].clip(-5, 60)

    # --- NUEVO: CÁLCULO DE SEPARACIÓN D-N (SHALE INDICATOR) ---
    # Calculamos cuánto se separa el Neutrón de la Densidad.
    # En arenas limpias/petróleo: DPHI >= NPHI (Separación negativa o cero).
    # En arcillas (Shale): NPHI >>> DPHI (Separación positiva grande).
    if 'DPHI_FINAL' in df.columns and 'NPHI_FINAL' in df.columns:
        df['DN_SEP'] = df['NPHI_FINAL'] - df['DPHI_FINAL']
    else:
        df['DN_SEP'] = 0.0
            
    return df

def calcular_sw(df, a=1, m=2, n=2, rw=0.05):
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
    mask_valid = (phi > 0.001) & (rt > 0.1)
    
    sw = pd.Series(1.0, index=df.index)
    
    try:
        term = (a * rw) / (np.power(phi[mask_valid], m) * rt[mask_valid])
        sw_calc = np.power(term, (1/n))
        sw.loc[mask_valid] = np.clip(sw_calc, 0, 1)
    except:
        pass

    df['SW'] = sw
    return df

def aplicar_filtro_calidad(df, bit_size=8.5, tolerancia=2.5):
    """
    Control de Calidad (QC) Integral:
    1. Detecta Washouts (Caliper).
    2. Elimina lecturas de Densidad imposibles (Lodo/Agua).
    3. Recorta Porosidades irreales.
    """
    # --- 1. FILTRO MECÁNICO (CALIPER / WASHOUT) ---
    cal = obtener_curva(df, 'CALI')
    
    if cal.isna().all():
        df['BAD_HOLE'] = False
        print("   ⚠️  No se encontró Caliper. Saltando filtro mecánico.")
    else:
        # Lógica: Si Caliper > Bit Size + Tolerancia
        mask_bad_hole = cal > (bit_size + tolerancia)
        df['BAD_HOLE'] = mask_bad_hole
        
        pct_bad = (mask_bad_hole.sum() / len(df)) * 100
        if pct_bad > 0:
            print(f"   -> QC Mecánico: {pct_bad:.1f}% marcado como Derrumbe (Washout)")
            
            # Limpiamos curvas sensibles al contacto con la pared
            cols_sensibles = ['RHOB', 'DPHI_FINAL', 'PEF', 'DRHO']
            for col in cols_sensibles:
                if col in df.columns:
                    df.loc[mask_bad_hole, col] = np.nan

    # --- 2. FILTRO FÍSICO (DENSIDAD MÍNIMA) ---
    if 'RHOB' in df.columns:
        limite_fisico = 1.75
        mask_rho_erronea = df['RHOB'] < limite_fisico
        
        pct_err = (mask_rho_erronea.sum() / len(df)) * 100
        if pct_err > 0:
            print(f"   -> QC Físico: {pct_err:.1f}% eliminado por Densidad irreal (< {limite_fisico} g/cc)")
            
            # Anulamos la densidad y cualquier cálculo derivado
            df.loc[mask_rho_erronea, 'RHOB'] = np.nan
            if 'DPHI_FINAL' in df.columns: 
                df.loc[mask_rho_erronea, 'DPHI_FINAL'] = np.nan

    # --- 3. FILTRO LÓGICO (TECHO DE POROSIDAD) ---
    # Nadie tiene 56% de porosidad a 3000 metros de profundidad.
    techo_phi = 45.0 # Porcentaje
    
    for col in ['DPHI_FINAL', 'NPHI_FINAL']:
        if col in df.columns:
            # Clip upper limita los valores máximos sin borrarlos (los baja al techo)
            # Opcional: Podrías usar NaN si prefieres ser más estricto
            df[col] = df[col].clip(upper=techo_phi)

    # Re-limpiamos saturación si las porosidades cambiaron a NaN
    if 'SW' in df.columns and 'DPHI_FINAL' in df.columns:
        # Si la porosidad se volvió NaN por los filtros, la Sw debe morir también
        df.loc[df['DPHI_FINAL'].isna(), 'SW'] = np.nan
            
    return df
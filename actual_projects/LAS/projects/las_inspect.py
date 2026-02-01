import lasio
import pandas as pd
import numpy as np
import os

# --- CONFIGURACIÓN DE ALIAS Y FUNCIONES ---

# 1. Tu diccionario maestro (Edítalo si descubres nuevos nombres raros)
ALIAS_CFG = {
    'GR':   ['GR', 'GAPI', 'GAM', 'GR_EDTC', 'CGR', 'NGAP', 'SGR'], # Added SGR as it was in original
    'RDEP': ['RDEP', 'RT', 'ILD', 'LLD', 'AT90', 'RES_DEEP', 'HDRS'],
    'RMED': ['RMED', 'ILM', 'LLS', 'AT30', 'AT20', 'RES_MED', 'IMPH'], # Added IMPH
    'NPHI': ['NPHI', 'TNPH', 'NPOR', 'CNPOR', 'CNC', 'NPSS', 'NPLS'], # Added NPLS
    'RHOB': ['RHOB', 'RHOZ', 'DEN', 'ZDEN', 'BDEN', 'RHOM', 'DPLS', 'DPHI', 'PEF'], # Merged DPHI list here as RHOB alias group seems to be the target for density, but let's be careful. 
    # Original 'DPHI' list: ['DPLS', 'DPHI', 'RHOB', 'ZDEN', 'DEN', 'PEF']. 
    # Snippet 'RHOB' list: ['RHOB', 'RHOZ', 'DEN', 'ZDEN', 'BDEN', 'RHOM'].
    # I will keep them separate or merge intelligently. The snippet asks for RHOB. 
    # I will add DPHI/DPLS to RHOB list as alternate density/porosity sources if that's the intent, 
    # BUT `normalizar_porosidad` distinguishes between Density (g/cc) and Porosity (v/v or %).
    # The snippet `obtener_curva(df, 'RHOB')` implies grabbing Density. 
    # I will stick to the snippet's ALIAS_CFG for RHOB but add the extra ones from the original file to it to be safe.
    'DT':   ['DT', 'DTCO', 'DTC', 'DT4P', 'AC']
}

def obtener_curva(df, mnemonico_objetivo):
    """Busca la curva usando alias y devuelve una Serie limpia."""
    cols_upper = {col.upper(): col for col in df.columns}
    candidatos = ALIAS_CFG.get(mnemonico_objetivo, [mnemonico_objetivo])
    
    for alias in candidatos:
        if alias in cols_upper:
            nombre_real = cols_upper[alias]
            print(f"   -> {mnemonico_objetivo}: Encontrado como '{nombre_real}'")
            return df[nombre_real]
            
    print(f"⚠️  WARNING: No se encontró '{mnemonico_objetivo}'. Se llenará con NaN.")
    return pd.Series(np.nan, index=df.index)

def inspeccionar_las(las_file):
    try:
        # --- CARGA DE DATOS ---
        print(f"--- REPORTE DEL POZO: {os.path.basename(las_file)} ---")
        las = lasio.read(las_file)
        df = las.df() # Convertir a DataFrame

        # 2.1 LIMPIEZA CRÍTICA DE NULOS
        val_nulo = las.well.NULL.value if 'NULL' in las.well else None
        
        if val_nulo is not None:
            df.replace(val_nulo, np.nan, inplace=True)
        else:
            # Si el header no lo dice, forzamos el estándar común
            df.replace(-999.25, np.nan, inplace=True)
            
        # Limpieza extra: Eliminar filas donde TODO sea NaN
        df.dropna(how='all', inplace=True)
        
        # Recuperar lógica de unidades para display (opcional, nice feature)
        unidad_profundidad = las.well['STRT'].unit if 'STRT' in las.well else ""
        if not unidad_profundidad and len(las.curves) > 0:
            unidad_profundidad = las.curves[0].unit
            
        print(f"Unidad detectada: {unidad_profundidad}")
        
        return df

    except Exception as e:
        print(f"Error leyendo el archivo: {e}")
        return None

def calcular_vsh(df):
    print("\n--- CÁLCULO DE VSH INTELIGENTE ---")
    
    # 1. Usamos obtener_curva
    # Note: df is already clean from inspeccionar_las
    gr = obtener_curva(df, 'GR')
    
    # Manejo de errores si no hay GR (todo NaN)
    if gr.isna().all():
        print("Error: No se encontró ninguna curva de Gamma Ray válida.")
        return df # Retornamos DF original sin VSH, o con VSH vacía? Mejor sin.

    # 2. Limpieza y Estadística (sobre la serie ya extraída)
    # gr es una Series, podemos usar sus métodos.
    # Clip outliers for standard Vcal? Or just Linear?
    # Keeping implementation simple as per snippet suggestion but robust
    
    gr_min, gr_max = gr.min(), gr.max()
    
    # Avoid div by zero
    if gr_max == gr_min:
         vsh = pd.Series(0, index=df.index)
    else:
         vsh = (gr - gr_min) / (gr_max - gr_min)
    
    df['VSH'] = np.clip(vsh, 0, 1) # Guardamos en el DF
    return df

def normalizar_porosidad(df, rho_matrix=2.65, rho_fluid=1.0):
    print("\n--- NORMALIZANDO CURVAS DE POROSIDAD ---")
    
    # Usamos obtener_curva para extraer las series (ya limpias de nulos del sistema)
    # y manejamos NANs locales.
    den = obtener_curva(df, 'RHOB') 
    neu = obtener_curva(df, 'NPHI') 

    # --- CORRECCIÓN DE DENSIDAD (RHOB -> DPHI) ---
    if not den.isna().all():
        # Lógica para distinguir si es RHOB (g/cc) o ya es Porosidad
        # Filtramos valores "físicos" para el check
        datos_validos = den[den > 0]
        
        if datos_validos.empty:
             promedio = 0
        else:
             promedio = datos_validos.mean()

        # Si el promedio es > 1.5, es Densidad (g/cc) --> Convertir
        if promedio > 1.5:
            print(f"Detectado RHOB. Usando Matrix={rho_matrix}, Fluid={rho_fluid}")
            # Guardamos como DPHI_FINAL (usando variables, no constantes)
            df['DPHI_FINAL'] = ((rho_matrix - den) / (rho_matrix - rho_fluid)) * 100
        
        # Si no, verificamos si es Porosidad Decimal (v/v) --> Multiplicar por 100
        elif datos_validos.max() <= 1.0: 
            print(f"Detectado DPHI decimal. Pasando a %.")
            df['DPHI_FINAL'] = den * 100
        
        # Si no, ya está en porcentaje
        else:
            print(f"Detectado DPHI Porcentaje.")
            df['DPHI_FINAL'] = den
    else:
        print("No se encontró curva de Densidad/Porosidad válida.")

    # --- CORRECCIÓN DE NEUTRÓN (NPHI) ---
    if not neu.isna().all():
        # Misma lógica: filtrar nulos negativos/extremos
        datos_validos_neu = neu[(neu > -10) & (neu.notna())]
        
        if not datos_validos_neu.empty and datos_validos_neu.max() <= 1.0:
            print(f"Detectado NPHI decimal. Pasando a %.")
            df['NPHI_FINAL'] = neu * 100
        else:
            df['NPHI_FINAL'] = neu
    
    if 'DPHI_FINAL' in df.columns:
        df['DPHI_FINAL'] = df['DPHI_FINAL'].clip(lower=-5, upper=60)
    if 'NPHI_FINAL' in df.columns:
        df['NPHI_FINAL'] = df['NPHI_FINAL'].clip(lower=-5, upper=60)
    
    # Clip entre -5% y 60%. 
    # ¿Por qué -5 y no 0? Para que si hay Anhidrita (matriz pesada), 
    # veas la curva irse un poco a la izquierda (aviso visual) en vez de 
    # aplanarse en cero artificialmente.
    # El neutrón a veces lee -2% o -3% en gas muy seco o matrices apretadas.
            
    return df
import lasio
import pandas as pd
import numpy as np
import os

def inspeccionar_las(las_file):
    #usamos try por si el archivo no se encuentra o está dañado
    try:
        #leemos el archivo las

        las = lasio.read(las_file)
        #asignamos valores a variables

        start = las.well['STRT'].value if 'STRT' in las.well else "N/A"
        stop  = las.well['STOP'].value if 'STOP' in las.well else "N/A"
        step  = las.well['STEP'].value if 'STEP' in las.well else "N/A"
        # 1. Intento A: Leer la unidad del atributo 'STRT' (Estándar)
        # Nota: No buscamos una variable 'UNITS', sino el atributo .unit de STRT
        unidad_profundidad = las.well['STRT'].unit if 'STRT' in las.well else ""

        # 2. Intento B: Si el encabezado falla, mirar la primera curva
        # La primera curva (índice 0) SIEMPRE es la referencia (Profundidad o Tiempo)
        if not unidad_profundidad or unidad_profundidad.strip() == "":
            if len(las.curves) > 0:
                unidad_profundidad = las.curves[0].unit
                print(f"Nota: Unidad recuperada desde la curva '{las.curves[0].mnemonic}'")
    
        # 3. Normalización (Evitar F, FT, F., FEET)
        if unidad_profundidad.upper() in ['F', 'FT', 'FEET', 'F.']:
            unidad_std = "FT"
        elif unidad_profundidad.upper() in ['M', 'METER', 'METERS', 'METRE']:
            unidad_std = "M"
        else:
            unidad_std = "DESCONOCIDO"

        print(f"Unidad detectada: {unidad_profundidad} -> Estandarizada: {unidad_std}")
        print(f"Rango: {start} a {stop} ({unidad_std})")
        print(f"Step: {step} ({unidad_std})")

        #listar curvas disponibles
        print("\nCurvas disponibles:")
        for curve in las.curves:
            break
            print(curve)
            print(f"{curve.mnemonic:<10} : {curve.unit:<5} : {curve.descr}")

        #Convertir a Dataframe (Pandas)
        df = las.df()
        print("\nDataFrame:")
        print(df.head())

        #Verificar valores nulos
        print("\nValores nulos:")
        print(df.isnull().sum())

        return df
    except Exception as e:
        raise
        print(f"Error al inspeccionar el archivo LAS: {e}")
        return None

def calcular_vsh(df):
    print(f"\n Cálculo de VSH (Gamma Ray)")
    #1 Verificar si existe la curva de Gamma Ray (GR)
    if 'GR' not in df.columns:
        print("Error: No se encontró la curva GR (Gamma Ray)")
        return df
    #2 Limpieza para estadística
    gr_clean = df['GR'].dropna() #sin borrar filas del dataframe original
    #3 Calcular estadísticas
    # P5 (5%) = Arena Limpia (Clean Sand)
    # P95 (95%) = Arcilla (Shale)
    # Usamos percentiles para evitar que un error de lectura (0 o 9999) dañe el cálculo
    gr_min = np.percentile(gr_clean, 5)
    gr_max = np.percentile(gr_clean, 95)
    
    print(f"Estadísticas del Pozo")
    print(f"  > GR Sand (P5):  {gr_min:.2f} gAPI".replace('.', ','))
    print(f"  > GR Shale (P95): {gr_max:.2f} gAPI".replace('.', ','))

    #4 Calcular VSH Vectorizado
    # Lineal:
    vsh_linear = (df['GR'] - gr_min) / (gr_max - gr_min)
    
    #5 Clamping
    df['VSH'] = np.clip(vsh_linear, 0, 1)

    return df

if __name__ == "__main__":
    #Ejemplo de uso
    # 1. Obtener la ruta donde vive ESTE script (las_inspect.py)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Construir la ruta hacia la data (subir uno, entrar a LAS_data)
    # Explicación: '..' sube un nivel
    las_folder = os.path.join(script_dir, '..', 'LAS_data')
    
    # 3. Pedir solo el nombre del archivo
    archivo_nombre = input("Nombre del archivo (ej: pozo1.las): ")
    
    # 4. Unir todo
    ruta_completa = os.path.join(las_folder, archivo_nombre)
    
    print(f"Buscando en: {ruta_completa}")
    
    # Llamar a la función
    df = inspeccionar_las(ruta_completa)

    if df is not None:
        # --- CÁLCULO DE ARCILLOSIDAD ---
        df = calcular_vsh(df)
        
        print("\n--- RESULTADOS (Muestra de 10 datos) ---")
        # Mostramos solo donde hay datos (dropna) para no ver puros NaNs del inicio
        print(df[['GR', 'VSH']].dropna().head(10))
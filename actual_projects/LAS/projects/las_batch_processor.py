import os
import pandas as pd
import numpy as np
import glob
import time

# Usamos los nombres estándar de tus archivos
from las_inspect import inspeccionar_las, calcular_vsh, normalizar_porosidad, calcular_sw
from las_visualizer import graficar_quad_combo

# --- CONFIGURACIÓN DE RUTAS ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join(SCRIPT_DIR, '..', 'LAS_data') 
OUTPUT_BASE = os.path.join(SCRIPT_DIR, '..', 'Resultados_Fase4_PayZone') # Carpeta nueva
IMG_FOLDER = os.path.join(OUTPUT_BASE, 'Plots')
EXCEL_FOLDER = os.path.join(OUTPUT_BASE, 'Tablas')

def setup_folders():
    for folder in [OUTPUT_BASE, IMG_FOLDER, EXCEL_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)

def procesar_lote(matriz_rho=2.65, cutoff_vsh=0.5, cutoff_phi=8.0, 
                 rw=0.05, a=1, m=2, n=2, cutoff_sw=0.5):
    
    setup_folders()
    
    patron = os.path.join(INPUT_FOLDER, "*.las")
    archivos = glob.glob(patron)
    
    print(f"\n--- INICIANDO PROCESAMIENTO (CÁLCULO EN PAY ZONE) ---")
    print(f"Archivos: {len(archivos)}")
    print(f"Criterios Pay: Vsh<{cutoff_vsh} | Phi>{cutoff_phi}% | Sw<{cutoff_sw}")
    
    resumen_pozos = []
    start_time = time.time()

    for i, ruta_las in enumerate(archivos):
        nombre_archivo = os.path.basename(ruta_las)
        nombre_pozo = os.path.splitext(nombre_archivo)[0]
        
        print(f"\n[{i+1}/{len(archivos)}] Procesando: {nombre_pozo}...")
        
        # 1. Carga (Normalizada a Metros)
        df = inspeccionar_las(ruta_las)
        
        if df is None or df.empty:
            continue
            
        try:
            # 2. Cálculos Petrofísicos
            df = calcular_vsh(df)

            # --- NUEVO: FILTRO DE CALIDAD ---
            # Asumimos Bit Size 8.5" estándar, o podrías pedirlo como parámetro global
            from las_inspect import aplicar_filtro_calidad # Recuerda importarlo arriba
            df = aplicar_filtro_calidad(df, bit_size=8.5) 
            # --------------------------------

            df = normalizar_porosidad(df, rho_matrix=matriz_rho)
            df = calcular_sw(df, a=a, m=m, n=n, rw=rw)
            
            # 3. Detectar STEP (Metros)
            if len(df) > 1:
                step_val = pd.Series(df.index).diff().abs().median()
                if np.isnan(step_val) or step_val == 0:
                    step_val = 0.1524 
            else:
                step_val = 0

            # 4. Generar Gráfico
            ruta_imagen = os.path.join(IMG_FOLDER, f"{nombre_pozo}_Eval.png")
            graficar_quad_combo(df, nombre_pozo=nombre_pozo, guardar=True, ruta_salida=ruta_imagen)
            
            # 5. Estadísticas Avanzadas (PAY ZONE)
            top_depth = df.index.min()
            bottom_depth = df.index.max()
            
            net_pay_thk = 0
            phi_pay_mean = np.nan # Inicializamos en NaN por si el pozo es seco
            sw_pay_mean  = np.nan
            vsh_pay_mean = np.nan
            
            if {'VSH', 'DPHI_FINAL', 'SW'}.issubset(df.columns):
                # Máscara Lógica de PAY (Cumple TODO)
                mask_pay = (
                    (df['VSH'] < cutoff_vsh) & 
                    (df['DPHI_FINAL'] >= cutoff_phi) & 
                    (df['SW'] < cutoff_sw)
                )
                
                # Espesor Neto
                count_pay = mask_pay.sum()
                net_pay_thk = count_pay * step_val
                
                # --- CORRECCIÓN CRÍTICA: Promedios solo donde mask_pay es True ---
                if count_pay > 0:
                    phi_pay_mean = df.loc[mask_pay, 'DPHI_FINAL'].mean()
                    sw_pay_mean  = df.loc[mask_pay, 'SW'].mean()
                    vsh_pay_mean = df.loc[mask_pay, 'VSH'].mean()
            
            # Guardar datos
            resumen_pozos.append({
                'Pozo': nombre_pozo,
                'Net_Pay_m': round(net_pay_thk, 2),
                'Phi_Pay_Avg_%': round(phi_pay_mean, 2) if not np.isnan(phi_pay_mean) else 0,
                'Sw_Pay_Avg_Frac': round(sw_pay_mean, 3) if not np.isnan(sw_pay_mean) else 1.0,
                'Vsh_Pay_Avg_Frac': round(vsh_pay_mean, 3) if not np.isnan(vsh_pay_mean) else None,
                'Tope_m': round(top_depth, 2),
                'Base_m': round(bottom_depth, 2),
                'Status': 'OK'
            })
            
        except Exception as e:
            print(f"   ❌ Error lógica interna: {e}")
            resumen_pozos.append({'Pozo': nombre_pozo, 'Status': f'Error: {str(e)}'})

    # 6. Exportar CSV
    if resumen_pozos:
        df_resumen = pd.DataFrame(resumen_pozos)
        
        # Ordenar columnas (Las más importantes primero)
        cols_order = ['Pozo', 'Status', 'Net_Pay_m', 'Phi_Pay_Avg_%', 'Sw_Pay_Avg_Frac', 'Vsh_Pay_Avg_Frac', 'Tope_m', 'Base_m']
        final_cols = [c for c in cols_order if c in df_resumen.columns]
        df_resumen = df_resumen[final_cols]
        
        # Ranking
        if 'Net_Pay_m' in df_resumen.columns:
            df_resumen.sort_values(by='Net_Pay_m', ascending=False, inplace=True)

        ruta_csv = os.path.join(EXCEL_FOLDER, "Resumen_Reservas_PayZone.csv")
        df_resumen.to_csv(ruta_csv, index=False, encoding='utf-8-sig')
        
        print(f"\n--- PROCESO FINALIZADO ---")
        print(f"Tiempo: {time.time() - start_time:.2f} s")
        print(f"📊 CSV de Reservas: {ruta_csv}")
    else:
        print("\nNo se generaron resultados.")

# --- ENTRY POINT ---
if __name__ == "__main__":
    print("--- EVALUACIÓN DE RESERVAS (NET PAY STATISTICS) ---")
    
    # Defaults rápidos
    try:
        rho_ma = float(input("1. Densidad Matriz (Enter=2.65): ").strip() or 2.65)
        rw_val = float(input("2. Rw (Enter=0.05): ").strip() or 0.05)
        # Cutoffs
        cut_phi = float(input("3. Cutoff Porosidad % (Enter=8.0): ").strip() or 8.0)
        cut_sw  = float(input("4. Cutoff Sw (Enter=0.5): ").strip() or 0.5)
    except:
        rho_ma, rw_val, cut_phi, cut_sw = 2.65, 0.05, 8.0, 0.5

    procesar_lote(matriz_rho=rho_ma, rw=rw_val, cutoff_phi=cut_phi, cutoff_sw=cut_sw)
import os
import pandas as pd
import numpy as np
import glob
import time

# Usamos los nombres estándar de tus archivos
from las_inspect import inspeccionar_las, calcular_vsh, normalizar_porosidad, calcular_sw, obtener_curva, aplicar_filtro_calidad
from las_visualizer import graficar_quad_combo

# --- CONFIGURACIÓN DE RUTAS ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join(SCRIPT_DIR, '..', 'LAS_data') 
OUTPUT_BASE = os.path.join(SCRIPT_DIR, '..', 'Resultados_Fase 5: HCPV') # Carpeta nueva
IMG_FOLDER = os.path.join(OUTPUT_BASE, 'Plots')
EXCEL_FOLDER = os.path.join(OUTPUT_BASE, 'Tablas')

def setup_folders():
    for folder in [OUTPUT_BASE, IMG_FOLDER, EXCEL_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)

def procesar_lote(matriz_rho=None, cutoff_vsh=0.5, cutoff_phi=8.0, 
                rw=0.05, a=1, m=2, n=2, cutoff_sw=0.5,
                cutoff_dn_sep=15.0, # <--- 15% por defecto
                r_shale=2.0, # <--- Simandoux
                gr_sand=None, gr_shale=None): # <--- Normalización de Campo
    
    setup_folders()
    
    # Mensaje sobre modo de densidad
    rho_mode_str = f"Fijo ({matriz_rho} g/cc)" if matriz_rho else "AUTO (Basado en PEF)"
    
    patron = os.path.join(INPUT_FOLDER, "*.las")
    archivos = glob.glob(patron)
    
    print(f"\n--- INICIANDO PROCESAMIENTO (CÁLCULO EN PAY ZONE) ---")
    print(f"Archivos: {len(archivos)}")
    print(f"Rho Matriz: {rho_mode_str}")
    print(f"Modelo Sw: Simandoux (R_Shale={r_shale})")
    if gr_sand and gr_shale:
        print(f"Normalización Vsh: Campo (Sand={gr_sand}, Shale={gr_shale})")
    else:
        print(f"Normalización Vsh: Estadística por Pozo (P05-P95)")
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
            
            # A) Primero: Vshale
            df = calcular_vsh(df, gr_sand=gr_sand, gr_shale=gr_shale)

            # B) Segundo: Determinar Densidad Matriz y Calcular Porosidad (DPHI_FINAL)
            # --- LÓGICA RHO MATRIX INTELIGENTE ---
            rho_final = 2.65 
            if matriz_rho is not None:
                rho_final = float(matriz_rho)
            else:
                # AUTO MODE: Detectar por PEF
                try:
                    pef_curve = obtener_curva(df, 'PEF')
                    if not pef_curve.isna().all():
                        pef_mean = pef_curve.mean()
                        if pef_mean < 2.5:
                            rho_final = 2.65
                            print(f"   -> Auto Rho: 2.65 (Sandstone, PEF={pef_mean:.2f})")
                        elif pef_mean > 4.0:
                            rho_final = 2.71
                            print(f"   -> Auto Rho: 2.71 (Limestone, PEF={pef_mean:.2f})")
                        else:
                            rho_final = 2.85
                            print(f"   -> Auto Rho: 2.85 (Dolomite/Mix, PEF={pef_mean:.2f})")
                    else:
                        print("   -> Auto Rho: 2.65 (Default, sin PEF)")
                except:
                    print("   -> Auto Rho: 2.65 (Error detección)")

            # AHORA calculamos las curvas de porosidad
            df = normalizar_porosidad(df, rho_matrix=rho_final, usar_pef=True)

            # C) Tercero: AHORA aplicamos el Filtro de Calidad
            # Como DPHI_FINAL ya existe, el filtro >35% funcionará y eliminará la basura.
            df = aplicar_filtro_calidad(df, bit_size=8.5) 

            # D) Cuarto: Finalmente calculamos Sw (con datos limpios)
            df = calcular_sw(df, a=a, m=m, n=n, rw=rw, modelo='simandoux', r_shale=r_shale)
            
            # 3. Detectar STEP (Metros)
            if len(df) > 1:
                step_val = pd.Series(df.index).diff().abs().median()
                if np.isnan(step_val) or step_val == 0:
                    step_val = 0.1524 
            else:
                step_val = 0

            # 4. Estadísticas Avanzadas (PAY ZONE) -> Se mueve ANTES de graficar
            top_depth = df.index.min()
            bottom_depth = df.index.max()
            
            net_pay_thk = 0
            phi_pay_mean = np.nan # Inicializamos en NaN por si el pozo es seco
            sw_pay_mean  = np.nan
            vsh_pay_mean = np.nan
            
            if {'VSH', 'DPHI_FINAL', 'SW'}.issubset(df.columns):
                # Máscara Lógica de PAY (Cumple TODO)
                if 'NPHI_FINAL' in df.columns:
                    phi_para_corte = (df['DPHI_FINAL'] + df['NPHI_FINAL']) / 2
                else:
                    phi_para_corte = df['DPHI_FINAL']

                # --- NUEVO: MÁSCARA DE EFECTO ARCILLA (DN SEPARATION) ---
                # Si NPHI es 15% mayor que DPHI, es arcilla, no Pay.
                # (Ej. Pozo 31_2-19 S: N=29%, D=5% -> Sep=24% -> ELIMINADO)
                if 'DN_SEP' in df.columns:
                    mask_bad_litho = df['DN_SEP'] > cutoff_dn_sep
                else:
                    mask_bad_litho = False

                # --- MÁSCARA LÓGICA DE PAY (ACTUALIZADA) ---
                mask_pay = (
                    (df['VSH'] < cutoff_vsh) & 
                    (phi_para_corte >= cutoff_phi) & 
                    (df['SW'] < cutoff_sw) &
                    (~mask_bad_litho) # <--- APLICAMOS EL FILTRO AQUÍ
                )
                
                # Espesor Neto
                count_pay = mask_pay.sum()
                net_pay_thk = count_pay * step_val
                
                # --- CORRECCIÓN CRÍTICA: Promedios solo donde mask_pay es True ---
                if count_pay > 0:
                    # CORRECCIÓN: Usar 'phi_para_corte' (Promedio) en lugar de 'DPHI_FINAL'
                    phi_pay_mean = phi_para_corte[mask_pay].mean() 
                    
                    sw_pay_mean  = df.loc[mask_pay, 'SW'].mean()
                    vsh_pay_mean = df.loc[mask_pay, 'VSH'].mean()

                    # --- NUEVO: CÁLCULO DE HCPV (VOLUMEN DE HIDROCARBURO) ---
                    # Fórmula: Espesor * Porosidad * (1 - Sw)
                    # Ojo: phi_pay_mean está en % (ej. 24.5), hay que dividir entre 100.
                    hcpv_val = net_pay_thk * (phi_pay_mean / 100) * (1 - sw_pay_mean)
                else:
                    hcpv_val = 0

            # Preparar diccionario de stats para pasar al visualizador
            stats_dict = {
                'Net_Pay_m': round(net_pay_thk, 2),
                'HCPV_m':    round(hcpv_val, 2),
                'Phi_Pay_Avg_%': round(phi_pay_mean, 2) if not np.isnan(phi_pay_mean) else 0,
                'Sw_Pay_Avg_Frac': round(sw_pay_mean, 3) if not np.isnan(sw_pay_mean) else 1.0,
                'Vsh_Pay_Avg_Frac': round(vsh_pay_mean, 3) if not np.isnan(vsh_pay_mean) else None
            }

            # 5. Generar Gráfico (Ahora con stats)
            ruta_imagen = os.path.join(IMG_FOLDER, f"{nombre_pozo}_Eval.png")
            graficar_quad_combo(df, nombre_pozo=nombre_pozo, guardar=True, 
                    ruta_salida=ruta_imagen, pay_stats=stats_dict,
                    cut_vsh=cutoff_vsh, cut_phi=cutoff_phi, cut_sw=cutoff_sw)
            
            # Guardar datos
            resumen_pozos.append({
                'Pozo': nombre_pozo,
                'Net_Pay_m': round(net_pay_thk, 2),
                'HCPV_m':    round(hcpv_val, 2),
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
        cols_order = ['Pozo', 'Status', 'Net_Pay_m', 'HCPV_m', 'Phi_Pay_Avg_%', 'Sw_Pay_Avg_Frac', 'Vsh_Pay_Avg_Frac', 'Tope_m', 'Base_m']
        final_cols = [c for c in cols_order if c in df_resumen.columns]
        df_resumen = df_resumen[final_cols]
        
        # Ranking
        if 'HCPV_m' in df_resumen.columns:
            df_resumen.sort_values(by='HCPV_m', ascending=False, inplace=True)
        elif 'Net_Pay_m' in df_resumen.columns:
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
        rho_in = input("1. Densidad Matriz [Enter=AUTO/PEF o Valor]: ").strip()
        rho_ma = float(rho_in) if rho_in else None # None activa el modo Auto
        
        rw_val = float(input("2. Rw (Enter=0.05): ").strip() or 0.05)
        
        # Nuevos inputs
        print("--- Parámetros Simandoux ---")
        r_shale_val = float(input("3. R_Shale (Enter=2.0): ").strip() or 2.0)
        
        print("--- Normalización Vsh (Opcional) ---")
        use_field = input("4. ¿Usar GR Fijo de Campo? [s/N]: ").lower().startswith('s')
        gr_sand_val, gr_shale_val = None, None
        if use_field:
            gr_sand_val = float(input("   -> GR Sand: ").strip())
            gr_shale_val = float(input("   -> GR Shale: ").strip())

        # Cutoffs
        print("--- Cutoffs Pay Zone ---")
        cut_phi = float(input("5. Cutoff Porosidad % (Enter=8.0): ").strip() or 8.0)
        cut_sw  = float(input("6. Cutoff Sw (Enter=0.5): ").strip() or 0.5)
    except:
        rho_ma, rw_val, r_shale_val = 2.65, 0.05, 2.0
        gr_sand_val, gr_shale_val = None, None
        cut_phi, cut_sw = 8.0, 0.5

    procesar_lote(matriz_rho=rho_ma, rw=rw_val, cutoff_phi=cut_phi, cutoff_sw=cut_sw,
                  r_shale=r_shale_val, gr_sand=gr_sand_val, gr_shale=gr_shale_val)
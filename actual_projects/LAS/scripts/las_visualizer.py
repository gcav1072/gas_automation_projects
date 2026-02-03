import matplotlib.pyplot as plt
import os
import numpy as np
import pandas as pd
from las_inspect import obtener_curva, inspeccionar_las, calcular_vsh, normalizar_porosidad, calcular_sw, aplicar_filtro_calidad

def graficar_quad_combo(df, nombre_pozo="Pozo Desconocido", guardar=False, ruta_salida=None, pay_stats=None):
    fig, ax = plt.subplots(nrows=1, ncols=4, figsize=(14, 8), sharey=True)

    depth = df.index
    gr    = obtener_curva(df, 'GR')
    res_d = obtener_curva(df, 'RDEP')
    cal   = obtener_curva(df, 'CALI')
    
    # -------------------------------------------------------------------------
    # TRACK 1: LITOLOGÍA (GR + CALIPER)
    # -------------------------------------------------------------------------
    if not gr.isna().all():
        ax[0].plot(gr, depth, color='green', linewidth=0.5, label='GR')
        ax[0].set_xlim(0, 150)
        # Sombreado litológico simple
        ax[0].fill_betweenx(depth, gr, 150, where=(gr < 60), color='gold', alpha=0.2, label='Sand Potential')
        ax[0].fill_betweenx(depth, gr, 0, where=(gr > 100), color='black', alpha=0.1)

    if not cal.isna().all():
        ax0_cal = ax[0].twiny()
        ax0_cal.plot(cal, depth, color='black', linestyle='--', linewidth=0.8, label='CALI')
        ax0_cal.set_xlim(6, 26)
        ax0_cal.spines['top'].set_position(('outward', 10))
        ax0_cal.set_xlabel("Caliper (in)", color='black', fontsize=7)

    ax[0].set_xlabel("Gamma Ray [gAPI]", color='green', fontsize=9)
    ax[0].set_ylabel("Profundidad (m)", fontsize=10, fontweight='bold')
    ax[0].grid(True, which='major', alpha=0.3)

    # -------------------------------------------------------------------------
    # TRACK 2: RESISTIVIDAD
    # -------------------------------------------------------------------------
    if not res_d.isna().all():
        valid = res_d[res_d > 0]
        if not valid.empty:
            ax[1].semilogx(valid, valid.index, color='red', linewidth=1, label='RDeep')
            
    ax[1].set_xlim(0.2, 2000)
    ax[1].set_xlabel("Resistividad (ohm.m)", fontsize=9)
    ax[1].grid(True, which='both', alpha=0.3)

    # -------------------------------------------------------------------------
    # TRACK 3: POROSIDAD
    # -------------------------------------------------------------------------
    ax[2].set_xlim(45, -15) 
    if 'NPHI_FINAL' in df.columns:
        ax[2].plot(df['NPHI_FINAL'], depth, color='blue', linestyle='--', linewidth=0.8, label='NPHI')
    if 'DPHI_FINAL' in df.columns:
        ax[2].plot(df['DPHI_FINAL'], depth, color='red', linewidth=0.8, label='DPHI')
        
    # Sombreado de Crossover (Gas/Limpio)
    if 'NPHI_FINAL' in df.columns and 'DPHI_FINAL' in df.columns:
        ax[2].fill_betweenx(depth, df['NPHI_FINAL'], df['DPHI_FINAL'], 
                            where=(df['DPHI_FINAL'] > df['NPHI_FINAL']), 
                            color='yellow', alpha=0.6, label='X-Over')
    
    ax[2].set_xlabel("Porosidad (%)", fontsize=9)
    ax[2].grid(True, alpha=0.3)
    ax[2].legend(loc='upper right', fontsize='x-small')

    # -------------------------------------------------------------------------
    # TRACK 4: PAY ZONE (Corregido: Solo pinta si cumple criterios)
    # -------------------------------------------------------------------------
    ax[3].set_xlim(1.0, 0.0)
    
    if 'SW' in df.columns:
        sw_valid = df['SW'].dropna()
        ax[3].plot(sw_valid, sw_valid.index, color='black', linewidth=1.0, label='Sw')
        
        # --- LÓGICA DE RECONSTRUCCIÓN VISUAL DE PAY ---
        # Recalculamos la máscara aquí para pintarla (o usamos una pasada si existiera)
        # Esto asegura que lo que ves en verde ES lo que sumó metros.
        
        is_pay = pd.Series(False, index=df.index)
        
        # Intentamos replicar criterios estándar o usar columnas pre-calculadas si existieran
        # Para visualización genérica, usamos criterios medios, PERO si pasaste stats,
        # intentamos ser consistentes.
        
        # Recuperamos curvas críticas
        vsh = df['VSH'] if 'VSH' in df.columns else pd.Series(0, index=df.index)
        
        # Definimos cutoffs visuales (Deben coincidir con tu batch processor)
        v_cut_vsh = 0.4    # Un poco más estricto visualmente
        v_cut_sw = 0.5
        v_cut_phi = 8.0
        
        # Phi promedio
        if 'NPHI_FINAL' in df.columns and 'DPHI_FINAL' in df.columns:
            phi_avg = (df['DPHI_FINAL'] + df['NPHI_FINAL']) / 2
        elif 'DPHI_FINAL' in df.columns:
            phi_avg = df['DPHI_FINAL']
        else:
            phi_avg = pd.Series(0, index=df.index)

        # Máscara
        mask_pay_visual = (vsh < v_cut_vsh) & (phi_avg >= v_cut_phi) & (df['SW'] < v_cut_sw)
        
        # PINTAR PAY: Rellenamos de verde SOLO donde es Pay real
        # Usamos 'where' para filtrar el llenado
        ax[3].fill_betweenx(depth, df['SW'], 1.0, 
                           where=mask_pay_visual, 
                           color='lime', alpha=0.5, label='NET PAY')
        
        # Pintar Agua (Azul) para contraste
        ax[3].fill_betweenx(depth, df['SW'], 0.0, 
                           where=(df['SW'] > v_cut_sw), 
                           color='blue', alpha=0.1)

    ax[3].set_xlabel("Sw (v/v)", fontsize=9, color='blue')
    ax[3].grid(True, alpha=0.3)
    ax[3].legend(loc='upper right', fontsize='x-small')

    # -------------------------------------------------------------------------
    # BAD HOLE FLAG
    # -------------------------------------------------------------------------
    if 'BAD_HOLE' in df.columns:
        for axis in ax:
            axis.fill_betweenx(depth, 0, 1, where=df['BAD_HOLE'], 
                                transform=axis.get_xaxis_transform(), 
                                color='gray', alpha=0.5, zorder=10)

    # Ajustes finales
    ax[0].invert_yaxis()
    plt.suptitle(f"Evaluación QC: {nombre_pozo}", fontsize=14, y=0.98)
    
    # Mostrar Estadísticas
    if pay_stats:
        stats_text = (
            f"Net Pay: {pay_stats.get('Net_Pay_m', 0)} m\n"
            f"Phi Avg: {pay_stats.get('Phi_Pay_Avg_%', 0)} %\n"
            f"Sw Avg: {pay_stats.get('Sw_Pay_Avg_Frac', 1.0)} v/v"
        )
        plt.figtext(0.02, 0.95, stats_text, fontsize=9, ha='left', va='top', 
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.tight_layout()
    plt.subplots_adjust(top=0.88)
    
    if guardar and ruta_salida:
        plt.savefig(ruta_salida, dpi=100)
        plt.close(fig)
    else:
        plt.show()

# --- BLOQUE MAIN INTERACTIVO ---
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    las_folder = os.path.join(script_dir, '..', 'LAS_data')
    
    print("\n--- VISUALIZADOR QC (Con Filtro de Derrumbe) ---")
    archivo_nombre = input("Nombre del archivo (ej: 25_4-5.las): ").strip()
    ruta_completa = os.path.join(las_folder, archivo_nombre)
    
    if os.path.exists(ruta_completa):
        # 1. Parámetros
        try:
            bs_in = input("Bit Size (pulgadas) [Enter=8.5]: ").strip()
            bs = float(bs_in) if bs_in else 8.5
            
            rw_in = input("Rw (Resistividad Agua) [Enter=0.05]: ").strip()
            rw_val = float(rw_in) if rw_in else 0.05
            
            m_in = input("m (Exponente Cementación) [Enter=2.0]: ").strip()
            m_val = float(m_in) if m_in else 2.0
        except: 
            bs, rw_val, m_val = 8.5, 0.05, 2.0
            
        # 2. Proceso
        df = inspeccionar_las(ruta_completa)
        df = calcular_vsh(df)
        df = aplicar_filtro_calidad(df, bit_size=bs) # <--- AQUÍ FILTRAMOS
        df = normalizar_porosidad(df)
        df = calcular_sw(df, rw=rw_val, m=m_val)
        
        # 3. Calcular Net Pay y Estadísticas (Lógica copiada de las_batch_processor.py)
        
        # Inputs de Cutoff
        try:
            cut_vsh = float(input("Cutoff Vsh [Enter=0.5]: ").strip() or 0.5)
            cut_phi = float(input("Cutoff Phi % [Enter=8.0]: ").strip() or 8.0)
            cut_sw  = float(input("Cutoff Sw [Enter=0.5]: ").strip() or 0.5)
        except:
            cut_vsh, cut_phi, cut_sw = 0.5, 8.0, 0.5
        
        print(f"\nCalculando Pay Zone (Vsh<{cut_vsh}, Phi>{cut_phi}%, Sw<{cut_sw})...")

        # Detectar STEP
        if len(df) > 1:
            step_val = pd.Series(df.index).diff().abs().median()
            if np.isnan(step_val) or step_val == 0:
                step_val = 0.1524 
        else:
            step_val = 0

        # Lógica de Pay
        net_pay_thk = 0
        phi_pay_mean = np.nan
        sw_pay_mean  = np.nan
        vsh_pay_mean = np.nan
        
        if {'VSH', 'DPHI_FINAL', 'SW'}.issubset(df.columns):
            # Porosidad Promedio para corte
            if 'NPHI_FINAL' in df.columns:
                phi_para_corte = (df['DPHI_FINAL'] + df['NPHI_FINAL']) / 2
            else:
                phi_para_corte = df['DPHI_FINAL']

            # Máscara Bad Litho (DN Separation > 15%)
            mask_bad_litho = False
            cutoff_dn_sep = 15.0 # Mismo default que batch processor
            if 'DN_SEP' in df.columns:
                mask_bad_litho = df['DN_SEP'] > cutoff_dn_sep
            
            # Máscara Pay
            mask_pay = (
                (df['VSH'] < cut_vsh) & 
                (phi_para_corte >= cut_phi) & 
                (df['SW'] < cut_sw) &
                (~mask_bad_litho)
            )
            
            # Espesor
            count_pay = mask_pay.sum()
            net_pay_thk = count_pay * step_val
            
            # Promedios
            if count_pay > 0:
                phi_pay_mean = phi_para_corte[mask_pay].mean()
                sw_pay_mean  = df.loc[mask_pay, 'SW'].mean()
                vsh_pay_mean = df.loc[mask_pay, 'VSH'].mean()

        # Preparar diccionario de stats
        stats = {
            'Net_Pay_m': round(net_pay_thk, 2),
            'Phi_Pay_Avg_%': round(phi_pay_mean, 2) if not np.isnan(phi_pay_mean) else 0,
            'Sw_Pay_Avg_Frac': round(sw_pay_mean, 3) if not np.isnan(sw_pay_mean) else 1.0,
            'Vsh_Pay_Avg_Frac': round(vsh_pay_mean, 3) if not np.isnan(vsh_pay_mean) else None
        }
        
        print(f"Resultados: Pay={stats['Net_Pay_m']}m, Phi={stats['Phi_Pay_Avg_%']}%, Sw={stats['Sw_Pay_Avg_Frac']}")

        # 4. Graficar
        print("Generando gráfico...")
        graficar_quad_combo(df, nombre_pozo=archivo_nombre, guardar=False, pay_stats=stats)
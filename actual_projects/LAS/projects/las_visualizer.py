import matplotlib.pyplot as plt
import os
import numpy as np
from las_inspect import obtener_curva, inspeccionar_las, calcular_vsh, normalizar_porosidad, calcular_sw, aplicar_filtro_calidad

def graficar_quad_combo(df, nombre_pozo="Pozo Desconocido", guardar=False, ruta_salida=None):
    fig, ax = plt.subplots(nrows=1, ncols=4, figsize=(14, 8), sharey=True)

    depth = df.index
    gr    = obtener_curva(df, 'GR')
    res_d = obtener_curva(df, 'RDEP')
    cal   = obtener_curva(df, 'CALI') # Traemos Caliper para dibujar
    
    # -------------------------------------------------------------------------
    # TRACK 1: LITOLOGÍA + CALIPER
    # -------------------------------------------------------------------------
    if not gr.isna().all():
        ax[0].plot(gr, depth, color='green', linewidth=0.5, label='GR')
        ax[0].set_xlim(0, 150)
        ax[0].fill_betweenx(depth, gr, 75, where=(gr < 75), color='gold', alpha=0.4)
        ax[0].fill_betweenx(depth, gr, 75, where=(gr >= 75), color='darkgreen', alpha=0.4)
    
    # Graficar Caliper (Eje superior)
    if not cal.isna().all():
        ax0_cal = ax[0].twiny()
        ax0_cal.plot(cal, depth, color='black', linestyle='--', linewidth=0.8, label='CALI')
        ax0_cal.set_xlim(6, 26) # Escala típica de caliper (6 a 26 pulgadas)
        ax0_cal.set_xlabel("Caliper (in)", color='black', fontsize=8)
        ax0_cal.spines['top'].set_position(('outward', 10))

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
        ax[2].plot(df['NPHI_FINAL'], depth, color='blue', linestyle='--', linewidth=0.8)
    if 'DPHI_FINAL' in df.columns:
        ax[2].plot(df['DPHI_FINAL'], depth, color='red', linewidth=0.8)
    if 'NPHI_FINAL' in df.columns and 'DPHI_FINAL' in df.columns:
        ax[2].fill_betweenx(depth, df['NPHI_FINAL'], df['DPHI_FINAL'], 
                            where=(df['DPHI_FINAL'] > df['NPHI_FINAL']), color='yellow', alpha=0.6)
    
    ax[2].set_xlabel("Porosidad (%)", fontsize=9)
    ax[2].grid(True, alpha=0.3)

    # -------------------------------------------------------------------------
    # TRACK 4: SATURACIÓN
    # -------------------------------------------------------------------------
    ax[3].set_xlim(1.0, 0.0)
    if 'SW' in df.columns:
        # Filtramos nulos para que no se rompa el plot
        sw_valid = df['SW'].dropna()
        ax[3].plot(sw_valid, sw_valid.index, color='black', linewidth=1.0)
        ax[3].fill_betweenx(sw_valid.index, sw_valid, 1.0, color='green', alpha=0.3)
        ax[3].axvline(x=0.5, color='gray', linestyle=':', linewidth=0.8)

    ax[3].set_xlabel("Sw (v/v)", fontsize=9, color='blue')
    ax[3].grid(True, alpha=0.3)

    # -------------------------------------------------------------------------
    # BAD HOLE FLAG (Sombreado Gris)
    # -------------------------------------------------------------------------
    if 'BAD_HOLE' in df.columns:
        # Usamos fill_betweenx para pintar franjas grises donde BAD_HOLE es True
        # Lo aplicamos en todos los ejes para que sea evidente
        for axis in ax:
            axis.fill_betweenx(depth, 0, 1, where=df['BAD_HOLE'], 
                               transform=axis.get_xaxis_transform(), 
                               color='gray', alpha=0.5, zorder=0)

    # Ajustes finales
    ax[0].invert_yaxis()
    plt.suptitle(f"Evaluación QC: {nombre_pozo}", fontsize=14, y=0.98)
    plt.subplots_adjust(top=0.88, bottom=0.08, left=0.06, right=0.98, wspace=0.15)
    
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
        except: bs = 8.5
            
        # 2. Proceso
        df = inspeccionar_las(ruta_completa)
        df = calcular_vsh(df)
        df = aplicar_filtro_calidad(df, bit_size=bs) # <--- AQUÍ FILTRAMOS
        df = normalizar_porosidad(df)
        df = calcular_sw(df)
        
        # 3. Graficar
        print("Generando gráfico...")
        graficar_quad_combo(df, nombre_pozo=archivo_nombre, guardar=False)
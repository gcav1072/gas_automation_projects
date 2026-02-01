import matplotlib.pyplot as plt
import os
import numpy as np
# IMPORTANTE: Traemos 'obtener_curva' del backend y quitamos 'buscar_curva'
from las_inspect import inspeccionar_las, calcular_vsh, obtener_curva, normalizar_porosidad

def graficar_triple_combo(df, nombre_pozo="Pozo Desconocido"):
    # Configuración del lienzo (3 Tracks)
    fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(10, 8), sharey=True)

    # --- ASIGNACIÓN DE VARIABLES ---
    # Extraemos Series limpias para usar directamente en el plot
    depth = df.index
    gr    = obtener_curva(df, 'GR')
    res_d = obtener_curva(df, 'RDEP')
    res_m = obtener_curva(df, 'RMED')
    # Nota: Porosidad y VSH ya vienen calculadas/normalizadas en el DF si se corrieron los pasos previos.
    # Pero para consistencia visual en Tracks 1 y 2 usamos las variables 'gr', 'res_...'.
    
    # -------------------------------------------------------------------------
    # TRACK 1: LITOLOGÍA (Gamma Ray y Vsh)
    # -------------------------------------------------------------------------
    
    if not gr.isna().all():
        ax[0].plot(gr, depth, color='green', linewidth=0.5)
        ax[0].set_xlabel("Gamma Ray [gAPI]", color='green', fontsize=10)
        ax[0].set_xlim(0, 150)

        gr_cutoff = 75 
        ax[0].plot(gr, depth, color='green', linewidth=0.5)

        # Relleno condicional:
        # 1. Relleno Amarillo (Arenas) cuando GR < Cutoff
        ax[0].fill_betweenx(depth, gr, gr_cutoff, where=(gr < gr_cutoff), 
                    interpolate=True, color='gold', alpha=0.4)

        # 2. Relleno Verde (Arcillas) cuando GR > Cutoff
        ax[0].fill_betweenx(depth, gr, gr_cutoff, where=(gr >= gr_cutoff), 
                    interpolate=True, color='darkgreen', alpha=0.4)

        ax[0].set_axisbelow(True) # Grid al fondo
    else:
        ax[0].text(0.5, 0.5, "SIN DATOS GR", ha='center', transform=ax[0].transAxes, color='red')

    if 'VSH' in df.columns:
        ax0_vsh = ax[0].twiny() 
        ax0_vsh.plot(df['VSH'], depth, color='black', linewidth=0.5)
        ax0_vsh.set_xlim(0, 1)
        ax0_vsh.fill_betweenx(depth, df['VSH'], 0, color='gray', alpha=0.5)
        ax0_vsh.spines['top'].set_position(('outward', 15))
        ax0_vsh.set_xlabel("Vsh (v/v)")
    
    ax[0].grid(True, which='major', linestyle='-', alpha=0.3)
    ax[0].set_title("Track 1: Litología")

    # -------------------------------------------------------------------------
    # TRACK 2: RESISTIVIDAD
    # -------------------------------------------------------------------------
    hay_res = False

    if not res_d.isna().all():
        # Filtramos valores <= 0 para evitar errores logarítmicos
        # Como res_d es una Serie, podemos filtrar directamente para el plot sin perder alineación de índice si usamos el índice de la serie filtrada
        rd_valid = res_d[res_d > 0]
        if not rd_valid.empty:
            ax[1].semilogx(rd_valid, rd_valid.index, 
                           color='red', linewidth=0.8, label='Res. Deep')
            hay_res = True
        
    if not res_m.isna().all():
        rm_valid = res_m[res_m > 0]
        if not rm_valid.empty:
            ax[1].semilogx(rm_valid, rm_valid.index, 
                           color='blue', linewidth=0.6, linestyle='--', label='Res. Med')
            hay_res = True

    if hay_res:
        ax[1].set_xscale('log')
        ax[1].set_xlim(0.2, 10000)
        ax[1].legend(loc='lower center', bbox_to_anchor=(0.5, 1.05), fontsize='small') 
    else:
        ax[1].text(0.5, 0.5, "SIN RESISTIVIDAD", ha='center', transform=ax[1].transAxes, color='red')
        
    ax[1].set_xlabel("Resistividad (ohm.m)")
    ax[1].grid(True, which='both', linestyle='-', alpha=0.3)
    ax[1].set_title("Track 2: Fluidos")

    # -------------------------------------------------------------------------
    # TRACK 3: POROSIDAD
    # -------------------------------------------------------------------------
    hay_porosidad = False
    
    # 1. Neutrón Final (Ya normalizado a %)
    if 'NPHI_FINAL' in df.columns:
        ax[2].plot(df['NPHI_FINAL'], depth, color='blue', linestyle='--', linewidth=0.8, label='Neutrón')
        hay_porosidad = True
    
    # 2. Densidad Final (Ya convertida a Porosidad %)
    if 'DPHI_FINAL' in df.columns:
        ax[2].plot(df['DPHI_FINAL'], depth, color='red', linewidth=0.8, label='Densidad')
        hay_porosidad = True
    
    # 3. Sombreado (Crossover)
    if 'NPHI_FINAL' in df.columns and 'DPHI_FINAL' in df.columns:
        try:
            ax[2].fill_betweenx(depth, df['NPHI_FINAL'], df['DPHI_FINAL'], 
                                where=(df['DPHI_FINAL'] > df['NPHI_FINAL']), 
                                color='yellow', alpha=0.5, label='Gas/Crossover')
        except:
            pass 

    # IMPORTANTE: Escala fija de Porosidad (45% a -15%)
    ax[2].set_xlim(45, -15) 
    ax[2].set_xlabel("Porosidad (%)")
    
    if hay_porosidad:
        ax[2].legend(loc='lower center', bbox_to_anchor=(0.5, 1.05), fontsize='small')
    else:
        ax[2].text(0.5, 0.5, "SIN DATOS POROSIDAD", ha='center', transform=ax[2].transAxes, color='red')

    ax[2].grid(True, which='both', linestyle='-', alpha=0.3)
    ax[2].set_title("Track 3: Porosidad")

    # Ajustes finales
    ax[0].invert_yaxis()
    plt.subplots_adjust(top=0.85, bottom=0.1, left=0.08, right=0.96, wspace=0.25)
    plt.suptitle(f"Triple Combo: {nombre_pozo}", fontsize=12)
    plt.show()

# --- BLOQUE MAIN ---
if __name__ == "__main__":
    # Setup de rutas
    script_dir = os.path.dirname(os.path.abspath(__file__))
    las_folder = os.path.join(script_dir, '..', 'LAS_data')
    
    archivo_nombre = input("Nombre del archivo (ej: 7_1-1.las): ")
    ruta_completa = os.path.join(las_folder, archivo_nombre)
    
    # --- NUEVO: SELECTOR DE LITOLOGÍA ---
    print("\nSeleccione la Matriz de referencia:")
    print("1. Arenisca (Sandstone) [2.65 g/cc] - (Enter por defecto)")
    print("2. Caliza (Limestone)   [2.71 g/cc]")
    print("3. Dolomía (Dolomite)   [2.87 g/cc]")
    print("4. Personalizado")
    
    opcion = input("Opción > ").strip()
    
    # Lógica de selección robusta
    if opcion == '2':
        rho_ma = 2.71
        litologia = "Caliza"
    elif opcion == '3':
        rho_ma = 2.87
        litologia = "Dolomía"
    elif opcion == '4':
        try:
            rho_ma = float(input("Introduce densidad de matriz (g/cc): "))
            litologia = f"Personalizada ({rho_ma})"
        except ValueError:
            print("Valor inválido. Se usará Arenisca (2.65).")
            rho_ma = 2.65
            litologia = "Arenisca"
    else:
        # Por defecto (Opción 1 o vacío)
        rho_ma = 2.65
        litologia = "Arenisca"

    print(f"\nProcesando '{archivo_nombre}' como litología: {litologia}...")
    
    df_pozo = inspeccionar_las(ruta_completa)
    
    if df_pozo is not None:
        # 1. Calcular Vsh
        df_calculado = calcular_vsh(df_pozo)
        
        # 2. Normalizar Porosidades (Arregla las líneas verticales)
        df_calculado = normalizar_porosidad(df_calculado, rho_matrix=rho_ma)

        # 3. Graficar
        graficar_triple_combo(df_calculado, nombre_pozo=archivo_nombre)
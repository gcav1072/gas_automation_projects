import matplotlib.pyplot as plt
import os
from las_inspect import inspeccionar_las, calcular_vsh

import matplotlib.pyplot as plt
import os

# --- IMPORTACIÓN MODULAR ---
# Aquí ocurre la magia. Traemos tus funciones desde el otro archivo.
# Nota: Esto funciona porque ambos archivos están en la misma carpeta.
from las_inspect import inspeccionar_las, calcular_vsh

import matplotlib.pyplot as plt
import pandas as pd # Necesario para manejar nulos en el relleno

# Mantén tus imports anteriores (from las_inspect...)

def graficar_triple_combo(df, nombre_pozo="Pozo Desconocido"):
    # Creamos 3 tracks compartiendo profundidad
    fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(14, 12), sharey=True)
    
    # --- TRACK 1: LITOLOGÍA (GR & Vsh) ---
    # Eje principal para GR
    ax[0].plot(df['GR'], df.index, color='green', linewidth=0.5)
    ax[0].set_xlabel("Gamma Ray (gAPI)", color='green')
    ax[0].set_xlim(0, 150)
    ax[0].fill_betweenx(df.index, df['GR'], 0, color='yellow', alpha=0.3)
    
    # Truco de Matplotlib: "Twin Axis" (Eje gemelo) para poner el Vsh en el mismo track
    ax0_vsh = ax[0].twiny() 
    ax0_vsh.plot(df['VSH'], df.index, color='black', linewidth=0.5)
    ax0_vsh.set_xlim(0, 1)
    ax0_vsh.fill_betweenx(df.index, df['VSH'], 0, color='gray', alpha=0.5)
    # Movemos la etiqueta del Vsh un poco para que no choque
    ax0_vsh.spines['top'].set_position(('outward', 40))
    ax0_vsh.set_xlabel("Vsh (v/v)", color='black')
    
    ax[0].set_title("Track 1: Litología")
    ax[0].grid(True, which='major', linestyle='-', alpha=0.3)

    # --- TRACK 2: RESISTIVIDAD (Fluidos) ---
    # ¡OJO! La resistividad SIEMPRE se grafica en escala Logarítmica
    # Usamos ILD (Inducción Profunda) e ILM (Inducción Media)
    # Si tienes valores 0 o negativos, semilogx lanzará error, filtramos visualmente con xlim
    ax[1].semilogx(df['ILD'], df.index, color='red', linewidth=0.8, label='Deep (ILD)')
    ax[1].semilogx(df['ILM'], df.index, color='blue', linewidth=0.6, linestyle='--', label='Med (ILM)')
    
    ax[1].set_xlim(0.2, 2000) # Escala estándar de 4 ciclos logarítmicos
    ax[1].set_xlabel("Resistividad (ohm.m)")
    ax[1].grid(True, which='both', linestyle='-', alpha=0.3)
    ax[1].legend(loc='upper right', fontsize='small')
    ax[1].set_title("Track 2: Fluidos")

    # --- TRACK 3: POROSIDAD (Neutrón-Densidad) ---
    # Aquí buscamos el "Crossover". 
    # Escala estándar: 45% a -15% (Invertida) para areniscas
    
    # NPLS (Neutron) - suele ser línea azul punteada
    ax[2].plot(df['NPLS'], df.index, color='blue', linestyle='--', linewidth=0.8, label='Neutrón (NPLS)')
    
    # DPLS (Densidad) - suele ser línea roja continua
    ax[2].plot(df['DPLS'], df.index, color='red', linewidth=0.8, label='Densidad (DPLS)')
    
    # Invertimos el eje X (de 60 a -15)
    ax[2].set_xlim(60, -15) 
    ax[2].set_xlabel("Porosidad (%)")
    ax[2].legend(loc='upper right', fontsize='small')
    ax[2].grid(True, which='both', linestyle='-', alpha=0.3)
    ax[2].set_title("Track 3: Porosidad")
    
    # Sombreado de Crossover (Efecto Gas): Cuando Densidad < Neutrón (visualmente se cruzan)
    # Rellenamos de amarillo donde DPLS < NPLS (o viceversa según la escala)
    # Nota: Requiere lógica cuidadosa con nulos, aquí hacemos un relleno simple visual
    ax[2].fill_betweenx(df.index, df['NPLS'], df['DPLS'], where=(df['DPLS'] > df['NPLS']), color='yellow', alpha=0.4, label='Gas/Light Oil')

    # --- AJUSTES FINALES ---
    ax[0].invert_yaxis() # Profundidad hacia abajo
    plt.suptitle(f"Triple Combo: {nombre_pozo}", fontsize=16)
    plt.tight_layout()
    plt.show()

# --- BLOQUE PRINCIPAL DE EJECUCIÓN ---
if __name__ == "__main__":
    # 1. Definir rutas (igual que hacías antes, pero ahora desde el visualizador)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    las_folder = os.path.join(script_dir, '..', 'LAS_data')
    
    # 2. Pedir archivo
    archivo_nombre = input("Nombre del archivo a visualizar (ej: KGS_1.las): ")
    ruta_completa = os.path.join(las_folder, archivo_nombre)
    
    print(f"Procesando: {ruta_completa}...")

    # 3. LLAMAR AL BACKEND
    # Paso A: Cargar y limpiar
    df_pozo = inspeccionar_las(ruta_completa)
    
    if df_pozo is not None:
        # Paso B: Calcular ingeniería (Vsh)
        df_calculado = calcular_vsh(df_pozo)
        
        # Paso C: Visualizar
        print("Generando gráficos...")
        graficar_triple_combo(df_calculado, nombre_pozo=archivo_nombre)
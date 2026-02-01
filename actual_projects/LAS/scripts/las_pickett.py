import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os

# Importamos tu "Backend Blindado"
from las_inspect import inspeccionar_las, obtener_curva, calcular_vsh, normalizar_porosidad, aplicar_filtro_calidad

def dibujar_lineas_sw(ax, phi_min, phi_max, rw, a, m, n):
    """Dibuja las líneas de referencia de Saturación de Agua (Archie)."""
    # Rango de porosidad para las líneas (0.01 a 1.0)
    phi_grid = np.logspace(np.log10(phi_min), np.log10(phi_max), 50)
    
    # Colores para las líneas de Sw: 100% (Azul), 50% (Verde), 20% (Rojo)
    niveles_sw = [1.0, 0.5, 0.2]
    colores = ['blue', 'green', 'red']
    etiquetas = ['Sw=100%', 'Sw=50%', 'Sw=20%']
    
    for sw, col, lbl in zip(niveles_sw, colores, etiquetas):
        # Ecuación de Archie despejada para Rt:
        # Rt = (a * Rw) / (Phi^m * Sw^n)
        rt_grid = (a * rw) / (np.power(phi_grid, m) * np.power(sw, n))
        
        ax.plot(phi_grid * 100, rt_grid, color=col, linestyle='--', linewidth=1.5, label=lbl, alpha=0.7)

def graficar_pickett(df, nombre_pozo, rw=0.05, a=1, m=2, n=2):
    """Genera el Pickett Plot interactivo."""
    
    # 1. Preparar Datos
    # Necesitamos Porosidad (Phi) y Resistividad Profunda (Rt)
    if 'DPHI_FINAL' not in df.columns or 'NPHI_FINAL' not in df.columns:
        print("❌ Error: Faltan curvas de porosidad. Revisa el procesamiento.")
        return

    # Calculamos porosidad promedio (igual que en tu batch processor)
    phi_pct = (df['DPHI_FINAL'] + df['NPHI_FINAL']) / 2
    rt = obtener_curva(df, 'RDEP')
    
    # 2. Filtrado Inteligente (Solo zonas limpias y válidas)
    # Pickett funciona mejor en arenas limpias (Vsh bajo)
    mask_clean = pd.Series(True, index=df.index)
    if 'VSH' in df.columns:
        mask_clean = df['VSH'] < 0.4 # Solo puntos con menos de 40% de arcilla
    
    # Filtro de validez física (Phi > 1%, Rt > 0.1)
    mask_valid = (phi_pct > 1) & (rt > 0.1) & mask_clean
    
    # Extraer puntos para graficar
    x_phi = phi_pct[mask_valid]
    y_rt = rt[mask_valid]
    
    # Color por Vsh o Gamma Ray para ver litología
    c_data = df['GR'][mask_valid] if 'GR' in df.columns else None

    # --- GRAFICAR ---
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Scatter Plot
    sc = ax.scatter(x_phi, y_rt, c=c_data, cmap='terrain_r', s=15, alpha=0.6, edgecolors='none')
    if c_data is not None:
        cbar = plt.colorbar(sc)
        cbar.set_label('Gamma Ray (API)')

    # Configurar Ejes Log-Log
    ax.set_xscale('log')
    ax.set_yscale('log')
    
    # Límites visuales (ajustables)
    ax.set_xlim(1, 100)      # Porosidad de 1% a 100%
    ax.set_ylim(0.1, 1000)   # Resistividad de 0.1 a 1000
    
    # Etiquetas y Títulos
    ax.set_xlabel('Porosidad (%) - Escala Log', fontsize=12)
    ax.set_ylabel('Resistividad Profunda (ohm.m) - Escala Log', fontsize=12)
    ax.set_title(f'Pickett Plot: {nombre_pozo}\n(Parámetros: Rw={rw}, m={m}, n={n})', fontsize=14)
    
    # DIBUJAR LÍNEAS DE ARCHIE
    dibujar_lineas_sw(ax, 0.01, 1.0, rw, a, m, n)
    
    ax.grid(True, which='both', linestyle='-', alpha=0.3)
    ax.legend(loc='upper right')
    
    print(f"Graficando {len(x_phi)} puntos filtrados (Zona Limpia)...")
    plt.show()

# --- ENTRY POINT ---
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    las_folder = os.path.join(script_dir, '..', 'LAS_data')
    
    print("\n--- HERRAMIENTA DE VALIDACIÓN: PICKETT PLOT ---")
    archivo_nombre = input("Nombre del archivo (ej: 30_3-5 S.las): ").strip()
    ruta_completa = os.path.join(las_folder, archivo_nombre)
    
    if os.path.exists(ruta_completa):
        # 1. Configuración de Archie
        try:
            rw_in = input("Rw (Resistividad Agua) [Enter=0.05]: ").strip()
            rw = float(rw_in) if rw_in else 0.05
            
            m_in = input("Exponente m (Cementación) [Enter=2.0]: ").strip()
            m = float(m_in) if m_in else 2.0
        except:
            rw, m = 0.05, 2.0
            
        # 2. Procesamiento Base
        print("Procesando y limpiando datos...")
        df = inspeccionar_las(ruta_completa)
        df = calcular_vsh(df)
        df = aplicar_filtro_calidad(df, bit_size=8.5) # ¡Importante! Usar el filtro de calidad
        df = normalizar_porosidad(df)
        
        # 3. Graficar
        graficar_pickett(df, nombre_pozo=archivo_nombre, rw=rw, a=1, m=m, n=2)
    else:
        print("Archivo no encontrado.")
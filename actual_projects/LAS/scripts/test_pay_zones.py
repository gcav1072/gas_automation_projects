import matplotlib.pyplot as plt
import numpy as np
import os
import sys

# --- IMPORTACIÓN DE TU LÓGICA EXISTENTE ---
# Aseguramos que Python encuentre tus módulos si están en la misma carpeta
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from las_inspect import (inspeccionar_las, calcular_vsh, normalizar_porosidad, 
                         calcular_sw, aplicar_filtro_calidad, obtener_curva)

def visualizar_validacion_pay(archivo_las, 
                              # Parámetros físicos
                              rho_ma=2.65, rw=0.05, a=1, m=2, n=2, bit_size=8.5,
                              # Cutoffs de Pay Zone (MISMOS QUE BATCH PROCESSOR)
                              cut_vsh=0.5, cut_phi=8.0, cut_sw=0.5, cut_dn_sep=15.0):
    
    print(f"--- Validando: {os.path.basename(archivo_las)} ---")
    
    # 1. PROCESAMIENTO IDÉNTICO AL BATCH
    # Usamos exactamente las mismas funciones para asegurar congruencia
    df = inspeccionar_las(archivo_las)
    if df is None: return

    # Pipeline de cálculo
    df = calcular_vsh(df)
    df = aplicar_filtro_calidad(df, bit_size=bit_size)
    df = normalizar_porosidad(df, rho_matrix=rho_ma)
    df = calcular_sw(df, a=a, m=m, n=n, rw=rw)

    # 2. REPLICAR LÓGICA DE PAY ZONE
    # (Copiada de las_batch_processor para exactitud visual)
    
    # a. Definir Porosidad de Corte
    if 'NPHI_FINAL' in df.columns and 'DPHI_FINAL' in df.columns:
        phi_para_corte = (df['DPHI_FINAL'] + df['NPHI_FINAL']) / 2
    elif 'DPHI_FINAL' in df.columns:
        phi_para_corte = df['DPHI_FINAL']
    else:
        phi_para_corte = df['NPHI_FINAL'] if 'NPHI_FINAL' in df.columns else None

    # b. Definir Bad Litho
    if 'DN_SEP' in df.columns:
        mask_bad_litho = df['DN_SEP'] > cut_dn_sep
    else:
        mask_bad_litho = False
        
    # c. Máscara Final
    # Validamos que existan las columnas calculadas
    if 'SW' in df.columns and 'VSH' in df.columns and phi_para_corte is not None:
        pay_flag = (
            (df['VSH'] < cut_vsh) & 
            (phi_para_corte >= cut_phi) & 
            (df['SW'] < cut_sw) & 
            (~mask_bad_litho)
        )
    else:
        print("❌ Faltan curvas calculadas para determinar Pay Zone.")
        pay_flag = np.zeros(len(df), dtype=bool)

    # --- 3. GRAFICACIÓN (Estilo Debugger) ---
    fig, ax = plt.subplots(nrows=1, ncols=5, figsize=(16, 10), sharey=True)
    fig.suptitle(f'Validación Pay Logic: {os.path.basename(archivo_las)}', fontsize=16)
    
    depth = df.index

    # TRACK 1: GR y VSH (Validar arcillosidad)
    gr = obtener_curva(df, 'GR')
    ax[0].plot(gr, depth, 'g', lw=0.5)
    ax[0].set_xlim(0, 150)
    ax[0].set_xlabel("GR (API)")
    
    # Superponemos VSH para ver si el cálculo tiene sentido
    ax0_vsh = ax[0].twiny()
    ax0_vsh.plot(df['VSH'], depth, 'k--', lw=1)
    ax0_vsh.set_xlim(0, 1)
    ax0_vsh.set_xlabel("VSH (Frac)", color='black')
    # Sombreado de Cutoff VSH
    ax0_vsh.fill_betweenx(depth, 0, 1, where=(df['VSH'] > cut_vsh), color='gray', alpha=0.3, label='Non-Res')

    # TRACK 2: Resistividad (Validar fluidos crudos)
    rt = obtener_curva(df, 'RDEP')
    ax[1].semilogx(rt, depth, 'r', lw=1)
    ax[1].set_xlim(0.2, 2000)
    ax[1].set_xlabel("Rt (ohm.m)")
    ax[1].grid(True, which='both', alpha=0.5)

    # TRACK 3: Porosidad (Validar % y cruces)
    # NOTA: Tu sistema usa PORCENTAJE (0-60), ajustamos escala aquí
    if 'NPHI_FINAL' in df.columns:
        ax[2].plot(df['NPHI_FINAL'], depth, 'b--', lw=1, label='NPHI')
    if 'DPHI_FINAL' in df.columns:
        ax[2].plot(df['DPHI_FINAL'], depth, 'r-', lw=1, label='DPHI')
    
    ax[2].set_xlim(45, -15) # Escala compatible con Porcentaje
    ax[2].set_xlabel("Porosidad (%)")
    ax[2].legend(loc='upper right', fontsize='x-small')
    ax[2].grid(True)
    # Sombrear lo que NO pasa el corte de porosidad
    if phi_para_corte is not None:
         ax[2].fill_betweenx(depth, 45, -15, where=(phi_para_corte < cut_phi), color='gray', alpha=0.3)

    # TRACK 4: Saturación de Agua (El resultado de Archie)
    if 'SW' in df.columns:
        ax[3].plot(df['SW'], depth, 'k', lw=1)
        ax[3].set_xlim(1, 0)
        ax[3].set_xlabel("SW (v/v)")
        ax[3].axvline(cut_sw, color='red', linestyle=':')
        # Sombrear agua
        ax[3].fill_betweenx(depth, 1, 0, where=(df['SW'] > cut_sw), color='blue', alpha=0.3)
        
    # TRACK 5: RESULTADO FINAL (Flag)
    ax[4].fill_betweenx(depth, 0, 1, where=pay_flag, color='gold', label='PAY')
    ax[4].set_xlim(0, 1)
    ax[4].set_xlabel("PAY FLAG")
    ax[4].set_xticks([])
    
    # Manejo de Bad Hole (QC)
    if 'BAD_HOLE' in df.columns:
         for axis in ax:
             axis.fill_betweenx(depth, 0, 1, where=df['BAD_HOLE'], 
                                transform=axis.get_xaxis_transform(), color='black', alpha=0.2)

    ax[0].invert_yaxis()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # RUTA HARDCODED PARA PRUEBA RÁPIDA O INPUT
    # ruta_defecto = 'actual_projects/LAS/LAS_data/KGS_1.las' 
    
    # Si quieres probarlo dinámicamente:
    archivo = "KGS_1.las" # Cambia esto por tu archivo
    ruta_base = os.path.join(os.path.dirname(__file__), '..', 'LAS_data', archivo)
    
    # Si no encuentra la ruta relativa, intenta ruta absoluta (ajusta según tu PC)
    if not os.path.exists(ruta_base):
        ruta_base = archivo # Asume carpeta actual
        
    visualizar_validacion_pay(ruta_base, 
                              cut_phi=8.0,  # 8% Porosidad
                              cut_sw=0.5,   # 50% Sw
                              cut_vsh=0.4,  # 40% Vshale
                              rw=0.045)     # Rw específico
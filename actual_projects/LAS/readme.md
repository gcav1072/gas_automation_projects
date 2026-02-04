# Sistema de Evaluación Petrofísica Automatizada (PetroBatch)

- **Versión:** 1.1 (Fase 5 - Final Release)  
- **Autor:** Ing. Gabriel Astudillo  
- **Fecha:** Febrero 2026  
- **Motor:** Python 3.10+ (`lasio`, `pandas`, `numpy`, `matplotlib`)

---

## 1. Resumen Ejecutivo

PetroBatch es una suite de software de alto rendimiento diseñada para la evaluación petrofísica masiva (*Batch Processing*) de registros de pozos en formato LAS.  
Esta herramienta trasciende las calculadoras básicas de registros, implementando un flujo de trabajo de Ingeniería de Yacimientos industrialmente robusto. Su objetivo principal es convertir datos crudos en valor económico, jerarquizando activos mediante el cálculo de HCPV (*Hydrocarbon Pore Volume*).

### Capacidades Clave (Fase 5)

- **Física Avanzada:** Implementación de Simandoux Modificado para corrección de arcillosidad ($V_{sh}$) en el cálculo de saturación ($S_w$).
- **Matriz Inteligente:** Detección automática de litología (Arenisca/Caliza/Dolomía) basada en curvas PEF ($P_{ef}$) punto a punto.
- **Integridad de Datos:** *Pipeline* de ejecución estricto donde el Control de Calidad (QC) elimina datos espurios (derrumbes/*washouts*) antes de la estimación de reservas.
- **Ranking Económico:** Clasificación automática de pozos basada en HCPV (Metros de poro-hidrocarburo), no solo en espesor bruto.

---

## 2. Arquitectura del Sistema

El sistema es modular y desacoplado para facilitar el mantenimiento:

### A. `las_inspect.py` (El Motor Físico)

Contiene la "verdad matemática" del proyecto.

- **Gestión de Alias:** Reconoce mnemónicos variables (ej. `GR`, `GAPI`, `NGAP` → `GR`).
- **Normalización:** Convierte unidades imperiales (pies) a Sistema Internacional (metros) automáticamente.
- **Simandoux Modificado:**
  $$
  \frac{1}{R_t} = \frac{\phi^m}{a \cdot R_w (1-V_{sh})} + \frac{V_{sh} \cdot S_w}{R_{sh}}
  $$
- **QC "Hard Kill":** Elimina drásticamente datos donde:
  - Caliper > Bit Size + Tolerancia.
  - Densidad < 1.95 g/cc (Lodo).
  - Porosidad > 35% (Físicamente imposible en este contexto).

### B. `las_batch_processor.py` (El Orquestador)

Gestiona el flujo masivo:

- Itera sobre carpetas de datos.
- Determina parámetros dinámicos (Matriz Auto vs Fija).
- Ejecuta el *Pipeline Seguro*: $V_{sh} \rightarrow \phi \rightarrow \text{Filtro QC} \rightarrow S_w$.
- Exporta tablas de resultados (`.csv`) rankeadas por HCPV.

### C. `las_visualizer.py` (El Analista Gráfico)

- Genera visualizaciones *Quad-Combo* (Litología, Resistividad, Porosidad, *Pay Zone*).
- Garantiza consistencia visual: Aplica los mismos *cutoffs* usados en el cálculo numérico.
- Muestra estadísticas de HCPV y *Pay* en el gráfico.

---

## 3. Parámetros de Evaluación (Inputs)

El sistema solicita parámetros clave al inicio, permitiendo sensibilidades rápidas:

| Parámetro       | Default               | Descripción                                                                 |
|-----------------|-----------------------|-----------------------------------------------------------------------------|
| Densidad Matriz | `AUTO`                | Si es `None`, usa PEF (<2.5: Arena, >4.0: Caliza). Si falla PEF, asume 2.65. |
| Rw              | 0.05 $\Omega \cdot m$ | Resistividad del agua de formación (a temperatura de yacimiento).           |
| R_Shale         | 2.0 $\Omega \cdot m$  | Resistividad de la arcilla (para Simandoux).                                |
| Cutoff Vsh      | 0.50 (50%)            | Límite máximo de volumen de arcilla.                                        |
| Cutoff Phi      | 8.0 %                 | Porosidad mínima efectiva.                                                  |
| Cutoff Sw       | 0.50 (50%)            | Saturación de agua máxima.                                                  |

---

## 4. Definición de Reservas (Resultados)

El sistema calcula dos métricas fundamentales para cada pozo:

1. **Net Pay (Espesor Neto Productivo)**  
   Suma de intervalos (paso de profundidad) que cumplen simultáneamente:
   - $V_{sh} < \text{Cutoff}$
   - $\phi_{final} \ge \text{Cutoff}$ (Datos limpios post-QC)
   - $S_w < \text{Cutoff}$
   - Sin indicio de derrumbe (QC Flag = OK)

2. **HCPV (*Hydrocarbon Pore Volume*)**  
   Es la métrica de "dinero". Representa el espesor equivalente si se comprimiera todo el hidrocarburo en una capa 100% porosa y saturada:
   $$
   HCPV = \sum_{\text{Pay}} (\text{Step} \times \phi \times (1 - S_w))
   $$
   Este es el criterio utilizado para ordenar el ranking final.

---

## 5. Guía de Uso Rápida

### Requisitos

```bash
pip install lasio pandas numpy matplotlib
```

### Ejecución

1. Colocar archivos `.las` en la carpeta `LAS_data`.
2. Correr el script maestro:
   ```bash
   python las_batch_processor.py
   ```
3. Seguir las instrucciones en consola. Para una corrida estándar, presionar `Enter` en todos los *prompts* para usar los *defaults* recomendados.

### Salidas

- **CSV de Reservas:**  
  `Resultados_Fase4_PayZone/Tablas/Resumen_Reservas_PayZone.csv`
- **Gráficos:**  
  `Resultados_Fase4_PayZone/Plots/*.png`

---

## 6. Historial de Cambios (Change Log)

### Fase 5 (Actual)

- **[FÍSICA]** Migración de Archie a Simandoux Modificado.
- **[LÓGICA]** Corrección crítica del orden de ejecución: El filtro de calidad ahora se aplica después de calcular porosidad para eliminar picos falsos (>35%) antes de calcular saturación.
- **[ECONOMÍA]** Implementación de HCPV en todos los módulos y reordenamiento del CSV por potencial económico.
- **[UX]** Visualizador ahora recibe *cutoffs* dinámicos del procesador para total consistencia imagen-dato.

### Fase 4

- Implementación de procesamiento por lotes (*Batch*).
- Generación de CSV resumen.

### Fase 1-3

- Carga de curvas, normalización de unidades y visualización básica.
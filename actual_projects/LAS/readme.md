# Sistema de Evaluación Petrofísica Automatizada (PetroBatch)

Versión: 1.0 (Release Fase 5)

Autor: Ing. Gabriel Astudillo

Fecha: Febrero 2026

Lenguaje: Python 3.10+

Librerías: lasio, pandas, numpy, matplotlib

## 1. Resumen Ejecutivo

PetroBatch es una suite de software desarrollada en Python diseñada para la evaluación petrofísica masiva ("Batch Processing") de archivos de registros de pozo (formato LAS).

A diferencia de calculadoras simples, este sistema implementa un flujo de trabajo de Ingeniería de Yacimientos robusto, incorporando:

Normalización automática de unidades (SI).

Control de Calidad (QC) multi-variable (Mecánico, Físico y Litológico).

Cálculo de reservas (Net Pay) basado en cortes petrofísicos estándar.

Generación de reportes auditables y visualización avanzada (Quad-Combo).

## 2. Arquitectura del Sistema

El proyecto es modular y consta de tres componentes principales y una herramienta de validación:

### las_inspect.py (El Núcleo / Backend)

Contiene la lógica física y matemática.

Gestión de Alias: Diccionario inteligente para reconocer mnemónicos (GR, GAPI, CGR -> GR).

Normalización SI: Detecta si el pozo está en pies (FT) y convierte índices y espesores a Metros (m).

Algoritmos: Cálculo de $V_{sh}$, Porosidad ($\phi_D$, $\phi_N$, $\phi_T$), Saturación de Agua ($S_w$).

Filtros de Calidad (QC): Lógica para anular datos en zonas de derrumbe o lecturas erróneas.

### las_visualizer.py (El Visualizador / Frontend)

Genera gráficos de calidad de publicación.

Quad-Combo Plot: 4 Pistas (Litología+Caliper, Resistividad, Porosidad+Efecto Gas/Lutita, Fluidos).

QC Flags: Sombreado gris en zonas donde la data fue invalidada por mala calidad.

Interpretación Visual: Rellenos de color para litología (Gamma Ray), Gas (Crossover D-N) y Pay (Saturación).

### las_batch_processor.py (El Orquestador)

Procesa carpetas enteras de archivos LAS.

Itera sobre todos los archivos .las.

Aplica la lógica de negocio (Cutoffs).

Calcula el Net Pay (Espesor Neto Productivo).

Exporta estadísticas finales a CSV (Ranking de Pozos).

### las_pickett.py (Validación)

Herramienta gráfica interactiva (Pickett Plot) para calibrar parámetros de Archie ($R_w, m$) y asegurar la coherencia física.

## 3. Metodología de Cálculo

### 3.1. Pre-procesamiento

Limpieza de Nulos: Se eliminan valores -999.25 y similares.

Conversión de Profundidad: Si STRT.unit es 'F' o 'FT', se multiplica la profundidad por 0.3048.

### 3.2. Propiedades Petrofísicas

Volumen de Arcilla ($V_{sh}$): Modelo Lineal usando percentiles estadísticos del pozo (P05 para arena limpia, P95 para arcilla) para evitar outliers.


$$V_{sh} = \frac{GR - GR_{min}}{GR_{max} - GR_{min}}$$

Porosidad Densidad ($\phi_D$):


$$\phi_D = \frac{\rho_{ma} - \rho_b}{\rho_{ma} - \rho_{fl}}$$


Parámetros: $\rho_{ma}=2.65$ (Arenisca), $\rho_{fl}=1.0$ (Agua).

Porosidad Total ($\phi_T$): Promedio aritmético para compensar efectos de gas y arcilla.


$$\phi_T = \frac{\phi_D + \phi_N}{2}$$

Saturación de Agua ($S_w$): Ecuación de Archie.


$$S_w = \sqrt[n]{ \frac{a \cdot R_w}{\phi_T^m \cdot R_t} }$$


Parámetros Típicos: $a=1, m=2, n=2, R_w=0.05$.

## 4. Sistema de Control de Calidad (QC Shield) 🛡️

El sistema aplica tres filtros estrictos antes de calcular reservas. Si un dato falla en cualquiera de estos filtros, se marca como NaN y **no suma reservas**.

| Tipo de Filtro | Criterio | Acción | Razón Física |
| :---- | :---- | :---- | :---- |
| **Mecánico** | $CALI > BitSize + 2.5"$ | Anular $\phi, S_w$ | Derrumbe (Washout). El patín de densidad lee lodo, creando porosidad falsa. |
| **Físico** | $\rho_b < 1.75 g/cc$ | Anular $\phi, S_w$ | Lectura de lodo o error de herramienta. Evita porosidades \> 100%. |
| **Litológico** | $\phi_N - \phi_D > 15\%$ | Anular Pay | Efecto de Arcilla (Shale Effect). Separa lutitas húmedas de reservorios reales. |


## 5. Definición de "Net Pay" (Reservas)

Para que un intervalo de profundidad cuente como Espesor Neto Productivo (Net Pay), debe cumplir simultáneamente:

Condición de Roca: $V_{sh} < 50\%$ (Es Arena).

Condición de Almacén: $\phi_T \ge 8\%$ (Tiene espacio poroso conectado).

Condición de Fluido: $S_w < 50\%$ (Tiene Hidrocarburo móvil).

Condición de Calidad: QC_Flag == PASS (El dato es confiable).

$$NetPay = \sum (\text{Step} \times \text{PayFlag})$$

## 6. Guía de Uso

### Requisitos Previos

Tener Python instalado y las librerías necesarias:

pip install lasio pandas numpy matplotlib


### Ejecución

Colocar archivos .las en la carpeta LAS_data.

Ejecutar el procesador:

python las_batch_processor.py


Ingresar parámetros cuando se soliciten (o usar defaults con Enter).

Matriz (2.65), Rw (0.05), Cutoffs.

### Resultados

Los archivos se generan en la carpeta Resultados_Fase4_PayZone:

/Plots: Imágenes .png de cada pozo (Quad-Combo).

/Tablas: Resumen_Reservas_PayZone.csv con el ranking de pozos.

## 7. Validación y Benchmarking

La herramienta ha sido validada mediante:

Prueba de Escritorio: Comparación celda por celda contra cálculo manual en Excel (Diferencia < 0.5%).

Pickett Plot: Verificación gráfica de $R_w$ y $m$ usando las_pickett.py.

Prueba de Estrés: Procesamiento exitoso de 120 pozos, identificando correctamente pozos secos y descartando falsos positivos por mala calidad de hoyo.

Nota Final: Esta herramienta debe ser utilizada como soporte a la decisión. Se recomienda siempre una inspección visual final de los pozos "Top Ranking" por un petrofísico cualificado.
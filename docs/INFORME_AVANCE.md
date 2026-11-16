# Informe de Avance: Optimización de Horarios Universitarios mediante Algoritmos Genéticos (EvoSchedule)

**Asignatura:** Inteligencia Artificial  
**Carrera:** Ingeniería Civil Informática  
**Formato:** Entrega Hito 1 (Máximo 4 páginas)  

---

## 1. Introducción y Planteamiento del Problema

La calendarización de horarios universitarios (*University Course Timetabling Problem*, UCTP) es un problema clásico de optimización combinatoria de clase NP-hard. En el contexto de la carrera de Ingeniería Civil Informática (ICI), planificar las clases semanales de forma manual implica coordinar variables fuertemente acopladas:
1. **Restricciones duras:** Choques horarios de un mismo docente ($P_{prof}$), solapamiento de asignaturas del mismo nivel semestral ($P_{asig}$) y choques por uso simultáneo de un mismo espacio físico o laboratorio ($P_{sal}$).
2. **Restricciones blandas:** Acumulación excesiva de ventanas o tiempos muertos entre bloques de clase ($P_{vent}$) para los estudiantes de cada nivel.

El objetivo del proyecto **EvoSchedule** es automatizar la generación de mallas horarias universitarias utilizando **Algoritmos Genéticos (AG)**, formulando una función de aptitud normalizada que castiga cuadráticamente la distancia a una solución ideal libre de conflictos.

---

## 2. Flujo General del Sistema y Exploración de Datos (EDA)

### 2.1 Flujo General del Sistema (Entrada, Procesamiento, Salida)

El flujo global se estructura de la siguiente manera:
* **Entrada:** Ingesta del archivo institucional Excel `HorarioICI_2026-2.xlsx`, extracción del catálogo oficial de asignaturas, identificación de docentes asignados, cupos y catálogo de infraestructura (aulas y laboratorios).
* **Procesamiento:** Transformación de la carga docente en 88 sesiones atómicas (genes). Ejecución de la cota de referencia (Baseline aleatorio y voraz) e iteración del motor genético (inicialización, selección por torneo $k=3$, cruce uniforme, mutación estocástica, elitismo y cálculo multiobjetivo de fitness).
* **Salida:** Horario semanal optimizado desglosado por nivel y sala, métricas de evolución generacional (JSON) y visualización interactiva a través del prototipo de interfaz.

```
[Entrada: Excel Institucional] ---> [DataLoader & 88 Genes Atómicos]
                                            |
                                            v
[Salida: Malla Semanal & Logs] <--- [Algoritmo Genético: Selección + Cruce + Mutación + Fitness]
```

### 2.2 Exploración de Datos (EDA)

A partir del dataset institucional `dataset/HorarioICI_2026-2.xlsx`, se desarrolló un extractor en Python basado en OpenXML que recuperó el 100% de la oferta académica:

| Variable / Dimensión | Valor Observado | Descripción en el Modelo |
| :--- | :---: | :--- |
| **Total Asignaturas** | 45 | Cursos impartidos entre Nivel I y Nivel XI |
| **Sesiones Atómicas ($m$)** | 88 | Genes que componen el cromosoma del individuo |
| **Cuerpo Docente** | 32 profesores | Docentes con asignación de cátedra o laboratorio |
| **Salas Disponibles** | 17 espacios | Aulas teóricas (A, B, C, D, E) y Labs (LAB-C, LAB-E, LAB-Q, LC1) |
| **Jornada Semanal** | 5 días (L-V) | 8 bloques diarios de 80 minutos (08:10 a 20:00 hrs) |

**Distribución de Asignaturas por Nivel Académico:**
* *Nivel I y II (Primer Año):* 11 asignaturas (Cálculo Diferencial, Química, Int. a la Programación, etc.).
* *Nivel III y IV (Segundo Año):* 11 asignaturas (Cálculo en Varias Variables, Ecuaciones Dif., Estructura de Datos, etc.).
* *Nivel V y VI (Tercer Año):* 8 asignaturas (Base de Datos, Estadística, Análisis de Algoritmos, etc.).
* *Nivel VII y VIII (Cuarto Año):* 9 asignaturas (Sistemas Operativos, Inteligencia Artificial, Ing. de Software, etc.).
* *Nivel XI (Quinto Año / Electivos):* 6 asignaturas (Seguridad Informática, React, Arquitectura de SW, etc.).

---

## 3. Modelamiento Matemático y Código Base en Python

### 3.1 Representación del Cromosoma (Genotipo y Fenotipo)

Un individuo $H$ (horario completo) se expresa como un conjunto de $m = 88$ tuplas atómicas:
$$H = \{ t_1, t_2, \dots, t_m \}, \quad t_i = (dia, bloque, duracion, profesor, asignatura, sala)$$
Donde $dia \in [1, 5]$, $bloque \in [1, 8]$, $duracion = 1$, y $sala \in \{ \text{Salas disponibles} \}$.

### 3.2 Función de Penalización y Distancia Multiobjetivo

Se calcula el vector de penalizaciones $P(H) = [P_{prof}, P_{asig}, P_{vent}, P_{sal}] \in \mathbb{R}^4$, donde:
* $P_{prof}$: Pares de asignaturas solapadas de un mismo docente.
* $P_{asig}$: Pares de asignaturas del mismo nivel solapadas en día y bloque.
* $P_{vent}$: Suma total de bloques libres internos (huecos) entre clases de un mismo nivel en un mismo día.
* $P_{sal}$: Pares de asignaturas que colisionan en la misma sala física.

La distancia cuadrática ponderada al horario ideal ($H_{ideal}$ con $P = \vec{0}$) y la función de aptitud normalizada son:
$$D(H) = \sqrt{\sum_{k=1}^4 w_k \cdot P_k(H)^2}, \qquad F(H) = \frac{1}{1 + D(H)} \in (0, 1]$$
Con vector de pesos: $w = (w_{prof}=5.0, \, w_{asig}=5.0, \, w_{vent}=0.05, \, w_{sal}=5.0)$ para priorizar la estricta eliminación de choques duros frente a la compactación de ventanas.

### 3.3 Código Base Modular en Python

El proyecto cuenta con una arquitectura desacoplada y documentada en `src/`:
* `src/data_loader.py`: Extracción OpenXML pura (sin dependencias externas pesadas) y estructuración de datos.
* `src/domain.py`: Clases `@dataclass Asignacion` y `Horario`.
* `src/fitness.py`: Evaluador vectorizado e indexado por diccionarios hash para $P(H)$, $D(H)$ y $F(H)$.
* `src/baseline.py`: Generador estadístico de asignaciones aleatorias y voraces.
* `src/genetic.py`: Motor evolutivo (selección, cruce uniforme, mutación estocástica y elitismo).
* `src/visualizer.py`: Renderizador de curvas de convergencia ASCII y matrices horarias.

---

## 4. Baseline Ejecutado, Evolución y Resultados Preliminares

### 4.1 Benchmark del Baseline (Cota Inferior)

Para validar cuantitativamente la necesidad y eficacia del Algoritmo Genético, se ejecutó un **Baseline Aleatorio** sobre 30 repeticiones independientes con semillas estocásticas controladas:

* **Fitness Promedio:** $F_{base} = 0.022349 \pm 0.004784$
* **Distancia Promedio:** $D(H)_{base} = 45.51$
* **Desglose de Conflictos Promedio:** $P_{prof} = 1.97$, $P_{asig} = 18.33$, $P_{vent} = 49.43$, $P_{sal} = 6.10$.

*Conclusión del Baseline:* La asignación no guiada produce un promedio inaceptable de 18 colisiones de asignaturas del mismo nivel y más de 6 salas en conflicto.

### 4.2 Evolución del Algoritmo Genético

Se ejecutó el AG con los siguientes **hiperparámetros iniciales**:
* Tamaño de población ($N$): 80 individuos
* Número de generaciones: 60 generaciones
* Tasa de cruce ($p_c$): 0.85 (Cruzamiento uniforme)
* Tasa de mutación ($p_m$): 0.05 por gen
* Selección: Torneo de tamaño $k = 3$
* Elitismo: 2 mejores individuos preservados intactos por generación
* Tiempo de cómputo: **1.58 segundos** en CPU estándar

### 4.3 Tabla Comparativa de Resultados Preliminares

| Métrica / Penalización | Baseline Aleatorio (30 runs) | Algoritmo Genético (Gen 60) | Impacto / Mejora |
| :--- | :---: | :---: | :---: |
| **Función de Aptitud $F(H)$** | $0.022349$ | **$0.151741$** | **+ 579.0% (Mejora radical)** |
| **Distancia al Origen $D(H)$** | $45.51$ | **$5.59$** | **- 87.7% (Reducción de penalidad)** |
| **Choque Docente ($P_{prof}$)** | $1.97$ | **0** | **100% resuelto (Sin choques)** |
| **Choque Asignatura Nivel ($P_{asig}$)** | $18.33$ | **0** | **100% resuelto (Sin solapamientos)** |
| **Choque de Sala ($P_{sal}$)** | $6.10$ | **0** | **100% resuelto (Sin choques físicos)** |
| **Ventanas Libres ($P_{vent}$)** | $49.43$ | **25** | **Reducción de casi el 50% en huecos** |

```
Curva de Convergencia del Fitness F(H):
0.1517 |                                        ██████
0.1192 |                    ██████████                
0.0703 |             ███████                          
0.0378 | ███████                                      
       └─────────────────────────────────────────────
        Gen 0                                 Gen 60
```

---

## 5. Primer Borrador del Diseño de Interfaz (UI)

Se implementó el prototipo interactivo en `app.py`, el cual presenta la siguiente arquitectura funcional:

1. **Estructura Funcional y Menús:**
   * `[1] Explorar Datos del Campus`: Despliegue de métricas del EDA (aulas, asignaturas, docentes).
   * `[2] Análisis de Carga Académica`: Consulta de sesiones por docente y materias por nivel.
   * `[3] Módulo de Baseline`: Ejecución del benchmark de referencia con métricas en pantalla.
   * `[4] Motor Evolutivo`: Configuración interactiva de población y generaciones con monitoreo en vivo.
   * `[5] Visualizador de Horario`: Renderizado de la matriz semanal (Lunes a Viernes, Bloques B1 a B8) filtrada por nivel académico.
   * `[6] Exportación`: Descarga del horario final en formato JSON estructurado (`output/horario_optimizado.json`).

2. **Componentes y Proyección Web:**
   * La estructura modular en capas desacopladas permite migrar de forma inmediata este backend a una interfaz visual en **Streamlit**, incorporando selectores de parámetros, gráficos dinámicos de convergencia y visualización de aulas con paletas de colores por nivel.

---

## 6. Descripción del Apoyo Recibido de Inteligencia Artificial Generativa (IAG)

En estricto cumplimiento ético y académico, se documenta el uso de IAG (asistente de código pair-programming) en las siguientes tareas:
1. **Depuración y Resolución de Bugs OpenXML:** Corrección de la extracción de cadenas compartidas XML en hojas de cálculo complejas, evitando desfasajes de índices en etiquetas `<si>` y `<t>`.
2. **Arquitectura y Modularización:** Diseño limpio de las estructuras de datos (`Asignacion` y `Horario`) y optimización de las funciones de penalización mediante tablas hash para evitar complejidades $O(m^2)$.
3. **Generación de Gráficos y Visualización:** Creación del módulo de renderizado ASCII en terminal para inspección rápida de curvas de convergencia y tablas de horarios.
4. **Redacción y Documentación:** Estructuración del presente informe técnico y elaboración del guión de presentación de 4 láminas.

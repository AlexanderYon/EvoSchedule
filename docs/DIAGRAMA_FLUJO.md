# Diagrama de Flujo General del Sistema EvoSchedule

A continuación se detalla la arquitectura de extremo a extremo del sistema de optimización de horarios universitarios, dividida en sus tres fases fundamentales: **Entrada**, **Procesamiento** y **Salida**.

```mermaid
flowchart TD
    subgraph ENTRADA ["1. FASE DE ENTRADA (Datos y Parámetros)"]
        direction TB
        E1["Archivo Institucional Excel<br/>(dataset/HorarioICI_2026-2.xlsx)"]
        E2["Catálogo de Asignaturas, Cupos y Niveles<br/>(Nivel I al Nivel XI)"]
        E3["Inventario de Salas y Laboratorios<br/>(A3, B7, LC1, LAB-Q, etc.)"]
        E4["Restricciones y Docentes Asignados<br/>(32 Docentes Oficiales)"]
        E5["Hiperparámetros de Evolución<br/>(Población N, Tasa Cruce, Tasa Mutación, Pesos w)"]

        E1 --> E2
        E1 --> E3
        E1 --> E4
    end

    subgraph PROCESAMIENTO ["2. FASE DE PROCESAMIENTO (Motor Genético y Baseline)"]
        direction TB
        P1["Data Loader & Normalizador<br/>Desglose en 88 Sesiones Atómicas (Genes)"]
        P2["Generación de Solución Baseline<br/>(Asignación Aleatoria y Voraz)"]
        P3["Población Inicial del AG<br/>(N = 80 Individuos Aleatorios)"]
        P4["Evaluador de Fenotipo & Penalizaciones P(H)<br/>[P_prof, P_asig, P_vent, P_sal] en R^4"]
        P5["Cálculo de Distancia Cuadrática D(H)<br/>D(H) = sqrt(sum(w_k * P_k^2))"]
        P6["Cálculo de Aptitud F(H)<br/>F(H) = 1 / (1 + D(H))"]
        P7{"¿Criterio de Parada?<br/>(Gen >= 60 o D(H) < Umbral)"}
        P8["Elitismo (Top 2)<br/>Preservar mejores soluciones"]
        P9["Selección por Torneo (k=3)"]
        P10["Cruzamiento Uniforme (Tasa: 85%)"]
        P11["Mutación Estocástica (Tasa: 5%)<br/>(Cambio de Día, Bloque o Sala)"]

        E2 & E3 & E4 --> P1
        P1 --> P2
        P1 --> P3
        P3 --> P4
        P2 --> P4
        P4 --> P5
        P5 --> P6
        P6 --> P7
        P7 -- No --> P8
        P7 -- No --> P9
        P9 --> P10
        P10 --> P11
        P11 --> P4
        P8 --> P4
    end

    subgraph SALIDA ["3. FASE DE SALIDA (Resultados e Interfaz)"]
        direction TB
        S1["Mejor Horario Optimizado H_opt<br/>(Cromosoma Libre de Conflictos Duros)"]
        S2["Trazas y Logs de Convergencia<br/>(JSON, Historial Generacional)"]
        S3["Dashboard / Interfaz de Usuario (CLI / Web)<br/>Visualización semanal por Nivel o Sala"]
        S4["Exportación de Horario Oficial<br/>(JSON / Matriz Académica)"]

        P7 -- Sí --> S1
        S1 --> S2
        S1 --> S3
        S1 --> S4
    end

    E5 -.-> P3
    E5 -.-> P5
    E5 -.-> P10
    E5 -.-> P11
```

---

## Explicación Detallada de Componentes

### 1. Entrada (Input)
* **Dataset Excel (`HorarioICI_2026-2.xlsx`):** Contiene la programación histórica y las tablas de carga académica de los 5 niveles (I al XI) de Ingeniería Civil Informática.
* **Extracción Normalizada:** Se procesa sin dependencias binarias externas, garantizando portabilidad multiplataforma.
* **Configuración del Problema:** Matriz de 8 bloques diarios (80 minutos c/u) $\times$ 5 días hábiles (Lunes a Viernes) y 17 aulas/laboratorios físicos.

### 2. Procesamiento (Processing)
* **Baseline:** Permite establecer una cota inferior de rendimiento estocástico evaluando 30 asignaciones aleatorias independientes.
* **Algoritmo Genético:**
  * **Cromosoma:** Array de $m = 88$ tuplas atómicas $t_i = (dia, bloque, duracion, profesor, asignatura, sala)$.
  * **Evaluación Multiobjetivo:** Penalizaciones agrupadas por índice hash en tiempo casi-lineal para las 4 restricciones: $P_{prof}, P_{asig}, P_{vent}, P_{sal}$.
  * **Operadores:** Torneo determinista de 3 contendientes, recombinación uniforme para conservar bloques válidos y mutación estocástica.

### 3. Salida (Output)
* **Horario Semanal Libre de Conflictos Duros:** Cero solapamientos de profesor ($P_{prof}=0$), cero choques de materias del mismo nivel ($P_{asig}=0$) y cero conflictos de sala ($P_{sal}=0$).
* **Métricas y Trazas:** Almacenamiento en `logs/` con formato JSON estructurado.
* **Interfaz de Usuario:** Prototipo funcional interactivo en terminal y compatible con frontend web.

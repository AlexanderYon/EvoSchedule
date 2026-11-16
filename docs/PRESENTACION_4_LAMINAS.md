# Guión de Exposición: EvoSchedule (Máximo 5 Minutos / 4 Láminas)

**Estructura de la Presentación:** 4 Láminas  
**Tiempo Límite:** 5:00 minutos exactos por equipo + ronda de preguntas individuales.  

---

## LÁMINA 1: Planteamiento del Problema, Contexto Académico y Datos (EDA)
**Tiempo sugerido:** 1:00 minuto  

### Contenido Visual de la Lámina:
* **Título:** EvoSchedule: Automatización y Optimización de Horarios Universitarios mediante Algoritmos Genéticos.
* **Problema Central (UCTP):** Coordinación de 45 asignaturas, 32 docentes y 17 salas en una carrera de ingeniería (ICI), minimizando solapamientos y tiempos muertos.
* **Exploración del Dataset Real (`HorarioICI_2026-2.xlsx`):**
  * 45 asignaturas desglosadas en 88 sesiones atómicas semanales (genes).
  * 5 Niveles formativos (Nivel I al XI).
  * 17 salas disponibles (aulas teóricas y laboratorios de especialidad LAB-C, LAB-E, LAB-Q, LC1).
  * Jornada académica: 5 días hábiles (Lunes a Viernes) $\times$ 8 bloques diarios de 80 minutos.

### Guión del Expositor:
> *"Buenos días profesor y compañeros. Hoy les presentamos EvoSchedule. La confección manual de horarios universitarios es un problema combinatorio de alta complejidad conocido como UCTP, donde el número de combinaciones posibles crece de forma exponencial.*
> *Para este proyecto abordamos el caso real de la carrera de Ingeniería Civil Informática utilizando los datos oficiales del segundo semestre. A partir del dataset institucional, extrajimos 45 asignaturas distribuidas en 5 niveles, lo que equivale a 88 sesiones atómicas que deben agendarse semanalmente entre 32 docentes y 17 espacios físicos disponibles. Nuestro objetivo es automatizar y optimizar esta asignación a través de Algoritmos Genéticos."*

---

## LÁMINA 2: Modelamiento Matemático, Cromosoma y Función de Aptitud
**Tiempo sugerido:** 1:15 minutos  

### Contenido Visual de la Lámina:
* **Representación del Genotipo (Cromosoma):**
  * Individuo $H = \{ t_1, t_2, \dots, t_m \}$ con $m = 88$ tuplas atómicas.
  * Gen atómico: $t_i = (dia, bloque, duracion, profesor, asignatura, sala)$.
* **Vector de Penalizaciones Multiobjetivo:**
  $$P(H) = [P_{prof}, P_{asig}, P_{vent}, P_{sal}] \in \mathbb{R}^4$$
  * $P_{prof}$: Solapamiento del mismo docente en un mismo bloque y día.
  * $P_{asig}$: Choques entre asignaturas del mismo nivel académico.
  * $P_{vent}$: Bloques libres (huecos) entre la primera y última clase del día para los estudiantes.
  * $P_{sal}$: Clases asignadas simultáneamente al mismo espacio físico o laboratorio.
* **Distancia Cuadrática y Fitness Normalizado:**
  $$D(H) = \sqrt{\sum w_k \cdot P_k(H)^2}, \qquad F(H) = \frac{1}{1 + D(H)} \in (0, 1]$$
  * Castigo no lineal al cuadrado ($P(H)^{\odot 2}$) para sancionar desastres concentrados y priorizar restricciones duras ($w_{prof}=w_{asig}=w_{sal}=5.0$).

### Guión del Expositor:
> *"Para abordar este desafío, modelamos cada solución como un cromosoma compuesto por 88 genes, donde cada gen representa una sesión de clase con su día, bloque y sala.*
> *Evaluamos la calidad de cada horario a través de un vector de cuatro penalizaciones: tres restricciones duras —docente, nivel y sala— y una blanda —ventanas libres entre clases—. Para evaluar qué tan lejos estamos de un horario ideal, utilizamos la distancia cuadrática ponderada al origen, aplicando un castigo no lineal al elevar las infracciones al cuadrado. Así, un horario con 10 choques es 4 veces peor que uno con 5. Finalmente, normalizamos esta métrica en una función de aptitud F(H) entre 0 y 1 que el algoritmo genético busca maximizar."*

---

## LÁMINA 3: Resultados Experimentales: Baseline vs. Algoritmo Genético
**Tiempo sugerido:** 1:30 minutos  

### Contenido Visual de la Lámina:
* **Tabla Comparativa de Desempeño:**

| Métrica | Baseline Aleatorio (30 runs) | Algoritmo Genético (Gen 60) | Diferencia / Impacto |
| :--- | :---: | :---: | :---: |
| **Fitness $F(H)$** | $0.022349$ | **$0.151741$** | **+ 579.0% (Mejora radical)** |
| **Distancia $D(H)$** | $45.51$ | **$5.59$** | **- 87.7% (Reducción de penalidad)** |
| **Choque Docente ($P_{prof}$)** | $1.97$ | **0** | **100% resuelto (Sin choques)** |
| **Choque de Nivel ($P_{asig}$)** | $18.33$ | **0** | **100% resuelto (Sin solapamientos)** |
| **Choque de Sala ($P_{sal}$)** | $6.10$ | **0** | **100% resuelto (Sin choques físicos)** |
| **Ventanas Libres ($P_{vent}$)** | $49.43$ | **25** | **Reducción del 50% en huecos** |

* **Gráfico de Convergencia:** Curva monótona creciente de Fitness a lo largo de 60 generaciones (tiempo de ejecución: **1.58 segundos**).
* **Hiperparámetros:** Población $N=80$, Cruce $85\%$, Mutación $5\%$, Torneo $k=3$, Elitismo $=2$.

### Guión del Expositor:
> *"Para medir la eficacia del algoritmo, implementamos primero un Baseline aleatorio evaluado en 30 repeticiones independientes, el cual arrojó un fitness promedio de 0.022 y más de 18 choques de asignaturas por nivel, lo que demuestra la inviabilidad de soluciones no inteligentes.*
> *Al ejecutar nuestro Algoritmo Genético durante 60 generaciones —lo cual toma apenas 1.58 segundos—, el fitness aumentó un 579%, mientras que la distancia de penalización se desplomó un 87.7%. Lo más destacable: el algoritmo eliminó por completo todas las colisiones de profesores, todas las colisiones del mismo nivel y todas las colisiones de salas, dejándolas en cero absoluto, a la vez que redujo las ventanas de los estudiantes a la mitad. Esto demuestra la enorme potencia del algoritmo."*

---

## LÁMINA 4: Diseño de Interfaz, Apoyo de IAG y Próximos Pasos
**Tiempo sugerido:** 1:15 minutos  

### Contenido Visual de la Lámina:
* **Prototipo de Interfaz Funcional (`app.py`):**
  * Menú modular: visualización del EDA, configuración de hiperparámetros en vivo, visualizador de horarios semanales por nivel y exportación en JSON.
* **Apoyo Recibido de IAG:**
  * Depuración del parser OpenXML (`sharedStrings` en archivos Excel complejos).
  * Optimización de complejidad temporal en la función de fitness (agrupaciones hash).
  * Generación de visualizadores y documentación técnica.
* **Trabajo Futuro:**
  * Implementación de frontend web interactivo en Streamlit.
  * Ponderación adaptativa de mutación para compactar aún más las ventanas libres.

### Guión del Expositor:
> *"Diseñamos además un primer prototipo interactivo de interfaz de usuario en Python, que permite al usuario cargar los datos, ajustar la población y tasas de mutación, y consultar la grilla horaria resultante filtrada por nivel de primero a quinto año.*
> *En cuanto al uso de Inteligencia Artificial Generativa, fue un apoyo fundamental como herramienta de pair-programming: nos asistió en la depuración del extractor OpenXML, en la vectorización hash del fitness para lograr evaluaciones en milisegundos, y en la estructuración de la documentación.*
> *Nuestros siguientes pasos consistirán en desplegar la interfaz web en Streamlit y experimentar con operadores adaptativos para compactar aún más las ventanas libres. Quedamos atentos a sus preguntas. Muchas gracias."*

---

## Batería de Preguntas Individuales Anticipadas (Para la defensa)

1. **¿Por qué utilizaron selección por torneo en lugar de la clásica ruleta?**
   * *Respuesta:* La ruleta sufre de estancamiento cuando las diferencias de fitness son pequeñas (como ocurre al inicio con valores cercanos a 0.02). El torneo de tamaño $k=3$ mantiene una presión selectiva constante, es computacionalmente eficiente ($O(k)$) y no requiere reescalar el fitness.
2. **¿Por qué la distancia al origen utiliza una penalización cuadrática ($P(H)^{\odot 2}$)?**
   * *Respuesta:* Para aplicar un castigo no lineal. Esto garantiza que una solución con 10 choques en una sola variable sea considerada mucho peor que otra con 2 choques distribuidos, forzando al algoritmo a resolver primero los conflictos más graves.
3. **¿Cómo garantizan que el mejor horario encontrado no se pierda durante la evolución?**
   * *Respuesta:* Mediante elitismo ($E=2$). En cada generación, los dos individuos más aptos pasan directamente y sin modificaciones a la siguiente población, asegurando una convergencia monótona no decreciente.

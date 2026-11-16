# EvoSchedule: Optimización de Horarios Universitarios mediante Algoritmos Genéticos

Proyecto de Inteligencia Artificial enfocado en la resolución del **University Course Timetabling Problem (UCTP)** mediante **Algoritmos Genéticos (AG)**, aplicado a la carrera de **Ingeniería Civil Informática (ICI)** a partir de datos reales institucionales.

---

## Estructura del Repositorio

```
EvoSchedule/
├── dataset/
│   └── HorarioICI_2026-2.xlsx      # Datos académicos reales (Catálogo, Docentes, Aulas, Horarios)
├── docs/
│   ├── requisitos_proyecto.txt     # Requisitos formales de la entrega
│   ├── DIAGRAMA_FLUJO.md           # Diagrama Mermaid de Entrada, Procesamiento y Salida
│   ├── INFORME_AVANCE.md           # Informe técnico de avance (máx. 4 páginas)
│   └── PRESENTACION_4_LAMINAS.md   # Guión cronometrado (5 min) y láminas para la exposición
├── logs/
│   ├── eda_summary.json            # Métricas del Análisis Exploratorio de Datos
│   ├── baseline_results.json       # Resultados estadísticos del Baseline (30 repeticiones)
│   └── ag_evolution.json           # Trazas generacionales del Algoritmo Genético
├── src/
│   ├── __init__.py
│   ├── data_loader.py              # Extracción OpenXML pura de asignaturas, cupos y salas
│   ├── domain.py                   # Entidades fundamentales: Asignacion (Gen) y Horario (Individuo)
│   ├── fitness.py                  # Función de penalización P(H) in R^4, distancia D(H) y fitness F(H)
│   ├── baseline.py                 # Generador de horarios Baseline (Aleatorio y Voraz)
│   ├── genetic.py                  # Motor del Algoritmo Genético (Torneo, Cruce, Mutación, Elitismo)
│   └── visualizer.py               # Renderizador ASCII de convergencia y mallas horarias
├── app.py                          # Prototipo interactivo de interfaz de usuario (CLI / Dashboard)
├── run_experiments.py              # Script reproducible de experimentos de punta a punta
├── DESC_PROBLEMA.md                # Formulación matemática y modelamiento del problema
├── requirements.txt                # Dependencias recomendadas del entorno
└── README.md                       # Documentación general del proyecto
```

---

## Ejecución Rápida

El núcleo del sistema está diseñado con biblioteca estándar de Python (>= 3.9), por lo que **no requiere instalación de paquetes adicionales** para su ejecución básica.

### 1. Ejecutar Experimentos de Punta a Punta
Ejecuta la extracción de datos (EDA), el benchmark del Baseline (30 repeticiones), la evolución de 60 generaciones del AG y genera las tablas comparativas y curvas de convergencia:

```bash
python3 run_experiments.py
```

### 2. Iniciar el Prototipo de Interfaz de Usuario
Despliega el menú interactivo para explorar el catálogo, configurar hiperparámetros del AG, inspeccionar horarios semanales por nivel académico y exportar a JSON:

```bash
python3 app.py
```

---

## Resultados Principales (Baseline vs. AG)

$$P(H) = [P_{prof}, P_{asig}, P_{vent}, P_{sal}] \in \mathbb{R}^4$$

| Métrica | Baseline Aleatorio (30 runs) | Algoritmo Genético (Gen 60) | Impacto / Mejora |
| :--- | :---: | :---: | :---: |
| **Aptitud $F(H)$** | $0.022349 \pm 0.0048$ | **$0.151741$** | **+ 579.0% (Mejora radical)** |
| **Distancia $D(H)$** | $45.51$ | **$5.59$** | **- 87.7% (Reducción de penalidad)** |
| **Choque Docente ($P_{prof}$)** | $1.97$ | **0** | **100% resuelto (Sin choques)** |
| **Choque de Nivel ($P_{asig}$)** | $18.33$ | **0** | **100% resuelto (Sin solapamientos)** |
| **Choque de Sala ($P_{sal}$)** | $6.10$ | **0** | **100% resuelto (Sin choques físicos)** |
| **Ventanas Libres ($P_{vent}$)** | $49.43$ | **25** | **Reducción del 50% en huecos** |

---

## Documentos de la Entrega

* [DIAGRAMA_FLUJO.md](file:///home/yonatan/Uni/IA/EvoSchedule/docs/DIAGRAMA_FLUJO.md): Diagrama Mermaid de flujo general.
* [INFORME_AVANCE.md](file:///home/yonatan/Uni/IA/EvoSchedule/docs/INFORME_AVANCE.md): Informe listo para imprimir en PDF (máx. 4 páginas).
* [PRESENTACION_4_LAMINAS.md](file:///home/yonatan/Uni/IA/EvoSchedule/docs/PRESENTACION_4_LAMINAS.md): Guión de 5 minutos y preparación de preguntas individuales.

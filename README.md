# EvoSchedule: Planificación de Horarios Universitarios mediante Algoritmos Genéticos

Proyecto de Inteligencia Artificial enfocado en la resolución del **University Course Timetabling Problem (UCTP)** mediante **Algoritmos Genéticos (AG)** y comparado rigurosamente contra un **Baseline Voraz (Greedy)**, aplicado a la carrera de **Ingeniería Civil Informática (ICI)** a partir de datos reales institucionales (`dataset/HorarioICI_2026-2.xlsx`).

---

## 📌 Guía de Orientación: ¿Dónde está cada cosa?

```text
EvoSchedule/
├── dataset/
│   └── HorarioICI_2026-2.xlsx      # Catálogo académico real (45 asignaturas, 32 docentes, 17 salas)
├── src/
│   ├── __init__.py
│   ├── data_loader.py              # Parser OpenXML nativo (sin dependencias): extrae 45 asignaturas y 90 sesiones
│   ├── domain.py                   # Entidades base: Asignacion (Gen) y Horario (Individuo/Cromosoma)
│   ├── fitness.py                  # Evaluador hash O(m): vector P(H) in R^4, distancia D(H) y fitness F(H)
│   ├── baseline.py                 # Baseline Oficial: Algoritmo Voraz constructivo (First-Fit / Best-Fit)
│   ├── genetic.py                  # Motor AG: Torneo k=3, Cruce uniforme (1 hijo), Mutación y Elitismo E=2
│   └── visualizer.py               # Renderizador ASCII de mallas horarias y curvas de convergencia
├── app.py                          # Prototipo interactivo por consola (CLI Dashboard)
├── gui.py                          # Interfaz gráfica en Tkinter (vistas por nivel, docente y sala)
├── run_experiments.py              # Script de experimentos (5 semillas, análisis de parámetros y baseline)
├── requirements.txt                # Dependencias recomendadas del entorno (PyQt6 para GUI)
└── README.md                       # Orientación y documentación general del proyecto
```

---

## 🚀 Guía de Ejecución

El núcleo algorítmico (`src/`, `app.py`, `run_experiments.py`) está desarrollado con la **biblioteca estándar de Python (>= 3.9)**, por lo que **no requiere instalar paquetes externos** para ejecutar la optimización y los experimentos.

### 1. Ejecutar el Benchmark Completo de Experimentos
Ejecuta la extracción de datos (EDA), la resolución mediante el **Baseline Voraz (Greedy)**, la evolución generacional del **Algoritmo Genético**, imprime las tablas comparativas y guarda las trazas en `logs/`:

```bash
python3 run_experiments.py
```

### 2. Ejecutar la Interfaz Gráfica (Tkinter)
Abre la aplicación de escritorio en Tkinter. Permite visualizar el horario semanal por nivel formativo, por docente y por sala, mostrando el resumen de restricciones violadas:

```bash
python gui.py
```
> *Nota:* Si estás en un servidor sin pantalla gráfica (headless) y quieres regenerar la captura para la documentación:
> ```bash
> python3 gui.py --screenshot
> ```

### 3. Iniciar el Dashboard Interactivo por Consola (CLI)
Permite inspeccionar datos del campus, ejecutar el Baseline Greedy o el AG con parámetros personalizados, ver la grilla por nivel en terminal y exportar a JSON:

```bash
python3 app.py
```

---

## 🧠 Modelamiento del Problema

El modelo sigue las siguientes especificaciones formales:

1. **Catálogo de Asignaturas:** 45 asignaturas regulares extraídas de `dataset/HorarioICI_2026-2.xlsx`.
2. **Sesiones Semanales:** Cada asignatura se dicta **2 veces por semana**, y cada clase dura **2 bloques pedagógicos de 45 minutos** (90 minutos continuos por sesión). Esto resulta en un cromosoma de **$m = 90$ sesiones atómicas** a programar.
3. **Jornada y Capacidad del Campus:**
   - 5 días lectivos (Lunes a Viernes).
   - **16 bloques pedagógicos de 45 minutos** por día: Mañana (B1 a B8, 08:10 a 14:00) y Tarde/Vespertino (B9 a B16, 14:10 a 20:00).
   - Bloques de inicio válidos para clases de 2 bloques: módulos impares $b \in \{1, 3, 5, 7, 9, 11, 13, 15\}$.
   - Oferta instalada: $17\text{ salas} \times 16\text{ bloques} \times 5\text{ días} = \mathbf{1,360\text{ casilleros bloque-sala}}$.
   - Demanda requerida: $90\text{ sesiones} \times 2\text{ bloques} = \mathbf{180\text{ casilleros}}$ ($13.24\%$ de ocupación de campus).
4. **Espacio de Penalizaciones $P(H) \in \mathbb{R}^4$ y Aptitud:**
   $$P(H) = \big[ P_{\text{prof}}(H),\, P_{\text{asig}}(H),\, P_{\text{vent}}(H),\, P_{\text{sal}}(H) \big]$$
   - $P_{\text{prof}}$ (*Dura*): Choque de docente en un mismo día y bloque ($w_1 = 5.0$).
   - $P_{\text{asig}}$ (*Dura*): Choque de asignaturas del mismo nivel académico ($w_2 = 5.0$).
   - $P_{\text{vent}}$ (*Blanda*): Ventanas horarias libres entre clases del mismo nivel ($w_3 = 0.05$).
   - $P_{\text{sal}}$ (*Dura*): Asignaciones simultáneas sobre la misma aula física ($w_4 = 5.0$).
   - **Distancia al origen y Aptitud:**
     $$D(H) = \sqrt{\sum w_k P_k(H)^2}, \qquad F(H) = \frac{1}{1 + D(H)} \in (0, 1]$$

---

## ⚙️ Arquitectura de los Algoritmos

### 1. Baseline Oficial: Algoritmo Voraz (Greedy)
- Enfoque constructivo secuencial determinista.
- Asigna cada una de las 90 sesiones en el casillero (día, bloque, sala) de menor costo inmediato.
- Incorpora alternancia de días para sesiones gemelas de una misma asignatura (ej. Lunes y Miércoles).
- **Rendimiento:** Encuentra una solución globalmente factible ($D=0.00, F=1.000000$) con cero choques en apenas **$0.088$ segundos**.

### 2. Algoritmo Genético (AG)
- **Representación:** Cromosoma de $m = 90$ tuplas $t_i = (dia, bloque, duracion=2, profesor, asignatura, sala)$.
- **Selección de Padres:** Torneo determinista de tamaño $k = 3$.
- **Cruce Uniforme (1 hijo):** Recorre los 90 genes en paralelo; para cada sesión académica se elige aleatoriamente (50/50) si hereda la asignación horaria del Padre 1 o del Padre 2.
- **Mutación Estocástica ($p_m = 0.05$):** Modifica aleatoriamente el día, el bloque modular o la sala física asignada a un gen.
- **Mecanismo de Supervivencia:** **Reemplazo Generacional con Elitismo ($E = 2$)**. Los dos mejores individuos de la generación se clonan directamente a la siguiente población, garantizando que el mejor fitness sea monótonamente no decreciente.
- **Criterio de Parada:** Cantidad fija de generaciones ($G = 60$), asegurando una cota superior determinista de tiempo de cómputo para evaluaciones comparativas uniformes.

---

## 👥 Integrantes del Equipo
- **Yonatan Chiuca**
- **Sebastián Cea**
- **Sebastian Cádiz**

*Asignatura:* Inteligencia Artificial (ICI 2026-2) -- *Proyecto EvoSchedule*

# EvoSchedule – Diseño de horarios universitarios (Avance 2)

Proyecto Python para Ingeniería Civil en Informática UBB. Compara un algoritmo genético con un baseline voraz sobre el mismo escenario.

## Ejecutar
Desde la carpeta EvoSchedule, con Python 3.9 o superior:

```bash
python -m pip install -r requirements.txt
python gui.py
```

Para reproducir las cinco semillas y las comparaciones de parámetros:

```bash
python run_experiments.py
```

También se conserva `python app.py` (consola). En Linux puede ser necesario instalar `python3-tk`. El AG utiliza DEAP para torneo y cruces cuando está instalado; si no está disponible, conserva los operadores Python originales como respaldo. El motor utilizado se registra en el JSON. Para la entrega con DEAP, instalarlo y volver a ejecutar los experimentos.

## Datos y supuestos
- Fuente: archivo institucional `dataset/HorarioICI_2026-2.xlsx`, planificación ICI UBB. Licencia/autorización no informada; verificar antes de distribuir fuera del curso.
- Se conservan 45 registros de asignaturas/secciones, 32 docentes registrados, 17 salas, 90 sesiones (dos por registro). No se reconstruye la carga horaria oficial ni se distingue automáticamente la asistencia de secciones paralelas.
- Cinco días, 16 bloques de 40 minutos por día según la interfaz original. Cada sesión dura dos bloques consecutivos y comienza en un bloque impar.
- Capacidad uniforme de 65 estudiantes por sala, por decisión del proyecto.
- Matrícula simulada de 30 a 65 estudiantes por registro; disponibilidad simulada de cuatro días por docente y preferencia mañana/tarde, generadas con `random.Random(2026)` en `src/data_loader.py`. Ambas sesiones del registro comparten matrícula y perfil docente. No son datos reales.
- Una segunda sesión práctica se supone para registros cuyo nombre contiene programación, taller, base de datos o estructura de datos; se asigna a salas LAB-* o LC*. Es una aproximación, no una clasificación oficial.

## Modelo
El cromosoma mantiene una asignación por sesión (día, bloque, sala, docente, nivel y duración), con metadatos de matrícula y perfil. El evaluador devuelve P_prof, P_asig, P_vent, P_sal, P_disp, P_cap, P_tipo, P_pref, en ese orden.

Restricciones duras: choques de profesor, nivel y sala; indisponibilidad docente; matrícula superior a 65; sesión práctica fuera de laboratorio. Blandas: ventanas y preferencias mañana/tarde.

Sea H el número total de infracciones duras y B = sqrt(0.05 * ventanas² + 0.05 * preferencias²). La distancia modificada es D = H + B/(1+B); el fitness sigue siendo F = 1/(1+D). La parte blanda es inferior a uno, por lo que un horario factible siempre supera a uno no factible. La distancia y fitness no son directamente comparables con los del avance anterior.

Greedy ordena sesiones por necesidad de laboratorio, número de sesiones a cargo del docente y duración, en orden descendente. Esta dificultad es logística, no académica. Prioriza evitar infracciones duras, luego preferencias y días distintos de una misma asignatura. El AG mantiene población aleatoria, torneo, cruce uniforme o de dos puntos, mutación y elitismo; genera y muta días y salas compatibles cuando existen.

## Interfaz y experimentos
La interfaz permite ejecutar ambos métodos, consultar horarios por nivel/docente/sala y seleccionar una fila para ver nombres completos y matrícula. El AG usa parámetros fijos en la interfaz: población 80, 40 generaciones, mutación 0.05, semilla 123 y cruce uniforme. Los gráficos y comparaciones se generan mediante run_experiments.py. Una fila rosada indica coincidencias en la vista seleccionada; el resumen contabiliza todas las infracciones del horario.

`run_experiments.py` ejecuta 5 semillas (42, 101, 202, 303, 404), población 80 y 40 generaciones; compara tres parámetros con semilla 123 y 30 generaciones. Guarda resultados y gráficos actualizados en `logs/`. Las comparaciones de parámetros son preliminares (una semilla). No se garantiza que AG supere a Greedy. Los tiempos dependen del equipo.

## Archivos principales
`src/domain.py`, `data_loader.py`, `fitness.py`, `baseline.py`, `genetic.py`, `visualizer.py`, `gui.py`, `app.py`, `run_experiments.py`. El informe y anexo IAG deben documentar los supuestos, cambios y resultados; no se incluyen como entregables terminados en este ZIP.

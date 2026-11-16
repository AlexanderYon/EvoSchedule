# Optimización de Horarios Universitarios mediante Algoritmos Genéticos

## Planteamiento del Problema

La planificación de horarios universitarios es un proceso organizativo complejo que incide directamente en la eficiencia institucional y en la dinámica académica. El problema central consiste en coordinar un conjunto de variables fuertemente interdependientes: la disponibilidad limitada de aulas, las restricciones de agenda del cuerpo docente, y la asignación de asignaturas para los estudiantes sin generar solapamientos, topes horarios ni ventanas excesivas (tiempo libre entre clases).

Con el aumento de la oferta académica y la matrícula, la programación manual o semi-manual se torna ineficiente y propensa a incompatibilidades de horario y subutilización de la infraestructura. En este contexto, surge la necesidad de contar con una solución optimizada que automatice la generación de horarios, reduciendo de manera efectiva los conflictos entre la disponibilidad de espacios físicos, la agenda de los profesores y los itinerarios lectivos de los estudiantes.

En este proyecto se contempla el uso de algoritmos genéticos que permitan diseñar los horarios universitarios de forma automática.

## Modelamiento del Problema

Por motivos de practicidad y escala, el dominio del problema se acotará al contexto de una misma carrera universitaria, aunque no se descarta la posibilidad de que la solución pueda extenderse posteriormente a un contexto más general y considerar todas las carreras que se dictan en un mismo campus.

### Representación del Individuo (Cromosoma)

Se define la tupla de asignación del horario atómico de una asignatura:

```
t = (dia, bloque, duracion, profesor, asignatura, sala)

```

Donde:

* **`dia`** $\in [1,5]$, asumiendo que la universidad tiene clases solo 5 días a la semana.

* **`bloque`** $\in [1,n]$, donde $n$ es la cantidad total de bloques de una jornada académica.

* **`duracion`** representa la cantidad de bloques continuos que dura la clase.

* **`profesor`** es el identificador del docente.

* **`asignatura`** es el identificador de la asignatura.

* **`sala`** es el identificador del espacio físico.

Llamaremos $H$ al conjunto de tuplas $t$ que completen un horario. Es decir, $H$ es el individuo en el contexto del Algoritmo Genético (AG). Por consiguiente, cada tupla $t_i$ representa un gen del individuo.

#### Ejemplo de Asignación

Consideremos una asignación atómica dada por la tupla:
`t_1 = (1, 1, 2, "P01", "INF-101", "Lab-02")`

Esto se traduce en:

* `dia = 1` (Lunes)

* `bloque = 1` (Primer bloque de la jornada)

* `duracion = 2` (Clase de 2 bloques continuos)

* `profesor = "P01"` (Código del profesor asignado)

* `asignatura = "INF-101"` (Código de la asignatura)

* `sala = "Lab-02"` (Identificador de la sala)

De este modo, un individuo $H$ (un horario completo) se expresa como el conjunto de $m$ tuplas atómicas:

$$
H = \{ t_1, t_2, ..., t_m \}
$$

Llamaremos $S$ al conjunto de todos los individuos $H$ posibles (el espacio de búsqueda o población de soluciones), sobre el cual operará el algoritmo genético mediante la evaluación de la función de aptitud (fitness) y la aplicación de los operadores de selección, cruzamiento y mutación.

### Restricciones y Penalización

Definimos una función de penalización $P : S \to \mathbb{R}^4$

$$
P(H) = [P_{prof}, P_{asig}, P_{vent}, P_{sal}]
$$

Donde cada componente evalúa un tipo de conflicto:

* $P_{prof}$: Cantidad de pares de asignaturas que un mismo profesor dicta al mismo tiempo (solapadas).

* $P_{asig}$: Cantidad de pares de asignaturas de un mismo nivel que se solapan.

* $P_{vent}$: Tiempo total (en bloques) entre clases (ventanas libres).

* $P_{sal}$: Cantidad de salas que tienen clases solapadas asignadas.

### Evaluación del Fenotipo

Para evaluar qué tan “correcto” es un individuo, consideramos la función de distancia:

$$
D(H) = \sqrt{w \cdot P(H)^{\odot 2}}
$$

Donde $w = (w_{prof}, w_{asig}, w_{vent}, w_{sal})$ es el vector de pesos.

Se utiliza la distancia al origen como métrica para determinar cuantitativamente qué tan lejos está una solución de la ideal. Adicionalmente, se aplica un **castigo no lineal** al vector de penalización elevando cada uno de sus elementos al cuadrado ($P(H)^{\odot 2}$). De esta forma, un horario con $P_{sal} = 10$ no es el doble de “malo” que uno con $P_{sal} = 5$, sino cuatro veces peor.

El individuo ideal $H_{sol}$ es aquel donde $D(H_{sol}) \approx 0$.

### Función de Aptitud (Fitness)

Dado que los algoritmos genéticos por lo general maximizan las métricas de selección, y en este problema buscamos minimizar la distancia al origen, se define la siguiente función de aptitud normalizada:

$$
F(H) = \frac{1}{1 + D(H)}
$$

Esta función $F(H) \in (0, 1]$ se utilizará para medir qué tan apto es un individuo $H$ para pasar sus genes a la siguiente generación.

"""Pruebas pequeñas del modelo: ejecutar python test_restricciones.py."""
from src.domain import Asignacion, Horario
from src.fitness import FitnessEvaluator
from src.data_loader import DataLoader
from src.baseline import GreedyBaseline
from src.genetic import AlgoritmoGenetico

f = FitnessEvaluator()
# A tiene un choque; B tiene muchas ventanas pero es factible.
a = (1, 0, 0, 0, 0, 0, 0, 0)
b = (0, 0, 200, 0, 0, 0, 0, 200)
assert f.calcular_fitness(f.calcular_distancia(b)) > f.calcular_fitness(f.calcular_distancia(a))
g = Asignacion('A', 'Prueba', 'P', 1, 2, 1, 9, 'A3', 66, True, 1, True)
assert f.restricciones_sesion(g) == (1, 1, 1, 1)
assert f.evaluar_penalizaciones(Horario([g]))[4:] == (1, 1, 1, 1)
assert g.clonar() == g
loader = DataLoader(); sesiones, salas = loader.extraer_datos()
assert all(c == 65 for c in loader.capacidades.values())
greedy = GreedyBaseline(sesiones, salas).ejecutar(f)['horario']
assert greedy.num_genes == len(sesiones)
assert greedy.duros == 0
ag = AlgoritmoGenetico(sesiones, salas, f, tam_poblacion=10, seed=42)
r = ag.evolucionar(3, False)
assert r['mejor_individuo'].num_genes == len(sesiones)
assert len({g.id_asig for g in r['mejor_individuo'].genes}) == len(sesiones)
assert all(a['mejor_fitness'] <= b['mejor_fitness'] for a,b in zip(r['historial'],r['historial'][1:]))
print('Pruebas correctas. Motor:', ag.motor)

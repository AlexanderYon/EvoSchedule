"""
Módulo de Algoritmos Baseline para EvoSchedule.
Implementa generadores de horarios de referencia para establecer una cota base (baseline):
1. RandomBaseline: Asignación puramente aleatoria de día, bloque y sala.
2. GreedyBaseline: Asignación voraz heurística secuencial.
Permite evaluar y reportar métricas estadísticas con fines comparativos contra el Algoritmo Genético.
"""

import random
from typing import List, Dict, Any, Tuple
from src.domain import Horario, Asignacion
from src.fitness import FitnessEvaluator


class BaselineGenerator:
    def __init__(self, workload: List[Dict[str, Any]], available_rooms: List[str], total_blocks: int = 8, days: int = 5):
        self.workload = workload
        self.available_rooms = available_rooms
        self.total_blocks = total_blocks
        self.days = days

    def generar_aleatorio(self, seed: int = None) -> Horario:
        """Genera un individuo con asignación completamente aleatoria uniforme."""
        if seed is not None:
            random.seed(seed)

        genes = []
        for item in self.workload:
            duracion = item["duracion"]
            dia = random.randint(1, self.days)
            bloque = random.randint(1, self.total_blocks - duracion + 1)
            sala = random.choice(self.available_rooms)

            genes.append(Asignacion(
                sesion_id=item["sesion_id"],
                asignatura=item["asignatura_nombre"],
                profesor=item["docente"],
                nivel=item["nivel"],
                duracion=duracion,
                dia=dia,
                bloque=bloque,
                sala=sala
            ))

        return Horario(genes=genes)

    def generar_voraz(self, seed: int = None) -> Horario:
        """
        Genera un horario mediante heurística voraz (Greedy):
        Intenta asignar cada sesión en la primera combinación (día, bloque, sala)
        que minimice conflictos inmediatos con las clases ya asignadas.
        """
        if seed is not None:
            random.seed(seed)

        genes: List[Asignacion] = []
        for item in self.workload:
            duracion = item["duracion"]
            mejor_opcion = None
            menor_choque = float('inf')

            # Mezclar opciones para evitar sesgos deterministas
            dias = list(range(1, self.days + 1))
            bloques = list(range(1, self.total_blocks - duracion + 1))
            salas = list(self.available_rooms)
            random.shuffle(dias)
            random.shuffle(bloques)
            random.shuffle(salas)

            # Probar opciones candidatas
            for d in dias:
                for b in bloques:
                    for s in salas:
                        choques = 0
                        temp = Asignacion(
                            sesion_id=item["sesion_id"],
                            asignatura=item["asignatura_nombre"],
                            profesor=item["docente"],
                            nivel=item["nivel"],
                            duracion=duracion,
                            dia=d,
                            bloque=b,
                            sala=s
                        )
                        for g in genes:
                            if temp.solapa_con(g):
                                if g.profesor == temp.profesor:
                                    choques += 3
                                if g.nivel == temp.nivel:
                                    choques += 2
                                if g.sala == temp.sala:
                                    choques += 2

                        if choques < menor_choque:
                            menor_choque = choques
                            mejor_opcion = (d, b, s)
                            if choques == 0:
                                break
                    if menor_choque == 0:
                        break
                if menor_choque == 0:
                    break

            dia_asig, bloque_asig, sala_asig = mejor_opcion
            genes.append(Asignacion(
                sesion_id=item["sesion_id"],
                asignatura=item["asignatura_nombre"],
                profesor=item["docente"],
                nivel=item["nivel"],
                duracion=duracion,
                dia=dia_asig,
                bloque=bloque_asig,
                sala=sala_asig
            ))

        return Horario(genes=genes)

    def ejecutar_benchmark_baseline(
        self,
        evaluador: FitnessEvaluator,
        num_muestras: int = 30,
        tipo: str = "aleatorio"
    ) -> Dict[str, Any]:
        """
        Ejecuta múltiples repeticiones del baseline para obtener estadísticas
        robustas (promedio, desviación estándar, mejor y peor caso).
        """
        fitnesses = []
        distancias = []
        penalizaciones_acum = [0, 0, 0, 0]
        mejor_horario = None
        mejor_fitness = -1.0

        for i in range(num_muestras):
            if tipo == "voraz":
                h = self.generar_voraz(seed=1000 + i)
            else:
                h = self.generar_aleatorio(seed=1000 + i)

            fit = evaluador.evaluar(h)
            fitnesses.append(fit)
            distancias.append(h.distancia)

            for idx in range(4):
                penalizaciones_acum[idx] += h.penalizaciones[idx]

            if fit > mejor_fitness:
                mejor_fitness = fit
                mejor_horario = h

        p_promedio = tuple(p / num_muestras for p in penalizaciones_acum)
        fit_promedio = sum(fitnesses) / num_muestras
        dist_promedio = sum(distancias) / num_muestras

        fit_std = (sum((f - fit_promedio) ** 2 for f in fitnesses) / num_muestras) ** 0.5

        return {
            "tipo": tipo,
            "muestras": num_muestras,
            "fitness_promedio": fit_promedio,
            "fitness_std": fit_std,
            "fitness_mejor": max(fitnesses),
            "fitness_peor": min(fitnesses),
            "distancia_promedio": dist_promedio,
            "penalizaciones_promedio": {
                "P_prof": p_promedio[0],
                "P_asig": p_promedio[1],
                "P_vent": p_promedio[2],
                "P_sal": p_promedio[3],
            },
            "mejor_individuo": mejor_horario
        }

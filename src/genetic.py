"""
Módulo del Algoritmo Genético (AG) para EvoSchedule.
Implementa el motor evolutivo para optimizar la asignación de horarios universitarios:
- Inicialización de población
- Selección por torneo (k=3)
- Cruzamiento (Crossover Uniforme)
- Mutación aleatoria de atributos fenotípicos (día, bloque, sala)
- Elitismo (preservación de los mejores individuos)
- Registro y monitoreo de la convergencia generación a generación.
"""

import random
from typing import List, Dict, Any, Tuple
from src.domain import Horario, Asignacion
from src.fitness import FitnessEvaluator
from src.baseline import BaselineGenerator


class AlgoritmoGenetico:
    def __init__(
        self,
        workload: List[Dict[str, Any]],
        available_rooms: List[str],
        evaluador: FitnessEvaluator,
        tam_poblacion: int = 80,
        tasa_cruce: float = 0.85,
        tasa_mutacion: float = 0.05,
        elitismo: int = 2,
        k_torneo: int = 3,
        total_blocks: int = 8,
        days: int = 5,
        seed: int = 42
    ):
        self.workload = workload
        self.available_rooms = available_rooms
        self.evaluador = evaluador
        self.tam_poblacion = tam_poblacion
        self.tasa_cruce = tasa_cruce
        self.tasa_mutacion = tasa_mutacion
        self.elitismo = elitismo
        self.k_torneo = k_torneo
        self.total_blocks = total_blocks
        self.days = days
        self.seed = seed

        self.generator = BaselineGenerator(workload, available_rooms, total_blocks, days)
        self.poblacion: List[Horario] = []
        self.historial: List[Dict[str, Any]] = []
        self.mejor_historico: Horario = None

        if seed is not None:
            random.seed(seed)

    def inicializar_poblacion(self):
        """Crea la población inicial con individuos aleatorios y semilleros."""
        self.poblacion = []
        for i in range(self.tam_poblacion):
            h = self.generator.generar_aleatorio()
            self.evaluador.evaluar(h)
            self.poblacion.append(h)

        self.poblacion.sort(key=lambda x: x.fitness, reverse=True)
        self.mejor_historico = self.poblacion[0].clonar()

    def seleccion_torneo(self) -> Horario:
        """Selecciona un individuo mediante torneo de tamaño k."""
        candidatos = random.sample(self.poblacion, self.k_torneo)
        candidatos.sort(key=lambda x: x.fitness, reverse=True)
        return candidatos[0]

    def cruce_uniforme(self, p1: Horario, p2: Horario) -> Tuple[Horario, Horario]:
        """
        Aplica cruzamiento uniforme entre dos progenitores gen a gen
        respetando la correspondencia de las sesiones atómicas.
        """
        if random.random() > self.tasa_cruce:
            return p1.clonar(), p2.clonar()

        hijo1_genes = []
        hijo2_genes = []

        for g1, g2 in zip(p1.genes, p2.genes):
            if random.random() < 0.5:
                hijo1_genes.append(g1.clonar())
                hijo2_genes.append(g2.clonar())
            else:
                hijo1_genes.append(g2.clonar())
                hijo2_genes.append(g1.clonar())

        return Horario(genes=hijo1_genes), Horario(genes=hijo2_genes)

    def mutar(self, individuo: Horario):
        """
        Muta aleatoriamente los genes del individuo (día, bloque o sala)
        con probabilidad tasa_mutacion por gen.
        """
        for gen in individuo.genes:
            if random.random() < self.tasa_mutacion:
                opcion = random.choice(["bloque", "dia", "sala", "todo"])

                if opcion in ["bloque", "todo"]:
                    gen.bloque = random.randint(1, self.total_blocks - gen.duracion + 1)
                if opcion in ["dia", "todo"]:
                    gen.dia = random.randint(1, self.days)
                if opcion in ["sala", "todo"]:
                    gen.sala = random.choice(self.available_rooms)

    def evolucionar(self, num_generaciones: int = 60, verbose: bool = True) -> Dict[str, Any]:
        """
        Ejecuta el ciclo generacional completo del Algoritmo Genético.
        Retorna las trazas completas de la evolución y el mejor individuo hallado.
        """
        if not self.poblacion:
            self.inicializar_poblacion()

        self.historial = []
        self._registrar_generacion(0, verbose)

        for gen_idx in range(1, num_generaciones + 1):
            nueva_poblacion: List[Horario] = []

            # 1. Elitismo
            for i in range(self.elitismo):
                nueva_poblacion.append(self.poblacion[i].clonar())

            # 2. Reproducción
            while len(nueva_poblacion) < self.tam_poblacion:
                p1 = self.seleccion_torneo()
                p2 = self.seleccion_torneo()

                h1, h2 = self.cruce_uniforme(p1, p2)

                self.mutar(h1)
                self.evaluador.evaluar(h1)
                nueva_poblacion.append(h1)

                if len(nueva_poblacion) < self.tam_poblacion:
                    self.mutar(h2)
                    self.evaluador.evaluar(h2)
                    nueva_poblacion.append(h2)

            self.poblacion = nueva_poblacion
            self.poblacion.sort(key=lambda x: x.fitness, reverse=True)

            if self.poblacion[0].fitness > self.mejor_historico.fitness:
                self.mejor_historico = self.poblacion[0].clonar()

            self._registrar_generacion(gen_idx, verbose)

        return {
            "mejor_individuo": self.mejor_historico,
            "historial": self.historial,
            "generaciones": num_generaciones,
            "tam_poblacion": self.tam_poblacion,
            "tasa_cruce": self.tasa_cruce,
            "tasa_mutacion": self.tasa_mutacion
        }

    def _registrar_generacion(self, gen_idx: int, verbose: bool):
        fitnesses = [ind.fitness for ind in self.poblacion]
        distancias = [ind.distancia for ind in self.poblacion]
        mejor = self.poblacion[0]

        registro = {
            "generacion": gen_idx,
            "mejor_fitness": mejor.fitness,
            "fitness_promedio": sum(fitnesses) / len(fitnesses),
            "menor_distancia": mejor.distancia,
            "distancia_promedio": sum(distancias) / len(distancias),
            "p_prof": mejor.penalizaciones[0],
            "p_asig": mejor.penalizaciones[1],
            "p_vent": mejor.penalizaciones[2],
            "p_sal": mejor.penalizaciones[3],
        }
        self.historial.append(registro)

        if verbose and (gen_idx % 10 == 0 or gen_idx == 1):
            p = mejor.penalizaciones
            print(
                f"Gen {gen_idx:03d} | Mejor Fitness: {mejor.fitness:.6f} | "
                f"D(H): {mejor.distancia:6.2f} | "
                f"P=[prof:{p[0]}, asig:{p[1]}, vent:{p[2]}, sal:{p[3]}]"
            )

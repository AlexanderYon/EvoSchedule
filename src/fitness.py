"""
Módulo de cálculo de penalizaciones, distancia al origen y función de aptitud (fitness)
para EvoSchedule, implementando fielmente la formulación matemática de DESC_PROBLEMA.md.

Formulación:
- P(H) = [P_prof, P_asig, P_vent, P_sal] in R^4
- D(H) = sqrt( sum( w_k * P_k(H)^2 ) )
- F(H) = 1 / (1 + D(H))
"""

import math
from typing import Tuple, Dict, List
from collections import defaultdict
from src.domain import Horario, Asignacion


class FitnessEvaluator:
    def __init__(
        self,
        w_prof: float = 5.0,
        w_asig: float = 5.0,
        w_vent: float = 0.05, # las ventanas no son tan graves como los choques horarios o de salas (es una restricción blanda)
        w_sal: float = 5.0,
    ):
        """
        Pesos del vector w = (w_prof, w_asig, w_vent, w_sal).
        Las restricciones duras (profesor, nivel y sala) tienen mayor ponderación.
        La restricción blanda (ventanas libres) tiene una ponderación menor.
        """
        self.weights = (w_prof, w_asig, w_vent, w_sal)


    # ===========================================================
    #       Determinar P(H)
    # ===========================================================
    def evaluar_penalizaciones(self, horario: Horario) -> Tuple[int, int, int, int]:
        """
        Calcula el vector de penalizaciones P(H) = [P_prof, P_asig, P_vent, P_sal].
        Implementado de manera eficiente mediante agrupaciones indexadas por día y entidad.
        """
        genes = horario.genes

        # 1. P_prof: Solapamiento de un mismo profesor en el mismo bloque y día
        p_prof = 0
        prof_dia_map: Dict[Tuple[str, int], List[Asignacion]] = defaultdict(list)
        for g in genes:
            prof_dia_map[(g.profesor, g.dia)].append(g)

        for (prof, dia), lista in prof_dia_map.items():
            n = len(lista)
            if n > 1:
                for i in range(n):
                    for j in range(i + 1, n):
                        if lista[i].solapa_con(lista[j]):
                            p_prof += 1

        # 2. P_asig: Solapamiento de asignaturas del mismo nivel académico
        # 3. P_vent: Ventanas libres entre clases para los estudiantes de un mismo nivel
        p_asig = 0
        p_vent = 0
        nivel_dia_map: Dict[Tuple[int, int], List[Asignacion]] = defaultdict(list)
        for g in genes:
            nivel_dia_map[(g.nivel, g.dia)].append(g)

        for (nivel, dia), lista in nivel_dia_map.items():
            n = len(lista)
            # Evaluar P_asig
            if n > 1:
                for i in range(n):
                    for j in range(i + 1, n):
                        if lista[i].solapa_con(lista[j]):
                            p_asig += 1

            # Evaluar P_vent (bloques libres entre la primera y la última clase del día)
            bloques_ocupados = set()
            for g in lista:
                for b in range(g.bloque, g.bloque + g.duracion):
                    bloques_ocupados.add(b)

            if len(bloques_ocupados) >= 2:
                bloque_min = min(bloques_ocupados)
                bloque_max = max(bloques_ocupados)
                span = bloque_max - bloque_min + 1
                huecos = span - len(bloques_ocupados)
                if huecos > 0:
                    p_vent += huecos

        # 4. P_sal: Cantidad de salas con clases solapadas en el mismo bloque y día
        p_sal = 0
        sala_dia_map: Dict[Tuple[str, int], List[Asignacion]] = defaultdict(list)
        for g in genes:
            sala_dia_map[(g.sala, g.dia)].append(g)

        for (sala, dia), lista in sala_dia_map.items():
            n = len(lista)
            if n > 1:
                for i in range(n):
                    for j in range(i + 1, n):
                        if lista[i].solapa_con(lista[j]):
                            p_sal += 1

        return (p_prof, p_asig, p_vent, p_sal)


    # ===========================================================
    #       D(H): Distancia al origen
    # ===========================================================
    def calcular_distancia(self, penalizaciones: Tuple[int, int, int, int]) -> float:
        """
        Calcula la distancia cuadrática ponderada al origen:
        D(H) = sqrt( w · P(H)^⊙2 )
        """

        # esta es la fórmula que se definió en el modelo
        w_prof, w_asig, w_vent, w_sal = self.weights
        p_prof, p_asig, p_vent, p_sal = penalizaciones

        suma_cuadratica = (
            w_prof * (p_prof ** 2)
            + w_asig * (p_asig ** 2)
            + w_vent * (p_vent ** 2)
            + w_sal * (p_sal ** 2)
        )
        return math.sqrt(suma_cuadratica)


    # ===========================================================
    #       F(H): Aptitud
    # ===========================================================
    def calcular_fitness(self, distancia: float) -> float:
        """
        Función de aptitud normalizada F(H) in (0, 1]:
        F(H) = 1 / (1 + D(H))
        """
        return 1.0 / (1.0 + distancia)

    # ===========================================================
    #       Recibe un horario y retorna su aptitud de inmediato
    # ===========================================================
    def evaluar(self, horario: Horario) -> float:
        """
        Evalúa un horario completo, asignando in-place sus penalizaciones,
        distancia D(H) y aptitud F(H). Retorna el valor de fitness.
        """
        penalizaciones = self.evaluar_penalizaciones(horario)
        distancia = self.calcular_distancia(penalizaciones)
        fitness = self.calcular_fitness(distancia)

        horario.penalizaciones = penalizaciones
        horario.distancia = distancia
        horario.fitness = fitness

        return fitness

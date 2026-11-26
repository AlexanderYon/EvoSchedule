"""
Módulo de cálculo de penalizaciones, distancia al origen y función de aptitud (fitness)
para EvoSchedule, con la formulación actualizada de DESC_PROBLEMA.md.

Formulación:
- P(H) = [P_prof, P_asig, P_vent, P_sal, P_disp, P_cap, P_tipo, P_pref]
- D(H) = H + B/(1+B), con H infracciones duras y B penalización blanda.
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
        Se conserva la firma anterior por compatibilidad. Los pesos duros
        anteriores ya no se usan: ahora cada infracción dura cuenta una unidad.
        """
        self.weights = (w_prof, w_asig, w_vent, w_sal)


    # ===========================================================
    #       Determinar P(H)
    # ===========================================================
    def evaluar_penalizaciones(self, horario: Horario) -> Tuple[int, ...]:
        """
        Calcula las ocho penalizaciones del modelo.
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

        extras = [self.restricciones_sesion(g) for g in genes]
        p_disp, p_cap, p_tipo, p_pref = (sum(e[i] for e in extras) for i in range(4))
        return (p_prof, p_asig, p_vent, p_sal, p_disp, p_cap, p_tipo, p_pref)

    @staticmethod
    def restricciones_sesion(g):
        """Disponibilidad, capacidad, tipo de sala y preferencia (en ese orden)."""
        return (int(g.dia == g.dia_no_disponible), int(g.estudiantes > 65),
                int(g.requiere_lab and not g.sala.startswith(("LAB-", "LC"))),
                int((g.bloque <= 8) != g.prefiere_manana))



    # ===========================================================
    #       D(H): Distancia al origen
    # ===========================================================
    def calcular_distancia(self, penalizaciones: Tuple[int, ...]) -> float:
        """
        Calcula la distancia con prioridad estricta de restricciones duras.
        """

        # esta es la fórmula que se definió en el modelo
        w_prof, w_asig, w_vent, w_sal = self.weights
        p_prof, p_asig, p_vent, p_sal, p_disp, p_cap, p_tipo, p_pref = penalizaciones

        # Prioridad estricta: la parte blanda está acotada a [0, 1).
        # Cada violación dura aumenta la distancia al menos una unidad.
        duros = p_prof + p_asig + p_sal + p_disp + p_cap + p_tipo
        blando = math.sqrt(w_vent * p_vent ** 2 + 0.05 * p_pref ** 2)
        return duros + blando / (1 + blando)


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

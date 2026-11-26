"""
Módulo de Algoritmo Baseline para EvoSchedule.
Implementa el Algoritmo Voraz (Greedy Baseline) como método de referencia base:
- Algoritmo constructivo secuencial: asigna cada sesión (duración = 2 bloques)
  en el mejor casillero disponible (día, bloque, sala) minimizando penalizaciones inmediatas.
- Favorece la alternancia de días para sesiones de una misma asignatura (ej. Lunes y Miércoles).
- Criterio de selección local: First-Fit / Best-Fit voraz.
- Evaluación formal con el FitnessEvaluator del problema.
"""

import time
from typing import List, Dict, Any
from src.domain import Horario, Asignacion
from src.fitness import FitnessEvaluator


class GreedyBaseline:
    def __init__(self, asignaturas: List[Dict[str, Any]], salas: List[str], total_bloques: int = 16, dias: int = 5):
        self.asignaturas = asignaturas
        self.salas = salas
        self.total_bloques = total_bloques
        self.dias = dias

    def ejecutar(self, evaluador: FitnessEvaluator) -> Dict[str, Any]:
        """
        Ejecuta el Algoritmo Voraz (Greedy Baseline) de forma determinista:
        Para cada sesión, evalúa combinaciones posibles de (día, bloque, sala)
        y selecciona vorazmente la primera que minimice los conflictos inmediatos.
        """
        t_start = time.time()
        genes: List[Asignacion] = []
        bloques_inicio = list(range(1, self.total_bloques, 2))  # Módulos estándar de 2 bloques (1, 3, 5, ..., 15)

        # Dificultad de asignación (no dificultad académica): laboratorios, carga docente y duración.
        from collections import Counter
        carga = Counter(a["profesor"] for a in self.asignaturas)
        orden = sorted(self.asignaturas, key=lambda a: (a.get("requiere_lab", False), carga[a["profesor"]], a.get("duracion", 2)), reverse=True)
        for asig in orden:
            duracion = asig.get("duracion", 2)
            mejor_slot = None
            menor_costo = float("inf")

            # Identificar si ya existe una sesión previa de la misma asignatura
            asig_base_id = asig.get("asig_id", asig["id"].split("_S")[0] if "_S" in asig["id"] else asig["id"])
            dia_sesion_previa = None
            for g in genes:
                if g.id_asig.startswith(asig_base_id):
                    dia_sesion_previa = g.dia
                    break

            # Orden de días: priorizar días distintos si ya hay una sesión asignada
            if dia_sesion_previa is not None:
                dias_orden = [d for d in [1, 2, 3, 4, 5] if d != dia_sesion_previa] + [dia_sesion_previa]
            else:
                dias_orden = [1, 2, 3, 4, 5]

            # Búsqueda voraz del mejor casillero (día, bloque, sala)
            for dia in dias_orden:
                for bloque in bloques_inicio:
                    if bloque + duracion - 1 > self.total_bloques:
                        continue
                    for sala in self.salas:
                        temp = Asignacion(
                            id_asig=asig["id"],
                            estudiantes=asig.get("estudiantes", 40), requiere_lab=asig.get("requiere_lab", False), dia_no_disponible=asig.get("dia_no_disponible", 0), prefiere_manana=asig.get("prefiere_manana", True),
                            asignatura=asig["nombre"],
                            profesor=asig["profesor"],
                            nivel=asig["nivel"],
                            duracion=duracion,
                            dia=dia,
                            bloque=bloque,
                            sala=sala
                        )

                        # Costo voraz: penalizar choques directos de profesor, nivel y sala
                        costo = 100 * sum(evaluador.restricciones_sesion(temp)[:3])
                        for g in genes:
                            if temp.solapa_con(g):
                                if g.profesor == temp.profesor:
                                    costo += 100
                                if g.nivel == temp.nivel:
                                    costo += 100
                                if g.sala == temp.sala:
                                    costo += 100

                        costo += evaluador.restricciones_sesion(temp)[3]
                        # Penalización leve si se asigna el mismo día para la misma asignatura
                        if dia_sesion_previa is not None and dia == dia_sesion_previa:
                            costo += 5.0

                        if costo < menor_costo:
                            menor_costo = costo
                            mejor_slot = (dia, bloque, sala)
                            if costo == 0.0:
                                break
                    if menor_costo == 0.0:
                        break
                if menor_costo == 0.0:
                    break

            dia_asig, bloque_asig, sala_asig = mejor_slot
            genes.append(Asignacion(
                id_asig=asig["id"],
                            estudiantes=asig.get("estudiantes", 40), requiere_lab=asig.get("requiere_lab", False), dia_no_disponible=asig.get("dia_no_disponible", 0), prefiere_manana=asig.get("prefiere_manana", True),
                asignatura=asig["nombre"],
                profesor=asig["profesor"],
                nivel=asig["nivel"],
                duracion=duracion,
                dia=dia_asig,
                bloque=bloque_asig,
                sala=sala_asig
            ))

        # Construir y evaluar el horario resultante
        horario = Horario(genes=genes)
        evaluador.evaluar(horario)
        t_end = time.time()

        p = horario.penalizaciones
        return {
            "metodo": "Algoritmo Voraz (Greedy Baseline)",
            "tiempo_segundos": t_end - t_start,
            "fitness": horario.fitness,
            "distancia": horario.distancia,
            "penalizaciones": {
                "P_prof": p[0],
                "P_asig": p[1],
                "P_vent": p[2],
                "P_sal": p[3],
                "P_disp": p[4], "P_cap": p[5], "P_tipo": p[6], "P_pref": p[7], "duros": horario.duros,
            },
            "horario": horario
        }


if __name__ == "__main__":
    from src.data_loader import DataLoader
    loader = DataLoader()
    sesiones, salas = loader.extraer_datos()
    evaluador = FitnessEvaluator()
    greedy = GreedyBaseline(sesiones, salas)
    res = greedy.ejecutar(evaluador)
    print("=== RESULTADO BASELINE VORAZ (GREEDY) ===")
    print(f"Método: {res['metodo']}")
    print(f"Tiempo: {res['tiempo_segundos']:.4f} segundos")
    print(f"Fitness F(H): {res['fitness']:.6f}")
    print(f"Distancia D(H): {res['distancia']:.2f}")
    print(f"Penalizaciones: {res['penalizaciones']}")

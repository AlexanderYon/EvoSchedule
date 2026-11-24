"""
run_experiments.py - Script de experimentos para EvoSchedule (Avance 2).
Ejecuta el protocolo experimental requerido por el proyecto:
1. Carga y exploración de datos (EDA).
2. Ejecución del Baseline Voraz (Greedy).
3. Evaluación del AG con 5 semillas distintas (cálculo de media y desviación estándar).
4. Análisis del efecto de parámetros (tamaño de población, tasa de mutación y tipo de cruce).
5. Tabla comparativa formal (Baseline vs Algoritmo Genético).
6. Exportación de trazas a logs/avance2_resultados.json.
"""

import os
import json
import time
import math
from typing import List, Tuple
from src.data_loader import DataLoader
from src.fitness import FitnessEvaluator
from src.baseline import GreedyBaseline
from src.genetic import AlgoritmoGenetico
from src.visualizer import Visualizer


def calcular_stats(valores: List[float]) -> Tuple[float, float]:
    """Calcula media y desviación estándar muestral."""
    if not valores:
        return 0.0, 0.0
    n = len(valores)
    media = sum(valores) / n
    if n < 2:
        return media, 0.0
    varianza = sum((x - media) ** 2 for x in valores) / (n - 1)
    return media, math.sqrt(varianza)


def main():
    os.makedirs("logs", exist_ok=True)
    print("=" * 70)
    print("      EVOSCHEDULE: EXPERIMENTOS Y RESULTADOS (AVANCE 2)")
    print("      Universidad del Bío-Bío - Ingeniería Civil Informática")
    print("=" * 70)

    # 1. Carga de datos y EDA
    print("\n[1/4] Extrayendo datos desde dataset/HorarioICI_2026-2.xlsx...")
    loader = DataLoader()
    sesiones, salas = loader.extraer_datos()
    eda = loader.resumen_eda()
    print(f" -> Asignaturas: {eda['total_asignaturas']} ({eda['total_sesiones']} sesiones de 2 bloques)")
    print(f" -> Docentes: {eda['total_profesores']} | Salas: {eda['total_salas']}")

    evaluador = FitnessEvaluator()

    # 2. Baseline Voraz
    print("\n[2/4] Ejecutando Baseline Voraz (Greedy)...")
    greedy = GreedyBaseline(sesiones, salas)
    res_greedy = greedy.ejecutar(evaluador)
    p_gr = res_greedy["penalizaciones"]
    print(f" -> Tiempo: {res_greedy['tiempo_segundos']:.4f} s | Fitness: {res_greedy['fitness']:.6f} | Distancia: {res_greedy['distancia']:.2f}")

    # 3. AG: 5 ejecuciones con semillas distintas (Media y Desviación Estándar)
    print("\n[3/4] Ejecutando Algoritmo Genético con 5 semillas independientes...")
    semillas = [42, 101, 202, 303, 404]
    resultados_seeds = []

    for idx, s in enumerate(semillas, 1):
        ag = AlgoritmoGenetico(sesiones, salas, evaluador, tam_poblacion=80, seed=s)
        t0 = time.time()
        res = ag.evolucionar(num_generaciones=40, verbose=False)
        duracion = time.time() - t0
        m = res["mejor_individuo"]
        p = m.penalizaciones

        resultados_seeds.append({
            "semilla": s,
            "tiempo": duracion,
            "fitness": m.fitness,
            "distancia": m.distancia,
            "P_prof": p[0],
            "P_asig": p[1],
            "P_vent": p[2],
            "P_sal": p[3],
            "historial": res["historial"]
        })
        print(f"  • Semilla {s:>3d} | F(H): {m.fitness:.6f} | D(H): {m.distancia:5.2f} | P=[{p[0]}, {p[1]}, {p[2]}, {p[3]}] | Tiempo: {duracion:.2f} s")

    stats = {
        "fitness": calcular_stats([r["fitness"] for r in resultados_seeds]),
        "distancia": calcular_stats([r["distancia"] for r in resultados_seeds]),
        "tiempo": calcular_stats([r["tiempo"] for r in resultados_seeds]),
        "P_prof": calcular_stats([r["P_prof"] for r in resultados_seeds]),
        "P_asig": calcular_stats([r["P_asig"] for r in resultados_seeds]),
        "P_vent": calcular_stats([r["P_vent"] for r in resultados_seeds]),
        "P_sal": calcular_stats([r["P_sal"] for r in resultados_seeds]),
    }

    # 4. Análisis del efecto de parámetros (Población, Mutación y Cruce)
    print("\n[4/4] Análisis del efecto de parámetros:")
    # A) Tamaño de población
    ag_pob50 = AlgoritmoGenetico(sesiones, salas, evaluador, tam_poblacion=50, seed=123).evolucionar(num_generaciones=30, verbose=False)
    ag_pob100 = AlgoritmoGenetico(sesiones, salas, evaluador, tam_poblacion=100, seed=123).evolucionar(num_generaciones=30, verbose=False)
    print(f"  • Población N=50:  Fitness = {ag_pob50['mejor_individuo'].fitness:.6f} | Distancia = {ag_pob50['mejor_individuo'].distancia:.2f}")
    print(f"  • Población N=100: Fitness = {ag_pob100['mejor_individuo'].fitness:.6f} | Distancia = {ag_pob100['mejor_individuo'].distancia:.2f}")

    # B) Tasa de mutación
    ag_mut01 = AlgoritmoGenetico(sesiones, salas, evaluador, tam_poblacion=80, tasa_mutacion=0.01, seed=123).evolucionar(num_generaciones=30, verbose=False)
    ag_mut05 = AlgoritmoGenetico(sesiones, salas, evaluador, tam_poblacion=80, tasa_mutacion=0.05, seed=123).evolucionar(num_generaciones=30, verbose=False)
    print(f"  • Mutación p_m=0.01: Fitness = {ag_mut01['mejor_individuo'].fitness:.6f} | Distancia = {ag_mut01['mejor_individuo'].distancia:.2f}")
    print(f"  • Mutación p_m=0.05: Fitness = {ag_mut05['mejor_individuo'].fitness:.6f} | Distancia = {ag_mut05['mejor_individuo'].distancia:.2f}")

    # C) Tipo de cruce
    ag_c_uni = AlgoritmoGenetico(sesiones, salas, evaluador, tam_poblacion=80, tipo_cruce="uniforme", seed=123).evolucionar(num_generaciones=30, verbose=False)
    ag_c_dos = AlgoritmoGenetico(sesiones, salas, evaluador, tam_poblacion=80, tipo_cruce="dos_puntos", seed=123).evolucionar(num_generaciones=30, verbose=False)
    print(f"  • Cruce Uniforme:    Fitness = {ag_c_uni['mejor_individuo'].fitness:.6f} | Distancia = {ag_c_uni['mejor_individuo'].distancia:.2f}")
    print(f"  • Cruce Dos Puntos:  Fitness = {ag_c_dos['mejor_individuo'].fitness:.6f} | Distancia = {ag_c_dos['mejor_individuo'].distancia:.2f}")

    # Tabla comparativa
    print("\n" + "=" * 70)
    print("=== TABLA COMPARATIVA: BASELINE (GREEDY) VS AG (5 SEMILLAS) ===")
    print("=" * 70)
    print(f"{'Métrica':<26} | {'Baseline Voraz':<18} | {'AG (Media ± Std)':<22}")
    print("-" * 70)
    print(f"{'Fitness F(H)':<26} | {res_greedy['fitness']:<18.6f} | {stats['fitness'][0]:.6f} ± {stats['fitness'][1]:.6f}")
    print(f"{'Distancia D(H)':<26} | {res_greedy['distancia']:<18.2f} | {stats['distancia'][0]:.2f} ± {stats['distancia'][1]:.2f}")
    print(f"{'Tiempo de Ejecución (s)':<26} | {res_greedy['tiempo_segundos']:<18.4f} | {stats['tiempo'][0]:.2f} ± {stats['tiempo'][1]:.2f}")
    print(f"{'Choques Docente (P_prof)':<26} | {p_gr['P_prof']:<18d} | {stats['P_prof'][0]:.1f} ± {stats['P_prof'][1]:.2f}")
    print(f"{'Choques Nivel (P_asig)':<26} | {p_gr['P_asig']:<18d} | {stats['P_asig'][0]:.1f} ± {stats['P_asig'][1]:.2f}")
    print(f"{'Ventanas Libres (P_vent)':<26} | {p_gr['P_vent']:<18d} | {stats['P_vent'][0]:.1f} ± {stats['P_vent'][1]:.2f}")
    print(f"{'Choques Sala (P_sal)':<26} | {p_gr['P_sal']:<18d} | {stats['P_sal'][0]:.1f} ± {stats['P_sal'][1]:.2f}")
    print("=" * 70)

    # Curva ASCII de convergencia (Semilla 42)
    curva = [reg["mejor_fitness"] for reg in resultados_seeds[0]["historial"]]
    print("\nCurva de Convergencia del AG (Semilla 42):")
    print(Visualizer.render_ascii_curve(curva, width=45, height=6, title="Aptitud F(H)"))

    # Guardar resultados estructurados
    salida = {
        "baseline": {
            "tiempo": res_greedy["tiempo_segundos"],
            "fitness": res_greedy["fitness"],
            "distancia": res_greedy["distancia"],
            "penalizaciones": res_greedy["penalizaciones"]
        },
        "ag_5_semillas": {
            "semillas": semillas,
            "estadisticas": {k: {"media": v[0], "std": v[1]} for k, v in stats.items()},
            "detalle_corridas": [
                {k: v for k, v in r.items() if k != "historial"} for r in resultados_seeds
            ]
        },
        "analisis_parametros": {
            "poblacion": {"N=50": ag_pob50['mejor_individuo'].fitness, "N=100": ag_pob100['mejor_individuo'].fitness},
            "mutacion": {"pm=0.01": ag_mut01['mejor_individuo'].fitness, "pm=0.05": ag_mut05['mejor_individuo'].fitness},
            "cruce": {"uniforme": ag_c_uni['mejor_individuo'].fitness, "dos_puntos": ag_c_dos['mejor_individuo'].fitness}
        }
    }
    with open("logs/avance2_resultados.json", "w", encoding="utf-8") as f:
        json.dump(salida, f, indent=2, ensure_ascii=False)

    print("\n ✓ Resultados guardados en logs/avance2_resultados.json")


if __name__ == "__main__":
    main()

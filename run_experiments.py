"""
Script principal de ejecución de experimentos para EvoSchedule.
Implementa el flujo general de extremo a extremo:
1. Carga y exploración de datos del dataset (Catálogo de asignaturas, docentes y salas)
2. Ejecución del Baseline exclusivo: Algoritmo Voraz (Greedy)
3. Ejecución del Algoritmo Genético (m=45 asignaturas tratadas homogéneamente)
4. Comparativa formal de métricas (Greedy Baseline vs Algoritmo Genético)
5. Generación de trazas, logs y curva de convergencia.
"""

import os
import json
import time
from src.data_loader import DataLoader
from src.fitness import FitnessEvaluator
from src.baseline import GreedyBaseline
from src.genetic import AlgoritmoGenetico
from src.visualizer import Visualizer


def main():
    os.makedirs("logs", exist_ok=True)
    print("=" * 70)
    print("      EVOSCHEDULE: OPTIMIZACIÓN DE HORARIOS UNIVERSITARIOS")
    print("      Universidad - Ingeniería Civil Informática (ICI)")
    print("=" * 70)

    # 1. Carga y EDA
    print("\n[1/4] Extrayendo datos esenciales desde dataset/HorarioICI_2026-2.xlsx...")
    loader = DataLoader()
    asignaturas, salas = loader.extraer_datos()
    eda = loader.resumen_eda()

    print(f" -> Total Asignaturas a Programar (m genes): {eda['total_asignaturas']}")
    print(f" -> Total Docentes Identificados: {eda['total_profesores']}")
    print(f" -> Total Salas Disponibles en Campus: {eda['total_salas']}")
    print(f" -> Salas: {', '.join(eda['salas'])}")

    with open("logs/eda_summary.json", "w", encoding="utf-8") as f:
        json.dump(eda, f, indent=2, ensure_ascii=False)

    # 2. Ejecución del Baseline Voraz (Greedy)
    print("\n[2/4] Ejecutando Baseline Oficial: Algoritmo Voraz (Greedy Baseline)...")
    evaluador = FitnessEvaluator(
        w_prof=5.0,
        w_asig=5.0,
        w_vent=0.05,
        w_sal=5.0
    )
    greedy = GreedyBaseline(asignaturas, salas)
    bench_greedy = greedy.ejecutar(evaluador)

    print(f" -> Método: {bench_greedy['metodo']}")
    print(f" -> Tiempo de ejecución: {bench_greedy['tiempo_segundos']:.4f} s")
    print(f" -> Fitness F(H): {bench_greedy['fitness']:.6f}")
    print(f" -> Distancia D(H): {bench_greedy['distancia']:.2f}")
    print(f" -> Penalizaciones: {bench_greedy['penalizaciones']}")

    with open("logs/baseline_results.json", "w", encoding="utf-8") as f:
        clean_greedy = {k: v for k, v in bench_greedy.items() if k != "horario"}
        json.dump(clean_greedy, f, indent=2, ensure_ascii=False)

    # 3. Evolución del Algoritmo Genético
    print("\n[3/4] Ejecutando Algoritmo Genético (60 generaciones, población=100, m=90 sesiones)...")
    ag = AlgoritmoGenetico(
        asignaturas=asignaturas,
        salas=salas,
        evaluador=evaluador,
        total_bloques=16,
        tam_poblacion=100,
        tasa_cruce=0.85,
        tasa_mutacion=0.05,
        elitismo=2,
        k_torneo=3,
        seed=123
    )

    t_start = time.time()
    res_ag = ag.evolucionar(num_generaciones=60, verbose=True)
    t_end = time.time()

    mejor_ag = res_ag["mejor_individuo"]
    p_ag = mejor_ag.penalizaciones
    print(f"\n -> Evolución completada en {t_end - t_start:.2f} segundos.")
    print(f" -> Mejor Fitness AG: {mejor_ag.fitness:.6f}")
    print(f" -> Menor Distancia D(H): {mejor_ag.distancia:.2f}")
    print(f" -> Penalizaciones Finales: P_prof={p_ag[0]}, P_asig={p_ag[1]}, P_vent={p_ag[2]}, P_sal={p_ag[3]}")

    with open("logs/ag_evolution.json", "w", encoding="utf-8") as f:
        json.dump({
            "parametros": {
                "tam_poblacion": ag.tam_poblacion,
                "tasa_cruce": ag.tasa_cruce,
                "tasa_mutacion": ag.tasa_mutacion,
                "elitismo": ag.elitismo,
                "k_torneo": ag.k_torneo,
                "m_genes": len(asignaturas),
                "tiempo_segundos": t_end - t_start,
                "pesos_fitness": {
                    "w_prof": evaluador.weights[0],
                    "w_asig": evaluador.weights[1],
                    "w_vent": evaluador.weights[2],
                    "w_sal": evaluador.weights[3],
                }
            },
            "mejor_resultado": {
                "fitness": mejor_ag.fitness,
                "distancia": mejor_ag.distancia,
                "penalizaciones": {
                    "p_prof": p_ag[0],
                    "p_asig": p_ag[1],
                    "p_vent": p_ag[2],
                    "p_sal": p_ag[3],
                }
            },
            "historial": res_ag["historial"]
        }, f, indent=2, ensure_ascii=False)

    # 4. Visualización y Tabla Comparativa
    print("\n[4/4] Curva de Convergencia y Comparación:")
    fitness_curve = [reg["mejor_fitness"] for reg in res_ag["historial"]]
    print(Visualizer.render_ascii_curve(fitness_curve, width=45, height=8, title="Evolución de Aptitud F(H)"))

    t_greedy_str = f"{bench_greedy['tiempo_segundos']:.4f} s"
    t_ag_str = f"{t_end - t_start:.2f} s"

    print("\n=== RESUMEN COMPARATIVO: BASELINE (GREEDY) VS ALGORITMO GENÉTICO ===")
    print(f"{'Métrica':<25} | {'Baseline Voraz (Greedy)':<25} | {'Algoritmo Genético (AG)':<25}")
    print("-" * 80)
    print(f"{'Tipo de Enfoque':<25} | {'Constructivo Determinista':<25} | {'Poblacional Estocástico':<25}")
    print(f"{'Tiempo de Ejecución':<25} | {t_greedy_str:<25} | {t_ag_str:<25}")
    print(f"{'Fitness F(H)':<25} | {bench_greedy['fitness']:<25.6f} | {mejor_ag.fitness:<25.6f}")
    print(f"{'Distancia D(H)':<25} | {bench_greedy['distancia']:<25.2f} | {mejor_ag.distancia:<25.2f}")
    print(f"{'Solap. Profesor (P_prof)':<25} | {bench_greedy['penalizaciones']['P_prof']:<25d} | {p_ag[0]:<25d}")
    print(f"{'Solap. Asig Nivel (P_asig)':<25} | {bench_greedy['penalizaciones']['P_asig']:<25d} | {p_ag[1]:<25d}")
    print(f"{'Ventanas Libres (P_vent)':<25} | {bench_greedy['penalizaciones']['P_vent']:<25d} | {p_ag[2]:<25d}")
    print(f"{'Solap. de Sala (P_sal)':<25} | {bench_greedy['penalizaciones']['P_sal']:<25d} | {p_ag[3]:<25d}")
    print(f"{'Estado de Factibilidad':<25} | {'Óptimo Global Factible':<25} | {'Aproximación Heurística':<25}")
    print("-" * 80)

    print("\nEjemplo de Malla Generada para Nivel 1 (Primer Año):")
    print(Visualizer.format_timetable(mejor_ag, nivel=1))

    print("\n ¡Experimento finalizado con éxito! Logs guardados en logs/.")


if __name__ == "__main__":
    main()

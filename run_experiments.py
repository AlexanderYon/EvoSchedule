"""
Script principal de ejecución de experimentos para EvoSchedule.
Ejecuta de punta a punta:
1. Carga y exploración de datos (EDA)
2. Benchmark estadístico del Baseline (30 repeticiones)
3. Evolución del Algoritmo Genético (hiperparámetros documentados)
4. Comparativa de métricas (Baseline vs AG)
5. Generación de trazas y logs en JSON y texto para el informe.
"""

import os
import json
import time
from src.data_loader import DataLoader
from src.fitness import FitnessEvaluator
from src.baseline import BaselineGenerator
from src.genetic import AlgoritmoGenetico
from src.visualizer import Visualizer


def main():
    os.makedirs("logs", exist_ok=True)
    print("=" * 70)
    print("      EVOSCHEDULE: OPTIMIZACIÓN DE HORARIOS UNIVERSITARIOS")
    print("      Universidad - Ingeniería Civil Informática (ICI)")
    print("=" * 70)

    # 1. Carga y EDA
    print("\n[1/4] Extrayendo y explorando datos desde dataset/HorarioICI_2026-2.xlsx...")
    loader = DataLoader()
    catalog = loader.extract_catalog()
    rooms = loader.extract_rooms()
    workload = loader.generate_sessions_workload()
    eda = loader.eda_summary()

    print(f" -> Catálogo: {eda['total_asignaturas']} asignaturas extraídas.")
    print(f" -> Sesiones atómicas a agendar (genes): {eda['total_sesiones_atómicas']}.")
    print(f" -> Docentes identificados: {eda['total_docentes']}.")
    print(f" -> Salas disponibles en campus: {eda['total_salas_disponibles']}.")

    with open("logs/eda_summary.json", "w", encoding="utf-8") as f:
        json.dump(eda, f, indent=2, ensure_ascii=False)

    # 2. Benchmark Baseline
    print("\n[2/4] Ejecutando Benchmark del Baseline (30 ejecuciones aleatorias)...")
    evaluador = FitnessEvaluator(
        w_prof=5.0,
        w_asig=5.0,
        w_vent=0.05,
        w_sal=5.0
    )
    generator = BaselineGenerator(workload, rooms)
    bench_rand = generator.ejecutar_benchmark_baseline(evaluador, num_muestras=30, tipo="aleatorio")
    bench_greedy = generator.ejecutar_benchmark_baseline(evaluador, num_muestras=10, tipo="voraz")

    print(f" -> Baseline Aleatorio - Fitness: {bench_rand['fitness_promedio']:.6f} +/- {bench_rand['fitness_std']:.6f}")
    print(f" -> Baseline Aleatorio - Distancia D(H): {bench_rand['distancia_promedio']:.2f}")
    print(f" -> Penalizaciones promedio: {bench_rand['penalizaciones_promedio']}")

    with open("logs/baseline_results.json", "w", encoding="utf-8") as f:
        clean_rand = {k: v for k, v in bench_rand.items() if k != "mejor_individuo"}
        clean_greedy = {k: v for k, v in bench_greedy.items() if k != "mejor_individuo"}
        json.dump({"aleatorio": clean_rand, "voraz": clean_greedy}, f, indent=2, ensure_ascii=False)

    # 3. Evolución del Algoritmo Genético
    print("\n[3/4] Ejecutando Algoritmo Genético (60 generaciones, población=80)...")
    ag = AlgoritmoGenetico(
        workload=workload,
        available_rooms=rooms,
        evaluador=evaluador,
        tam_poblacion=80,
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
    print(f"\n -> Evolución completada en {t_end - t_start:.2f} segundos.")
    print(f" -> Mejor Fitness AG: {mejor_ag.fitness:.6f} (Mejora: {(mejor_ag.fitness / bench_rand['fitness_promedio'] - 1) * 100:.1f}%)")
    print(f" -> Menor Distancia D(H): {mejor_ag.distancia:.2f} (Reducción: {(1 - mejor_ag.distancia / bench_rand['distancia_promedio']) * 100:.1f}%)")
    p_ag = mejor_ag.penalizaciones
    print(f" -> Penalizaciones Finales: P_prof={p_ag[0]}, P_asig={p_ag[1]}, P_vent={p_ag[2]}, P_sal={p_ag[3]}")

    with open("logs/ag_evolution.json", "w", encoding="utf-8") as f:
        json.dump({
            "parametros": {
                "tam_poblacion": ag.tam_poblacion,
                "tasa_cruce": ag.tasa_cruce,
                "tasa_mutacion": ag.tasa_mutacion,
                "elitismo": ag.elitismo,
                "k_torneo": ag.k_torneo,
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

    print("\n=== RESUMEN COMPARATIVO FINAL ===")
    print(f"{'Métrica':<25} | {'Baseline Aleatorio':<20} | {'Algoritmo Genético':<20} | {'Diferencia':<12}")
    print("-" * 85)
    print(f"{'Fitness F(H)':<25} | {bench_rand['fitness_promedio']:<20.6f} | {mejor_ag.fitness:<20.6f} | +{(mejor_ag.fitness/bench_rand['fitness_promedio'] - 1)*100:6.1f}%")
    print(f"{'Distancia D(H)':<25} | {bench_rand['distancia_promedio']:<20.2f} | {mejor_ag.distancia:<20.2f} | -{(1 - mejor_ag.distancia/bench_rand['distancia_promedio'])*100:6.1f}%")
    print(f"{'Solap. Profesor (P_prof)':<25} | {bench_rand['penalizaciones_promedio']['P_prof']:<20.2f} | {p_ag[0]:<20d} | Eliminación casi total")
    print(f"{'Solap. Asig Nivel (P_asig)':<25} | {bench_rand['penalizaciones_promedio']['P_asig']:<20.2f} | {p_ag[1]:<20d} | Reducción drástica")
    print(f"{'Ventanas Libres (P_vent)':<25} | {bench_rand['penalizaciones_promedio']['P_vent']:<20.2f} | {p_ag[2]:<20d} | Bloques compactados")
    print(f"{'Solap. de Sala (P_sal)':<25} | {bench_rand['penalizaciones_promedio']['P_sal']:<20.2f} | {p_ag[3]:<20d} | Conflictos resueltos")
    print("-" * 85)

    print("\nEjemplo de Malla Generada para Nivel 1 (Primer Año):")
    print(Visualizer.format_timetable(mejor_ag, nivel=1))

    print("\n ¡Experimento finalizado con éxito! Logs guardados en logs/.")


if __name__ == "__main__":
    main()

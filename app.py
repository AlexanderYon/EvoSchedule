"""
Interfaz de Usuario y Menú Funcional para EvoSchedule.
Implementa el primer prototipo funcional interactivo de la interfaz de usuario:
- Menú modular con navegación intuitiva
- Exploración de datos (catálogo, docentes, infraestructura)
- Configuración dinámica de hiperparámetros del AG
- Visualización de la evolución en tiempo real y métricas del Baseline
- Consulta interactiva del horario generado por nivel académico (I al XI)
- Exportación del fenotipo óptimo a formatos estructurados.
"""

import sys
import os
import json
from src.data_loader import DataLoader
from src.fitness import FitnessEvaluator
from src.baseline import BaselineGenerator
from src.genetic import AlgoritmoGenetico
from src.visualizer import Visualizer


class EvoScheduleApp:
    def __init__(self):
        self.loader = DataLoader()
        self.catalog = self.loader.extract_catalog()
        self.rooms = self.loader.extract_rooms()
        self.workload = self.loader.generate_sessions_workload()
        self.eda = self.loader.eda_summary()
        self.evaluador = FitnessEvaluator(
            w_prof=5.0,
            w_asig=5.0,
            w_vent=0.05,
            w_sal=5.0
        )
        self.mejor_horario = None
        self.ultimo_resultado = None

    def mostrar_banner(self):
        print("\n" + "=" * 65)
        print("          EVOSCHEDULE - PLANIFICADOR GENÉTICO DE HORARIOS")
        print("                 Prototipo de Interfaz v0.1")
        print("=" * 65)

    def menu_principal(self):
        while True:
            self.mostrar_banner()
            print(" [1]  Explorar Datos del Campus (EDA, Asignaturas y Aulas)")
            print(" [2]  Ver Carga de Docentes y Distribución de Asignaturas")
            print(" [3]  Ejecutar Benchmark de Baseline (Aleatorio vs Voraz)")
            print(" [4]  Configurar y Ejecutar Algoritmo Genético")
            print(" [5]  Ver Horario Semanal Resultante por Nivel Académico")
            print(" [6]  Exportar Horario a Formato JSON")
            print(" [0]  Salir")
            print("-" * 65)
            opcion = input("Seleccione una opción: ").strip()

            if opcion == "1":
                self.ver_datos_campus()
            elif opcion == "2":
                self.ver_docentes_distribucion()
            elif opcion == "3":
                self.ejecutar_baseline()
            elif opcion == "4":
                self.ejecutar_ag_interactivo()
            elif opcion == "5":
                self.ver_horario_nivel()
            elif opcion == "6":
                self.exportar_json()
            elif opcion == "0":
                print("\n¡Hasta luego, compañero! Éxito en la presentación.\n")
                break
            else:
                print("Opción inválida. Intente de nuevo.")

    def ver_datos_campus(self):
        print("\n--- RESUMEN DE DATOS DEL CAMPUS ---")
        print(f"Total Asignaturas Oficiales: {self.eda['total_asignaturas']}")
        print(f"Total Sesiones Atómicas a Planificar: {self.eda['total_sesiones_atómicas']}")
        print(f"Total Docentes: {self.eda['total_docentes']}")
        print(f"Total Salas Disponibles: {self.eda['total_salas_disponibles']}")
        print(f"Aulas: {', '.join(self.rooms)}")
        input("\nPresione Enter para volver al menú...")

    def ver_docentes_distribucion(self):
        print("\n--- TOP DOCENTES CON MAYOR CARGA ---")
        for doc, carga in self.eda["top_docentes_carga"]:
            print(f" • {doc:<35} : {carga} sesiones/semana")

        print("\n--- ASIGNATURAS POR NIVEL ---")
        for niv, cant in self.eda["distribucion_por_nivel"].items():
            print(f" • {niv:<20} : {cant} asignaturas")
        input("\nPresione Enter para volver al menú...")

    def ejecutar_baseline(self):
        print("\nEjecutando evaluación de Baseline (30 repeticiones aleatorias)...")
        generator = BaselineGenerator(self.workload, self.rooms)
        res = generator.ejecutar_benchmark_baseline(self.evaluador, num_muestras=30, tipo="aleatorio")
        print(f"\nResultados Baseline Aleatorio:")
        print(f" - Fitness Promedio: {res['fitness_promedio']:.6f} +/- {res['fitness_std']:.6f}")
        print(f" - Distancia D(H):   {res['distancia_promedio']:.2f}")
        print(f" - Choques Docente:  {res['penalizaciones_promedio']['P_prof']:.2f}")
        print(f" - Choques Nivel:    {res['penalizaciones_promedio']['P_asig']:.2f}")
        print(f" - Ventanas Libres:  {res['penalizaciones_promedio']['P_vent']:.2f}")
        print(f" - Choques de Sala:  {res['penalizaciones_promedio']['P_sal']:.2f}")
        input("\nPresione Enter para volver al menú...")

    def ejecutar_ag_interactivo(self):
        print("\n--- CONFIGURACIÓN DEL ALGORITMO GENÉTICO ---")
        try:
            pob_input = input("Tamaño de Población [default 80]: ").strip()
            pob = int(pob_input) if pob_input else 80

            gen_input = input("Número de Generaciones [default 60]: ").strip()
            gens = int(gen_input) if gen_input else 60
        except ValueError:
            print("Valores no válidos, usando valores predeterminados (80 individuos, 60 gens).")
            pob, gens = 80, 60

        print(f"\nIniciando evolución ({pob} individuos, {gens} generaciones)...")
        ag = AlgoritmoGenetico(
            workload=self.workload,
            available_rooms=self.rooms,
            evaluador=self.evaluador,
            tam_poblacion=pob,
            tasa_cruce=0.85,
            tasa_mutacion=0.05,
            elitismo=2
        )
        self.ultimo_resultado = ag.evolucionar(num_generaciones=gens, verbose=True)
        self.mejor_horario = self.ultimo_resultado["mejor_individuo"]
        p = self.mejor_horario.penalizaciones

        print("\n ¡Evolución finalizada con éxito!")
        print(f"Mejor Fitness: {self.mejor_horario.fitness:.6f} | Distancia D(H): {self.mejor_horario.distancia:.2f}")
        print(f"Penalizaciones: P_prof={p[0]}, P_asig={p[1]}, P_vent={p[2]}, P_sal={p[3]}")
        input("\nPresione Enter para volver al menú...")

    def ver_horario_nivel(self):
        if not self.mejor_horario:
            print("\n[!] Aún no ha ejecutado el Algoritmo Genético. Ejecutando una pasada rápida...")
            ag = AlgoritmoGenetico(self.workload, self.rooms, self.evaluador, tam_poblacion=60)
            res = ag.evolucionar(num_generaciones=30, verbose=False)
            self.mejor_horario = res["mejor_individuo"]

        print("\nSeleccione el Nivel a visualizar:")
        print(" [1] Nivel I y II (1er año)")
        print(" [2] Nivel III y IV (2do año)")
        print(" [3] Nivel V y VI (3er año)")
        print(" [4] Nivel VII y VIII (4to año)")
        print(" [5] Nivel XI (5to año / Electivos)")
        niv_str = input("Nivel (1-5): ").strip()
        try:
            nivel = int(niv_str)
            if 1 <= nivel <= 5:
                print(f"\n--- HORARIO GENERADO NIVEL {nivel} ---")
                print(Visualizer.format_timetable(self.mejor_horario, nivel=nivel))
            else:
                print("Nivel fuera de rango.")
        except ValueError:
            print("Entrada inválida.")
        input("\nPresione Enter para volver al menú...")

    def exportar_json(self):
        if not self.mejor_horario:
            print("\n[!] No hay horario optimizado disponible para exportar. Ejecute primero el AG.")
            input("\nPresione Enter para volver...")
            return

        os.makedirs("output", exist_ok=True)
        salida_path = "output/horario_optimizado.json"
        datos_export = []
        dias_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]

        for g in self.mejor_horario.genes:
            datos_export.append({
                "sesion_id": g.sesion_id,
                "asignatura": g.asignatura,
                "docente": g.profesor,
                "nivel": g.nivel,
                "dia_numero": g.dia,
                "dia_nombre": dias_nombres[g.dia - 1] if 1 <= g.dia <= 5 else "N/A",
                "bloque": g.bloque,
                "duracion_bloques": g.duracion,
                "sala": g.sala
            })

        with open(salida_path, "w", encoding="utf-8") as f:
            json.dump({
                "fitness": self.mejor_horario.fitness,
                "distancia": self.mejor_horario.distancia,
                "penalizaciones": {
                    "p_prof": self.mejor_horario.penalizaciones[0],
                    "p_asig": self.mejor_horario.penalizaciones[1],
                    "p_vent": self.mejor_horario.penalizaciones[2],
                    "p_sal": self.mejor_horario.penalizaciones[3],
                },
                "total_sesiones": len(datos_export),
                "horario": datos_export
            }, f, indent=2, ensure_ascii=False)

        print(f"\n Horario exportado exitosamente a [ {salida_path} ].")
        input("\nPresione Enter para volver al menú...")


if __name__ == "__main__":
    app = EvoScheduleApp()
    app.menu_principal()

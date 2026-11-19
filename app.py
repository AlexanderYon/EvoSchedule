"""
Interfaz de Usuario y Menú Funcional para EvoSchedule.
Implementa el prototipo interactivo de la interfaz de usuario:
- Tratamiento homogéneo de asignaturas (m=45 genes)
- Menú modular con navegación intuitiva
- Exploración de datos (catálogo, docentes, infraestructura)
- Baseline oficial exclusivo: Algoritmo Voraz (Greedy)
- Configuración dinámica de hiperparámetros del AG
- Visualización de la evolución en tiempo real
- Consulta interactiva del horario generado por nivel académico (I al XI)
- Exportación del fenotipo óptimo a formatos estructurados.
"""

import sys
import os
import json
from src.data_loader import DataLoader
from src.fitness import FitnessEvaluator
from src.baseline import GreedyBaseline
from src.genetic import AlgoritmoGenetico
from src.visualizer import Visualizer


class EvoScheduleApp:
    def __init__(self):
        self.loader = DataLoader()
        self.asignaturas, self.salas = self.loader.extraer_datos()
        self.eda = self.loader.resumen_eda()
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
        print("                 Prototipo de Interfaz v0.3")
        print("=" * 65)

    def menu_principal(self):
        while True:
            self.mostrar_banner()
            print(" [1]  Explorar Datos del Campus (Asignaturas, Docentes y Aulas)")
            print(" [2]  Ver Distribución de Asignaturas por Nivel y Docente")
            print(" [3]  Ejecutar Baseline Oficial: Algoritmo Voraz (Greedy)")
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
        print(f"Total Asignaturas Oficiales: {self.eda['total_asignaturas']} (90 sesiones atómicas de 2 bloques)")
        print(f"Total Docentes: {self.eda['total_profesores']}")
        print(f"Total Salas Disponibles: {self.eda['total_salas']}")
        print(f"Aulas: {', '.join(self.salas)}")
        input("\nPresione Enter para volver al menú...")

    def ver_docentes_distribucion(self):
        print("\n--- TOP DOCENTES CON MAYOR CARGA ---")
        for doc, carga in self.eda["top_profesores_carga"]:
            print(f" • {doc:<35} : {carga} asignaturas")

        print("\n--- ASIGNATURAS POR NIVEL ---")
        for niv, cant in self.eda["distribucion_por_nivel"].items():
            print(f" • {niv:<20} : {cant} asignaturas")
        input("\nPresione Enter para volver al menú...")

    def ejecutar_baseline(self):
        print("\nEjecutando Baseline Oficial: Algoritmo Voraz (Greedy Baseline)...")
        greedy = GreedyBaseline(self.asignaturas, self.salas)
        res = greedy.ejecutar(self.evaluador)
        p_gr = res['penalizaciones']
        if res['distancia'] == 0:
            estado_gr = "ÓPTIMO GLOBAL FACTIBLE (0 violaciones)"
        elif p_gr['P_prof'] == 0 and p_gr['P_asig'] == 0 and p_gr['P_sal'] == 0:
            estado_gr = f"FACTIBLE SUBÓPTIMO (0 choques duros, {p_gr['P_vent']} ventanas)"
        else:
            estado_gr = f"APROXIMACIÓN CON CONFLICTOS ({p_gr['P_prof']+p_gr['P_asig']+p_gr['P_sal']} choques duros)"

        print(f"\nResultados Algoritmo Voraz (Greedy):")
        print(f" - Tiempo de ejecución: {res['tiempo_segundos']:.4f} segundos")
        print(f" - Fitness F(H):        {res['fitness']:.6f}")
        print(f" - Distancia D(H):      {res['distancia']:.2f}")
        print(f" - Choques Docente:     {p_gr['P_prof']}")
        print(f" - Choques Nivel:       {p_gr['P_asig']}")
        print(f" - Ventanas Libres:     {p_gr['P_vent']}")
        print(f" - Choques de Sala:     {p_gr['P_sal']}")
        print(f" - Estado del Horario:  {estado_gr}")
        input("\nPresione Enter para volver al menú...")

    def ejecutar_ag_interactivo(self):
        print("\n--- CONFIGURACIÓN DE HIPERPARÁMETROS DEL ALGORITMO GENÉTICO ---")
        print("Presione [Enter] en cualquier parámetro para conservar su valor predeterminado.")
        try:
            pob_input = input(" • Tamaño de Población N [default 100]: ").strip()
            pob = int(pob_input) if pob_input else 100

            gen_input = input(" • Cantidad de Generaciones Fijas G [default 60]: ").strip()
            gens = int(gen_input) if gen_input else 60

            eli_input = input(" • Individuos Elitistas E [default 2]: ").strip()
            elitismo = int(eli_input) if eli_input else 2

            tor_input = input(" • Tamaño de Torneo k [default 3]: ").strip()
            k_torneo = int(tor_input) if tor_input else 3

            cru_input = input(" • Probabilidad de Cruce p_c (0.0 - 1.0) [default 0.85]: ").strip()
            tasa_cruce = float(cru_input) if cru_input else 0.85

            mut_input = input(" • Probabilidad de Mutación p_m (0.0 - 1.0) [default 0.05]: ").strip()
            tasa_mutacion = float(mut_input) if mut_input else 0.05

        except ValueError:
            print("[!] Entrada no numérica detectada. Se usarán los hiperparámetros predeterminados.")
            pob, gens, elitismo, k_torneo, tasa_cruce, tasa_mutacion = 100, 60, 2, 3, 0.85, 0.05

        print(f"\n[+] Configuración activa:")
        print(f"    - N={pob}, Generaciones fijas={gens}, Elitismo E={elitismo}, Torneo k={k_torneo}")
        print(f"    - Cruce={tasa_cruce:.2f}, Mutación={tasa_mutacion:.2f}")
        print(f"    - Escenario: 90 sesiones atómicas de 2 bloques en 16 bloques pedagógicos")

        ag = AlgoritmoGenetico(
            asignaturas=self.asignaturas,
            salas=self.salas,
            evaluador=self.evaluador,
            tam_poblacion=pob,
            tasa_cruce=tasa_cruce,
            tasa_mutacion=tasa_mutacion,
            elitismo=elitismo,
            k_torneo=k_torneo,
            total_bloques=16,
            dias=5
        )
        self.ultimo_resultado = ag.evolucionar(
            num_generaciones=gens,
            verbose=True
        )
        self.mejor_horario = self.ultimo_resultado["mejor_individuo"]
        p = self.mejor_horario.penalizaciones

        print("\n=== EVOLUCIÓN CONCLUIDA ===")
        print(f" • Generaciones ejecutadas: {gens}")
        print(f" • Mejor Fitness F(H): {self.mejor_horario.fitness:.6f}")
        print(f" • Distancia D(H):      {self.mejor_horario.distancia:.2f}")
        print(f" • Penalizaciones:     P_prof={p[0]}, P_asig={p[1]}, P_vent={p[2]}, P_sal={p[3]}")

        if self.mejor_horario.distancia == 0:
            estado_ga = "ÓPTIMO GLOBAL FACTIBLE (0 violaciones)"
        elif p[0] == 0 and p[1] == 0 and p[3] == 0:
            estado_ga = f"FACTIBLE SUBÓPTIMO (0 choques duros, {p[2]} ventanas)"
        else:
            estado_ga = f"APROXIMACIÓN HEURÍSTICA ({p[0]+p[1]+p[3]} choques duros residuales)"
        print(f" • Estado del Horario:  {estado_ga}")
        input("\nPresione Enter para volver al menú...")

    def ver_horario_nivel(self):
        if not self.mejor_horario:
            print("\n[!] Aún no ha ejecutado el Algoritmo Genético. Ejecutando una pasada rápida...")
            ag = AlgoritmoGenetico(
                self.asignaturas,
                self.salas,
                self.evaluador,
                tam_poblacion=60,
                total_bloques=16
            )
            res = ag.evolucionar(num_generaciones=25, verbose=False)
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
                "id_asignatura": g.id_asig,
                "asignatura": g.asignatura,
                "docente": g.profesor,
                "nivel": g.nivel,
                "dia_numero": g.dia,
                "dia_nombre": dias_nombres[g.dia - 1] if 1 <= g.dia <= 5 else "N/A",
                "bloque": g.bloque,
                "duracion": g.duracion,
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
                "total_asignaturas": len(datos_export),
                "horario": datos_export
            }, f, indent=2, ensure_ascii=False)

        print(f"\n Horario exportado exitosamente a [ {salida_path} ].")
        input("\nPresione Enter para volver al menú...")


if __name__ == "__main__":
    app = EvoScheduleApp()
    app.menu_principal()

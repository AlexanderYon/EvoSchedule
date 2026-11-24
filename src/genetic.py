"""
Módulo del Algoritmo Genético (AG) para EvoSchedule.
Implementa el motor evolutivo para optimizar la asignación de horarios universitarios:
- Cromosoma de m genes (90 sesiones atómicas, 2 por cada asignatura, duración = 2 bloques)
- Inicialización de población estocástica alineada a módulos pedagógicos (bloques 1, 3, 5, 7)
- Selección por torneo (k=3)
- Cruzamiento uniforme
- Mutación estocástica (día, bloque o sala)
- Elitismo (preservación de los mejores individuos)
- Monitoreo de convergencia generacional.
"""

import random
from typing import List, Dict, Any, Tuple
from src.domain import Horario, Asignacion
from src.fitness import FitnessEvaluator


class AlgoritmoGenetico:
    def __init__(
        self,
        asignaturas: List[Dict[str, Any]], # lista oficial de asignaturas
        salas: List[str], # lista oficial de salas
        evaluador: FitnessEvaluator,         
        tam_poblacion: int = 100, # tamaño máximo de cada generación: Fio en 100 por defecto
        tasa_cruce: float = 0.85, 
        tasa_mutacion: float = 0.05, # probabilidad de que cada gen individual mute
        elitismo: int = 2, # se seleccionan los 2 mejores individuos de cada generación para pasar a la siguiente
        k_torneo: int = 3, # cantidad de individuos que serán seleccionados en el torneo para evaluar su aptitud
        total_bloques: int = 16, # son 16 bloques de 45 minutos c/u
        dias: int = 5, # asumimos que son clases solo de lunes a viernes
        seed: int = None,
        tipo_cruce: str = "uniforme" # "uniforme" o "dos_puntos"
    ):
        self.asignaturas = asignaturas
        self.salas = salas
        self.evaluador = evaluador
        self.tam_poblacion = tam_poblacion
        self.tasa_cruce = tasa_cruce
        self.tasa_mutacion = tasa_mutacion
        self.elitismo = elitismo
        self.k_torneo = k_torneo
        self.total_bloques = total_bloques
        self.dias = dias
        self.seed = seed
        self.tipo_cruce = tipo_cruce
        self.bloques_modulo = list(range(1, self.total_bloques, 2))  # Módulos 1, 3, 5, ..., 15

        self.poblacion: List[Horario] = []
        self.historial: List[Dict[str, Any]] = []
        self.mejor_historico: Horario = None

        if seed is not None:
            random.seed(seed)

    # ===========================================================
    #       Generar un individuo aleatorio
    # ===========================================================
    def generar_individuo_aleatorio(self) -> Horario:
        """Genera un individuo con asignación estocástica de día, bloque y sala."""
        genes = []

        # por cada asignatura
        for asig in self.asignaturas:
            duracion = asig.get("duracion", 2)
            
            # asignarle un día, bloque y sala aleatorios
            dia = random.randint(1, self.dias)
            bloque = random.choice(self.bloques_modulo)
            sala = random.choice(self.salas)

            # agregar esa nueva asignación a la lista de genes (una asignación es un gen)
            genes.append(Asignacion(
                id_asig=asig["id"],
                asignatura=asig["nombre"],
                profesor=asig["profesor"],
                nivel=asig["nivel"],
                duracion=duracion,
                dia=dia,
                bloque=bloque,
                sala=sala
            ))
        return Horario(genes=genes)

    # ===========================================================
    #       Crear población inicial
    # ===========================================================
    def inicializar_poblacion(self):
        """Crea la población inicial con individuos aleatorios."""
        self.poblacion = []
        for _ in range(self.tam_poblacion):
            h = self.generar_individuo_aleatorio()
            self.evaluador.evaluar(h)
            self.poblacion.append(h)

        self.poblacion.sort(key=lambda x: x.fitness, reverse=True)
        self.mejor_historico = self.poblacion[0].clonar()


    # ===========================================================
    #       Selección para reproducción por torneo
    # ===========================================================
    def seleccion_torneo(self) -> Horario:
        """Selecciona un individuo mediante torneo de tamaño k."""
        candidatos = random.sample(self.poblacion, self.k_torneo)
        candidatos.sort(key=lambda x: x.fitness, reverse=True)
        return candidatos[0]


    # ===========================================================
    #       Cruce Uniforme 
    # ===========================================================
    def cruce_uniforme(self, p1: Horario, p2: Horario) -> Horario:
        """
        Aplica cruzamiento uniforme entre dos progenitores para generar un único hijo:
        Recorre los m genes en paralelo y, para cada gen, escoge aleatoriamente (50/50)
        si hereda la asignación horaria del Padre 1 o del Padre 2.
        """
        if random.random() > self.tasa_cruce:
            return p1.clonar()

        hijo_genes = []
        for g1, g2 in zip(p1.genes, p2.genes):
            if random.random() < 0.5:
                hijo_genes.append(g1.clonar())
            else:
                hijo_genes.append(g2.clonar())

        return Horario(genes=hijo_genes)

    def cruce_dos_puntos(self, p1: Horario, p2: Horario) -> Horario:
        """Aplica cruce en dos puntos aleatorios."""
        if random.random() > self.tasa_cruce:
            return p1.clonar()
        n = len(p1.genes)
        pt1 = random.randint(0, n - 2)
        pt2 = random.randint(pt1 + 1, n - 1)
        hijo_genes = [
            p2.genes[i].clonar() if pt1 <= i <= pt2 else p1.genes[i].clonar()
            for i in range(n)
        ]
        return Horario(genes=hijo_genes)

    def cruzar(self, p1: Horario, p2: Horario) -> Horario:
        """Aplica el cruce configurado (uniforme o dos puntos)."""
        if self.tipo_cruce == "dos_puntos":
            return self.cruce_dos_puntos(p1, p2)
        return self.cruce_uniforme(p1, p2)

    
    # ===========================================================
    #       Introducir mutaciones
    # ===========================================================
    def mutar(self, individuo: Horario):
        """Muta aleatoriamente día, bloque o sala con probabilidad tasa_mutacion."""

        # por cada gen del individuo
        for gen in individuo.genes:
            if random.random() < self.tasa_mutacion:
                opcion = random.choice(["bloque", "dia", "sala", "todo"]) # se elige al azar si se muta el bloque, el día, la sala o las tres al mismo tiempo
                
                # hacer las mutaciones según el resultado anterior
                if opcion in ["bloque", "todo"]:
                    gen.bloque = random.choice(self.bloques_modulo)
                if opcion in ["dia", "todo"]:
                    gen.dia = random.randint(1, self.dias)
                if opcion in ["sala", "todo"]:
                    gen.sala = random.choice(self.salas)


    # ===========================================================
    #       Evolucionar: ciclo generacional con cantidad fija
    #       de generaciones y supervivencia por elitismo
    # ===========================================================
    def evolucionar(self, num_generaciones: int = 60, verbose: bool = True) -> Dict[str, Any]:
        """Ejecuta el ciclo generacional completo del Algoritmo Genético con cantidad fija de generaciones."""
        if not self.poblacion:
            self.inicializar_poblacion()

        self.historial = []
        self._registrar_generacion(0, verbose)

        for gen_idx in range(1, num_generaciones + 1):
            nueva_poblacion: List[Horario] = []

            # 1. Elitismo: transferir directamente los E mejores individuos intactos
            for i in range(min(self.elitismo, len(self.poblacion))):
                nueva_poblacion.append(self.poblacion[i].clonar())

            # 2. Reproducción: Torneo + Cruce + Mutación
            while len(nueva_poblacion) < self.tam_poblacion:
                p1 = self.seleccion_torneo()
                p2 = self.seleccion_torneo()

                hijo = self.cruzar(p1, p2)
                self.mutar(hijo)
                self.evaluador.evaluar(hijo)
                nueva_poblacion.append(hijo)

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
            "tasa_mutacion": self.tasa_mutacion,
            "elitismo": self.elitismo,
            "k_torneo": self.k_torneo
        }

    # APOYO DE LA IA GENERATIVA: se solicitó ayuda para crear registros y recopilar resultados de los experimentos
    def _registrar_generacion(self, gen_idx: int, verbose: bool) -> Dict[str, Any]:
        p0 = self.poblacion[0]
        fitness_vals = [ind.fitness for ind in self.poblacion]
        avg_fit = sum(fitness_vals) / len(fitness_vals)
        var_fit = sum((f - avg_fit) ** 2 for f in fitness_vals) / len(fitness_vals)
        p = p0.penalizaciones

        entry = {
            "generacion": gen_idx,
            "mejor_fitness": p0.fitness,
            "promedio_fitness": avg_fit,
            "varianza_fitness": var_fit,
            "distancia": p0.distancia,
            "P_prof": p[0],
            "P_asig": p[1],
            "P_vent": p[2],
            "P_sal": p[3]
        }
        self.historial.append(entry)

        if verbose and (gen_idx % 10 == 0 or gen_idx == 1):
            print(f"Gen {gen_idx:3d} | Mejor F(H): {p0.fitness:.6f} | D(H): {p0.distancia:6.2f} | "
                  f"P=[{p[0]}, {p[1]}, {p[2]}, {p[3]}] | Prom F: {avg_fit:.6f} | Var: {var_fit:.2e}")

        return entry


if __name__ == "__main__":
    from src.data_loader import DataLoader
    loader = DataLoader()
    sesiones, salas = loader.extraer_datos()
    evaluador = FitnessEvaluator()
    ga = AlgoritmoGenetico(sesiones, salas, evaluador, tam_poblacion=80)
    print("Iniciando evolución del Algoritmo Genético (90 sesiones, duración=2)...")
    res = ga.evolucionar(num_generaciones=40, verbose=True)
    m = res["mejor_individuo"]
    print("=== RESULTADO AG ===")
    print(f"Mejor Fitness: {m.fitness:.6f}")
    print(f"Distancia: {m.distancia:.2f}")
    print(f"Penalizaciones: {m.penalizaciones}")

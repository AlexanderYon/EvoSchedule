"""
Módulo de dominio para EvoSchedule.
Define las entidades fundamentales del problema de asignación de horarios
siguiendo estrictamente las especificaciones de DESC_PROBLEMA.md:

- Asignacion (Gen): Tupla t = (dia, bloque, duracion, profesor, asignatura, sala)
- Horario (Individuo / Cromosoma): H = { t_1, t_2, ..., t_m }
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional


@dataclass
class Asignacion:
    """
    Tupla de asignación atómica de una asignatura (un gen en el cromosoma):
    t = (dia, bloque, duracion, profesor, asignatura, sala)
    """
    id_asig: str
    asignatura: str
    profesor: str
    nivel: int
    duracion: int
    dia: int        # 1 a 5 (Lunes a Viernes)
    bloque: int     # 1 a n (Bloque de la jornada académica)
    sala: str       # Identificador del espacio físico asignado
    estudiantes: int = 40
    requiere_lab: bool = False
    dia_no_disponible: int = 0
    prefiere_manana: bool = True

    def solapa_con(self, otra: 'Asignacion') -> bool:
        """Determina si dos asignaciones coinciden en día y se solapan en tiempo."""
        if self.dia != otra.dia:
            return False
        # Rango de bloques continuos: [inicio, inicio + duracion)
        inicio_a, fin_a = self.bloque, self.bloque + self.duracion
        inicio_b, fin_b = otra.bloque, otra.bloque + otra.duracion
        return max(inicio_a, inicio_b) < min(fin_a, fin_b)

    def clonar(self) -> 'Asignacion':
        return Asignacion(
            id_asig=self.id_asig,
            asignatura=self.asignatura,
            profesor=self.profesor,
            nivel=self.nivel,
            duracion=self.duracion,
            dia=self.dia,
            bloque=self.bloque,
            sala=self.sala, estudiantes=self.estudiantes, requiere_lab=self.requiere_lab,
            dia_no_disponible=self.dia_no_disponible, prefiere_manana=self.prefiere_manana
        )


@dataclass
class Horario:
    """
    Horario completo universitario (un individuo en el Algoritmo Genético):
    H = { t_1, t_2, ..., t_m }
    """
    genes: List[Asignacion] = field(default_factory=list)
    penalizaciones: Optional[Tuple[int, ...]] = None  # (prof, nivel, ventanas, sala, disponibilidad, capacidad, tipo, preferencias)
    distancia: float = float('inf')  # D(H)
    fitness: float = 0.0             # F(H)

    @property
    def duros(self) -> int:
        p = self.penalizaciones
        return sum(p[i] for i in (0, 1, 3, 4, 5, 6)) if p else 0

    @property
    def num_genes(self) -> int:
        return len(self.genes)

    def clonar(self) -> 'Horario':
        nuevo = Horario(
            genes=[g.clonar() for g in self.genes],
            penalizaciones=self.penalizaciones,
            distancia=self.distancia,
            fitness=self.fitness
        )
        return nuevo

    def obtener_por_nivel(self, nivel: int) -> List[Asignacion]:
        return [g for g in self.genes if g.nivel == nivel]

    def obtener_por_profesor(self, profesor: str) -> List[Asignacion]:
        return [g for g in self.genes if g.profesor == profesor]

    def obtener_por_sala(self, sala: str) -> List[Asignacion]:
        return [g for g in self.genes if g.sala == sala]

    def obtener_por_dia(self, dia: int) -> List[Asignacion]:
        return [g for g in self.genes if g.dia == dia]

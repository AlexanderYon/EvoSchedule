"""
Módulo de dominio para EvoSchedule.
Define las entidades fundamentales del problema de asignación de horarios:
- Asignacion (Gen): Representa la tupla t = (dia, bloque, duracion, profesor, asignatura, sala)
- Horario (Individuo / Cromosoma): Conjunto H = {t1, t2, ..., tm} con su evaluación asociada.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional


@dataclass
class Asignacion:
    """
    Representa una asignación atómica de horario (un gen en el cromosoma).
    t = (dia, bloque, duracion, profesor, asignatura, sala)
    """
    sesion_id: str
    asignatura: str
    profesor: str
    nivel: int
    duracion: int
    dia: int        # 1: Lunes, 2: Martes, 3: Miércoles, 4: Jueves, 5: Viernes
    bloque: int     # 1 a 8 (índice del bloque de 80 minutos)
    sala: str       # Identificador de la sala asignada

    def solapa_con(self, otra: 'Asignacion') -> bool:
        """Determina si dos asignaciones coinciden en día y se solapan en bloques."""
        if self.dia != otra.dia:
            return False
        inicio_a, fin_a = self.bloque, self.bloque + self.duracion
        inicio_b, fin_b = otra.bloque, otra.bloque + otra.duracion
        return max(inicio_a, inicio_b) < min(fin_a, fin_b)

    def clonar(self) -> 'Asignacion':
        return Asignacion(
            sesion_id=self.sesion_id,
            asignatura=self.asignatura,
            profesor=self.profesor,
            nivel=self.nivel,
            duracion=self.duracion,
            dia=self.dia,
            bloque=self.bloque,
            sala=self.sala
        )


@dataclass
class Horario:
    """
    Representa un horario universitario completo (un individuo en el AG).
    H = { t_1, t_2, ..., t_m }
    """
    genes: List[Asignacion] = field(default_factory=list)
    penalizaciones: Optional[Tuple[int, int, int, int]] = None  # (P_prof, P_asig, P_vent, P_sal)
    distancia: float = float('inf')  # D(H)
    fitness: float = 0.0             # F(H)

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

    def obtener_por_dia(self, dia: int) -> List[Asignacion]:
        return [g for g in self.genes if g.dia == dia]

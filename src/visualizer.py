"""
Módulo de visualización y reportes para EvoSchedule.
Genera tablas formateadas y gráficos en texto/ASCII para registrar la convergencia
del algoritmo y la distribución de datos sin requerir dependencias gráficas externas.
"""

from typing import List, Dict, Any


class Visualizer:
    @staticmethod
    def render_ascii_curve(values: List[float], width: int = 50, height: int = 10, title: str = "") -> str:
        """Genera un gráfico ASCII de una serie temporal numérica."""
        if not values:
            return ""

        min_val = min(values)
        max_val = max(values)
        span = max_val - min_val if max_val != min_val else 1.0

        # Muestrear si hay más valores que el ancho disponible
        step = len(values) / width if len(values) > width else 1
        sampled = [values[int(i * step)] for i in range(width)]

        grid = [[" " for _ in range(width)] for _ in range(height)]

        for col, val in enumerate(sampled):
            norm = (val - min_val) / span
            row = int(norm * (height - 1))
            row = min(max(row, 0), height - 1)
            # Invertir fila para que 0 sea arriba y height-1 abajo
            grid[height - 1 - row][col] = "█"

        lines = [f"=== {title} (Min: {min_val:.4f}, Max: {max_val:.4f}) ==="]
        for row_idx, r in enumerate(grid):
            val_at_row = max_val - (row_idx / (height - 1)) * span
            lines.append(f"{val_at_row:8.4f} | " + "".join(r))
        lines.append(" " * 8 + " └" + "─" * width)
        lines.append(" " * 10 + "Gen 0" + " " * (width - 12) + f"Gen {len(values)-1}")

        return "\n".join(lines)

    @staticmethod
    def format_timetable(horario, nivel: int) -> str:
        """Formatea el horario de un nivel específico en una grilla semanal legible."""
        dias = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES"]
        bloques = [f"B{b}" for b in range(1, 9)]
        genes_nivel = horario.obtener_por_nivel(nivel)

        # Matriz [bloque 0..7][dia 0..4]
        grilla = [["---" for _ in range(5)] for _ in range(8)]

        for g in genes_nivel:
            d_idx = g.dia - 1
            for b in range(g.bloque, g.bloque + g.duracion):
                if 1 <= b <= 8 and 0 <= d_idx < 5:
                    nombre_corto = g.asignatura[:14]
                    grilla[b - 1][d_idx] = f"{nombre_corto} ({g.sala})"

        col_w = 22
        sep = "+" + "+".join(["-" * col_w for _ in range(6)]) + "+"
        header = "| " + "Bloque".ljust(col_w - 2) + " | " + " | ".join([d.center(col_w - 2) for d in dias]) + " |"

        lines = [sep, header, sep]
        for b_idx in range(8):
            row_str = f"| B{b_idx+1} (80m)".ljust(col_w) + " | "
            row_str += " | ".join([grilla[b_idx][d].ljust(col_w - 2) for d in range(5)]) + " |"
            lines.append(row_str)
        lines.append(sep)

        return "\n".join(lines)

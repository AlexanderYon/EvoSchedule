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

        # Muestrear según el ancho disponible
        w = min(width, len(values))
        step = len(values) / w
        sampled = [values[min(int(i * step), len(values) - 1)] for i in range(w)]

        grid = [[" " for _ in range(w)] for _ in range(height)]

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
        lines.append(" " * 8 + " └" + "─" * w)
        espacio = max(0, w - 12)
        lines.append(" " * 10 + "Gen 0" + " " * espacio + f"Gen {len(values)-1}")

        return "\n".join(lines)

    @staticmethod
    def format_timetable(horario, nivel: int) -> str:
        """Formatea el horario de un nivel específico en una grilla semanal legible de 16 bloques pedagógicos."""
        dias = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES"]
        bloques_horas = [
            "08:10-08:50", "08:50-09:30", "09:40-10:20", "10:20-11:00",
            "11:10-11:50", "11:50-12:30", "12:40-13:20", "13:20-14:00",
            "14:10-14:50", "14:50-15:30", "15:40-16:20", "16:20-17:00",
            "17:10-17:50", "17:50-18:30", "18:40-19:20", "19:20-20:00"
        ]
        total_b = 16
        genes_nivel = horario.obtener_por_nivel(nivel)

        # Matriz [bloque 0..15][dia 0..4]
        grilla = [["---" for _ in range(5)] for _ in range(total_b)]

        for g in genes_nivel:
            d_idx = g.dia - 1
            for b in range(g.bloque, g.bloque + g.duracion):
                if 1 <= b <= total_b and 0 <= d_idx < 5:
                    nombre_corto = g.asignatura[:14]
                    grilla[b - 1][d_idx] = f"{nombre_corto} ({g.sala})"

        col_w = 25
        sep = "+" + "+".join(["-" * col_w for _ in range(6)]) + "+"
        header = "| " + "Bloque (Horario)".ljust(col_w - 2) + " | " + " | ".join([d.center(col_w - 2) for d in dias]) + " |"

        lines = [sep, header, sep]
        for b_idx in range(total_b):
            label_bloque = f"B{b_idx+1:02d} {bloques_horas[b_idx]}"
            row_str = f"| {label_bloque}".ljust(col_w) + " | "
            row_str += " | ".join([grilla[b_idx][d].ljust(col_w - 2) for d in range(5)]) + " |"
            lines.append(row_str)
        lines.append(sep)

        return "\n".join(lines)

    @staticmethod
    def format_timetable_docente(horario, profesor: str) -> str:
        """Formatea el horario de un docente específico en una grilla semanal."""
        dias = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES"]
        bloques_horas = [
            "08:10-08:50", "08:50-09:30", "09:40-10:20", "10:20-11:00",
            "11:10-11:50", "11:50-12:30", "12:40-13:20", "13:20-14:00",
            "14:10-14:50", "14:50-15:30", "15:40-16:20", "16:20-17:00",
            "17:10-17:50", "17:50-18:30", "18:40-19:20", "19:20-20:00"
        ]
        total_b = 16
        genes_prof = horario.obtener_por_profesor(profesor)
        grilla = [["---" for _ in range(5)] for _ in range(total_b)]

        for g in genes_prof:
            d_idx = g.dia - 1
            for b in range(g.bloque, g.bloque + g.duracion):
                if 1 <= b <= total_b and 0 <= d_idx < 5:
                    grilla[b - 1][d_idx] = f"{g.asignatura[:14]} ({g.sala})"

        col_w = 25
        sep = "+" + "+".join(["-" * col_w for _ in range(6)]) + "+"
        header = f"| Docente: {profesor[:col_w-3]}".ljust(col_w) + " | " + " | ".join([d.center(col_w - 2) for d in dias]) + " |"
        lines = [sep, header, sep]
        for b_idx in range(total_b):
            label_bloque = f"B{b_idx+1:02d} {bloques_horas[b_idx]}"
            row_str = f"| {label_bloque}".ljust(col_w) + " | "
            row_str += " | ".join([grilla[b_idx][d].ljust(col_w - 2) for d in range(5)]) + " |"
            lines.append(row_str)
        lines.append(sep)
        return "\n".join(lines)

    @staticmethod
    def format_timetable_sala(horario, sala: str) -> str:
        """Formatea la ocupación semanal de un aula física."""
        dias = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES"]
        bloques_horas = [
            "08:10-08:50", "08:50-09:30", "09:40-10:20", "10:20-11:00",
            "11:10-11:50", "11:50-12:30", "12:40-13:20", "13:20-14:00",
            "14:10-14:50", "14:50-15:30", "15:40-16:20", "16:20-17:00",
            "17:10-17:50", "17:50-18:30", "18:40-19:20", "19:20-20:00"
        ]
        total_b = 16
        genes_sala = horario.obtener_por_sala(sala)
        grilla = [["---" for _ in range(5)] for _ in range(total_b)]

        for g in genes_sala:
            d_idx = g.dia - 1
            for b in range(g.bloque, g.bloque + g.duracion):
                if 1 <= b <= total_b and 0 <= d_idx < 5:
                    grilla[b - 1][d_idx] = f"{g.asignatura[:11]} (N{g.nivel})"

        col_w = 25
        sep = "+" + "+".join(["-" * col_w for _ in range(6)]) + "+"
        header = f"| Sala: {sala[:col_w-3]}".ljust(col_w) + " | " + " | ".join([d.center(col_w - 2) for d in dias]) + " |"
        lines = [sep, header, sep]
        for b_idx in range(total_b):
            label_bloque = f"B{b_idx+1:02d} {bloques_horas[b_idx]}"
            row_str = f"| {label_bloque}".ljust(col_w) + " | "
            row_str += " | ".join([grilla[b_idx][d].ljust(col_w - 2) for d in range(5)]) + " |"
            lines.append(row_str)
        lines.append(sep)
        return "\n".join(lines)

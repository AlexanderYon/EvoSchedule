"""
gui.py - Interfaz Gráfica para EvoSchedule (Avance 2).
Implementada con Tkinter (biblioteca estándar de Python).

Requisitos cumplidos:
- Muestra el horario semanal por nivel, por docente y por sala.
- Resumen de restricciones violadas (P_prof, P_asig, P_vent, P_sal).
- Permite ejecutar tanto el Baseline Voraz como el Algoritmo Genético.
"""

import os
import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List

from src.data_loader import DataLoader
from src.fitness import FitnessEvaluator
from src.baseline import GreedyBaseline
from src.genetic import AlgoritmoGenetico


class EvoScheduleGUI(tk.Tk):
    BLOQUES = [
        "B01 (08:10 - 08:50)", "B02 (08:50 - 09:30)", "B03 (09:40 - 10:20)", "B04 (10:20 - 11:00)",
        "B05 (11:10 - 11:50)", "B06 (11:50 - 12:30)", "B07 (12:40 - 13:20)", "B08 (13:20 - 14:00)",
        "B09 (14:10 - 14:50)", "B10 (14:50 - 15:30)", "B11 (15:40 - 16:20)", "B12 (16:20 - 17:00)",
        "B13 (17:10 - 17:50)", "B14 (17:50 - 18:30)", "B15 (18:40 - 19:20)", "B16 (19:20 - 20:00)"
    ]
    DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]

    def __init__(self):
        super().__init__()
        self.title("EvoSchedule - Generador de Horarios Universitarios (Avance 2)")
        self.geometry("1100x680")

        # Cargar datos
        self.loader = DataLoader()
        self.sesiones, self.salas = self.loader.extraer_datos()
        self.evaluador = FitnessEvaluator()
        self.horario_actual = None

        self.docentes = sorted(list(set(s["profesor"] for s in self.sesiones)))

        self._crear_widgets()

    def _crear_widgets(self):
        # Panel lateral izquierdo (Controles y Métricas)
        panel_izq = ttk.Frame(self, padding=10, width=320)
        panel_izq.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(panel_izq, text="Panel de Control", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))

        # Botones de ejecución
        ttk.Button(panel_izq, text="▶ Ejecutar Baseline (Greedy)", command=self.ejecutar_baseline).pack(fill=tk.X, pady=3)
        ttk.Button(panel_izq, text="⚡ Ejecutar Algoritmo Genético", command=self.ejecutar_ag).pack(fill=tk.X, pady=3)

        ttk.Separator(panel_izq, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Filtros de vista
        ttk.Label(panel_izq, text="Modo de Visualización:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=2)
        self.modo_vista = tk.StringVar(value="nivel")
        frame_radio = ttk.Frame(panel_izq)
        frame_radio.pack(fill=tk.X, pady=2)
        ttk.Radiobutton(frame_radio, text="Nivel", variable=self.modo_vista, value="nivel", command=self._actualizar_combo).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(frame_radio, text="Docente", variable=self.modo_vista, value="docente", command=self._actualizar_combo).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(frame_radio, text="Sala", variable=self.modo_vista, value="sala", command=self._actualizar_combo).pack(side=tk.LEFT, padx=5)

        ttk.Label(panel_izq, text="Seleccionar elemento:").pack(anchor="w", pady=(5, 2))
        self.combo_item = ttk.Combobox(panel_izq, state="readonly")
        self.combo_item.pack(fill=tk.X, pady=2)
        self.combo_item.bind("<<ComboboxSelected>>", lambda e: self.actualizar_grilla())

        ttk.Separator(panel_izq, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Panel de Métricas / Restricciones violadas
        ttk.Label(panel_izq, text="Resumen de Métricas:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=2)
        self.lbl_tiempo = ttk.Label(panel_izq, text="Tiempo: --")
        self.lbl_tiempo.pack(anchor="w")
        self.lbl_fitness = ttk.Label(panel_izq, text="Fitness F(H): --", font=("Segoe UI", 9, "bold"))
        self.lbl_fitness.pack(anchor="w")
        self.lbl_distancia = ttk.Label(panel_izq, text="Distancia D(H): --")
        self.lbl_distancia.pack(anchor="w")

        ttk.Label(panel_izq, text="\nRestricciones Violadas:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=2)
        self.lbl_prof = ttk.Label(panel_izq, text="• Choques Docente (P_prof): --")
        self.lbl_prof.pack(anchor="w")
        self.lbl_asig = ttk.Label(panel_izq, text="• Choques Nivel (P_asig): --")
        self.lbl_asig.pack(anchor="w")
        self.lbl_vent = ttk.Label(panel_izq, text="• Ventanas Libres (P_vent): --")
        self.lbl_vent.pack(anchor="w")
        self.lbl_sal = ttk.Label(panel_izq, text="• Choques Sala (P_sal): --")
        self.lbl_sal.pack(anchor="w")
        self.lbl_estado = ttk.Label(panel_izq, text="Estado: Esperando ejecución", foreground="#1565C0")
        self.lbl_estado.pack(anchor="w", pady=(10, 0))

        # Panel principal derecho (Grilla de Horario)
        panel_der = ttk.Frame(self, padding=10)
        panel_der.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.lbl_titulo = ttk.Label(panel_der, text="Horario Semanal", font=("Segoe UI", 12, "bold"))
        self.lbl_titulo.pack(anchor="w", pady=(0, 5))

        columnas = ["bloque"] + [f"dia_{i}" for i in range(1, 6)]
        self.tree = ttk.Treeview(panel_der, columns=columnas, show="headings", height=16)

        self.tree.heading("bloque", text="Bloque")
        self.tree.column("bloque", width=140, anchor="center")
        for i, d in enumerate(self.DIAS, 1):
            self.tree.heading(f"dia_{i}", text=d.upper())
            self.tree.column(f"dia_{i}", width=150, anchor="w")

        scroll_y = ttk.Scrollbar(panel_der, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self._actualizar_combo()

    def _actualizar_combo(self):
        modo = self.modo_vista.get()
        if modo == "nivel":
            self.combo_item["values"] = ["Nivel 1", "Nivel 2", "Nivel 3", "Nivel 4", "Nivel 5"]
            self.combo_item.current(0)
        elif modo == "docente":
            self.combo_item["values"] = self.docentes
            self.combo_item.current(0)
        elif modo == "sala":
            self.combo_item["values"] = self.salas
            self.combo_item.current(0)
        self.actualizar_grilla()

    def ejecutar_baseline(self):
        t0 = time.time()
        greedy = GreedyBaseline(self.sesiones, self.salas)
        res = greedy.ejecutar(self.evaluador)
        self.horario_actual = res["horario"]
        self._mostrar_metricas(res["tiempo_segundos"], "Baseline Voraz")

    def ejecutar_ag(self):
        t0 = time.time()
        ag = AlgoritmoGenetico(self.sesiones, self.salas, self.evaluador, tam_poblacion=80, seed=123)
        res = ag.evolucionar(num_generaciones=40, verbose=False)
        self.horario_actual = res["mejor_individuo"]
        self._mostrar_metricas(time.time() - t0, "Algoritmo Genético")

    def _mostrar_metricas(self, tiempo: float, metodo: str):
        p = self.horario_actual.penalizaciones
        self.lbl_tiempo.config(text=f"Tiempo: {tiempo:.3f} s ({metodo})")
        self.lbl_fitness.config(text=f"Fitness F(H): {self.horario_actual.fitness:.6f}")
        self.lbl_distancia.config(text=f"Distancia D(H): {self.horario_actual.distancia:.2f}")
        self.lbl_prof.config(text=f"• Choques Docente (P_prof): {p[0]}")
        self.lbl_asig.config(text=f"• Choques Nivel (P_asig): {p[1]}")
        self.lbl_vent.config(text=f"• Ventanas Libres (P_vent): {p[2]}")
        self.lbl_sal.config(text=f"• Choques Sala (P_sal): {p[3]}")

        duros = p[0] + p[1] + p[3]
        if self.horario_actual.distancia == 0:
            self.lbl_estado.config(text="Estado: Óptimo Global Factible (0 violaciones)", foreground="#2E7D32")
        elif duros == 0:
            self.lbl_estado.config(text=f"Estado: Factible ({p[2]} ventanas libres)", foreground="#1565C0")
        else:
            self.lbl_estado.config(text=f"Estado: Subóptimo ({duros} choques duros)", foreground="#C62828")

        self.actualizar_grilla()

    def actualizar_grilla(self):
        self.tree.delete(*self.tree.get_children())
        if not self.horario_actual:
            for b in self.BLOQUES:
                self.tree.insert("", tk.END, values=(b, "", "", "", "", ""))
            return

        modo = self.modo_vista.get()
        item = self.combo_item.get()

        if modo == "nivel":
            nivel = self.combo_item.current() + 1
            genes = self.horario_actual.obtener_por_nivel(nivel)
            self.lbl_titulo.config(text=f"Horario Semanal: Nivel {nivel}")
        elif modo == "docente":
            genes = self.horario_actual.obtener_por_profesor(item)
            self.lbl_titulo.config(text=f"Horario Semanal: Docente '{item}'")
        else:
            genes = self.horario_actual.obtener_por_sala(item)
            self.lbl_titulo.config(text=f"Horario Semanal: Sala '{item}'")

        # Mapear asignaciones a matriz [bloque 1..16][dia 1..5]
        tabla = {b: {d: [] for d in range(1, 6)} for b in range(1, 17)}
        for g in genes:
            for b in range(g.bloque, g.bloque + g.duracion):
                if 1 <= b <= 16 and 1 <= g.dia <= 5:
                    if modo == "nivel":
                        txt = f"{g.asignatura[:14]} ({g.sala})"
                    elif modo == "docente":
                        txt = f"{g.asignatura[:14]} ({g.sala})"
                    else:
                        txt = f"{g.asignatura[:12]} (N{g.nivel})"
                    tabla[b][g.dia].append(txt)

        for b_idx in range(1, 17):
            b_label = self.BLOQUES[b_idx - 1]
            fila = [b_label]
            for d in range(1, 6):
                asigs = tabla[b_idx][d]
                fila.append(" / ".join(asigs) if asigs else "")
            self.tree.insert("", tk.END, values=fila)


if __name__ == "__main__":
    app = EvoScheduleGUI()
    if "--screenshot" in sys.argv:
        app.ejecutar_baseline()
        app.update()
        print("GUI verificada exitosamente.")
        app.destroy()
    else:
        app.mainloop()

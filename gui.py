"""
gui.py - Interfaz Gráfica para EvoSchedule estilo Excel.
Muestra la malla horaria en formato idéntico a una planilla de cálculo:
- Filas: Bloques pedagógicos individuales de 45 minutos (Bloques 1 a 8).
- Columnas: Días de la semana (Lunes a Viernes).
- Celdas combinadas (Merge / setSpan): Clases de 2 bloques continuos (90 min)
  ocupan 2 casilleros verticales combinados, idéntico a las celdas fusionadas de Excel.
- Selector interactivo de nivel curricular / cohorte.
"""

import os
import sys
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QSpinBox,
    QDoubleSpinBox, QGroupBox, QHeaderView, QTextEdit, QComboBox, QCheckBox
)
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt

from src.data_loader import DataLoader
from src.fitness import FitnessEvaluator
from src.baseline import GreedyBaseline
from src.genetic import AlgoritmoGenetico


class EvoScheduleGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EvoSchedule - Planificador de Horarios Universitarios (Vista Excel)")
        self.resize(1250, 850)

        # Carga de datos base (45 asignaturas -> 90 sesiones de 2 bloques)
        self.loader = DataLoader()
        self.sesiones, self.salas = self.loader.extraer_datos()
        self.evaluador = FitnessEvaluator()
        self.horario_actual = None

        # 16 bloques pedagógicos de 45 minutos (jornada completa del Excel: mañana y tarde)
        self.bloques_info = [
            ("Bloque 1", "08:10 - 08:50"),
            ("Bloque 2", "08:50 - 09:30"),
            ("Bloque 3", "09:40 - 10:20"),
            ("Bloque 4", "10:20 - 11:00"),
            ("Bloque 5", "11:10 - 11:50"),
            ("Bloque 6", "11:50 - 12:30"),
            ("Bloque 7", "12:40 - 13:20"),
            ("Bloque 8", "13:20 - 14:00"),
            ("Bloque 9", "14:10 - 14:50"),
            ("Bloque 10", "14:50 - 15:30"),
            ("Bloque 11", "15:40 - 16:20"),
            ("Bloque 12", "16:20 - 17:00"),
            ("Bloque 13", "17:10 - 17:50"),
            ("Bloque 14", "17:50 - 18:30"),
            ("Bloque 15", "18:40 - 19:20"),
            ("Bloque 16", "19:20 - 20:00"),
        ]

        self._init_ui()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Panel Izquierdo: Controles y Parámetros
        panel_control = QVBoxLayout()
        group_params = QGroupBox("Panel de Control y Parámetros")
        layout_params = QVBoxLayout()

        lbl_info = QLabel(
            f"<b>Catálogo Académico:</b><br>"
            f"• Asignaturas: 45 (90 sesiones semanales)<br>"
            f"• Duración clase: 2 bloques de 45 min (90 min)<br>"
            f"• Salas disponibles: {len(self.salas)}<br>"
            f"• Jornada: 5 días x 16 bloques de 45 min (Mañana y Tarde)"
        )
        layout_params.addWidget(lbl_info)

        # Filtro de visualización tipo Excel
        layout_params.addWidget(QLabel("<b>Filtrar Cohorte / Nivel Curricular:</b>"))
        self.combo_filtro = QComboBox()
        self.combo_filtro.addItems([
            "Nivel I y II (Año 1)",
            "Nivel III y IV (Año 2)",
            "Nivel V y VI (Año 3)",
            "Nivel VII y VIII (Año 4)",
            "Nivel XI (Año 5)",
            "Ver Todo (Campus Global)"
        ])
        self.combo_filtro.currentIndexChanged.connect(self._actualizar_grilla)
        layout_params.addWidget(self.combo_filtro)

        # Parámetros AG
        layout_params.addWidget(QLabel("Tamaño Población (N):"))
        self.spin_pob = QSpinBox()
        self.spin_pob.setRange(20, 300)
        self.spin_pob.setValue(100)
        layout_params.addWidget(self.spin_pob)

        layout_params.addWidget(QLabel("Generaciones Máximas:"))
        self.spin_gen = QSpinBox()
        self.spin_gen.setRange(10, 500)
        self.spin_gen.setValue(60)
        layout_params.addWidget(self.spin_gen)

        layout_params.addWidget(QLabel("Individuos Elitistas (E):"))
        self.spin_elitismo = QSpinBox()
        self.spin_elitismo.setRange(1, 20)
        self.spin_elitismo.setValue(2)
        layout_params.addWidget(self.spin_elitismo)

        layout_params.addWidget(QLabel("Tamaño de Torneo (k):"))
        self.spin_torneo = QSpinBox()
        self.spin_torneo.setRange(2, 10)
        self.spin_torneo.setValue(3)
        layout_params.addWidget(self.spin_torneo)

        layout_params.addWidget(QLabel("Probabilidad de Cruce:"))
        self.spin_cruce = QDoubleSpinBox()
        self.spin_cruce.setRange(0.10, 1.00)
        self.spin_cruce.setSingleStep(0.05)
        self.spin_cruce.setValue(0.85)
        layout_params.addWidget(self.spin_cruce)

        layout_params.addWidget(QLabel("Probabilidad de Mutación:"))
        self.spin_mut = QDoubleSpinBox()
        self.spin_mut.setRange(0.01, 0.50)
        self.spin_mut.setSingleStep(0.01)
        self.spin_mut.setValue(0.05)
        layout_params.addWidget(self.spin_mut)

        layout_params.addWidget(QLabel("Semilla RNG (0 = Estocástico Libre):"))
        self.spin_seed = QSpinBox()
        self.spin_seed.setRange(0, 999999)
        self.spin_seed.setValue(0)
        layout_params.addWidget(self.spin_seed)

        # Botones
        self.btn_greedy = QPushButton("▶ Ejecutar Baseline Greedy")
        self.btn_greedy.clicked.connect(self.ejecutar_greedy)
        layout_params.addWidget(self.btn_greedy)

        self.btn_ga = QPushButton("⚡ Ejecutar Algoritmo Genético")
        self.btn_ga.clicked.connect(self.ejecutar_ga)
        layout_params.addWidget(self.btn_ga)

        # Métricas
        layout_params.addWidget(QLabel("Métricas de Rendimiento:"))
        self.txt_metricas = QTextEdit()
        self.txt_metricas.setReadOnly(True)
        layout_params.addWidget(self.txt_metricas)

        group_params.setLayout(layout_params)
        panel_control.addWidget(group_params)
        main_layout.addLayout(panel_control, 1)

        # Panel Derecho: Malla Horaria Semanal (Estilo Excel)
        panel_resultado = QVBoxLayout()
        lbl_grilla = QLabel("<b>Planilla de Horario Semanal (Filas = Bloques de 45 min | Columnas = Días):</b>")
        panel_resultado.addWidget(lbl_grilla)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "Bloque (45 min)", "LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES"
        ])

        # Estilo de encabezados tipo Excel
        self.tabla.setStyleSheet("""
            QTableWidget {
                gridline-color: #D0D0D0;
                background-color: #FFFFFF;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QHeaderView::section {
                background-color: #E6E8EA;
                color: #263238;
                font-weight: bold;
                border: 1px solid #B0BEC5;
                padding: 4px;
            }
        """)

        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        for c in range(1, 6):
            self.tabla.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.Stretch)

        # 8 filas, cada una representando 1 bloque de 45 minutos
        self.tabla.setRowCount(len(self.bloques_info))
        for r, (nombre_b, horario_b) in enumerate(self.bloques_info):
            texto_col0 = f" {nombre_b}\n {horario_b} "
            item = QTableWidgetItem(texto_col0)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setBackground(QColor("#F5F7FA"))
            item.setForeground(QColor("#37474F"))
            item.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            self.tabla.setItem(r, 0, item)
            self.tabla.setRowHeight(r, 42)

        panel_resultado.addWidget(self.tabla)
        main_layout.addLayout(panel_resultado, 3)

    def ejecutar_greedy(self):
        greedy = GreedyBaseline(self.sesiones, self.salas)
        res = greedy.ejecutar(self.evaluador)
        self.horario_actual = res["horario"]
        p = res["penalizaciones"]

        p_gr = res['penalizaciones']
        if res['distancia'] == 0:
            estado_gr = "ÓPTIMO GLOBAL FACTIBLE (0 violaciones)"
        elif p_gr['P_prof'] == 0 and p_gr['P_asig'] == 0 and p_gr['P_sal'] == 0:
            estado_gr = f"FACTIBLE SUBÓPTIMO (0 choques duros, {p_gr['P_vent']} ventanas)"
        else:
            estado_gr = f"APROXIMACIÓN CON CONFLICTOS ({p_gr['P_prof']+p_gr['P_asig']+p_gr['P_sal']} choques duros)"

        info = (
            f"=== BASELINE GREEDY ===\n"
            f"Tiempo: {res['tiempo_segundos']:.4f} s\n"
            f"Fitness F(H): {res['fitness']:.6f}\n"
            f"Distancia D(H): {res['distancia']:.2f}\n"
            f"Choques Docente: {p_gr['P_prof']}\n"
            f"Choques Asignatura: {p_gr['P_asig']}\n"
            f"Ventanas Libres: {p_gr['P_vent']}\n"
            f"Sobrecupo Salas: {p_gr['P_sal']}\n"
            f"Estado: {estado_gr}"
        )
        self.txt_metricas.setText(info)
        self._actualizar_grilla()

    def ejecutar_ga(self):
        seed_val = self.spin_seed.value()
        seed = seed_val if seed_val > 0 else None

        ga = AlgoritmoGenetico(
            asignaturas=self.sesiones,
            salas=self.salas,
            evaluador=self.evaluador,
            tam_poblacion=self.spin_pob.value(),
            tasa_cruce=self.spin_cruce.value(),
            tasa_mutacion=self.spin_mut.value(),
            elitismo=self.spin_elitismo.value(),
            k_torneo=self.spin_torneo.value(),
            total_bloques=16,
            dias=5,
            seed=seed
        )
        t_ini = time.time()
        res = ga.evolucionar(
            num_generaciones=self.spin_gen.value(),
            verbose=False
        )
        t_total = time.time() - t_ini

        self.horario_actual = res["mejor_individuo"]
        p = self.horario_actual.penalizaciones

        if self.horario_actual.distancia == 0:
            estado_ga = "ÓPTIMO GLOBAL FACTIBLE (0 violaciones)"
        elif p[0] == 0 and p[1] == 0 and p[3] == 0:
            estado_ga = f"FACTIBLE SUBÓPTIMO (0 choques duros, {p[2]} ventanas)"
        else:
            estado_ga = f"APROXIMACIÓN HEURÍSTICA ({p[0]+p[1]+p[3]} choques duros residuales)"

        info = (
            f"=== ALGORITMO GENÉTICO ===\n"
            f"Tiempo: {t_total:.4f} s\n"
            f"Generaciones: {res['generaciones']}\n"
            f"Fitness F(H): {self.horario_actual.fitness:.6f}\n"
            f"Distancia D(H): {self.horario_actual.distancia:.2f}\n"
            f"Choques Docente: {p[0]}\n"
            f"Choques Asignatura: {p[1]}\n"
            f"Ventanas Libres: {p[2]}\n"
            f"Sobrecupo Salas: {p[3]}\n"
            f"Estado: {estado_ga}"
        )
        self.txt_metricas.setText(info)
        self._actualizar_grilla()

    def _actualizar_grilla(self):
        # 1. Limpiar celdas combinadas y contenido previo
        self.tabla.clearSpans()
        for r in range(len(self.bloques_info)):
            for c in range(1, 6):
                self.tabla.setCellWidget(r, c, None)
                vacio = QTableWidgetItem("")
                vacio.setBackground(QColor("#FFFFFF"))
                self.tabla.setItem(r, c, vacio)

        if not self.horario_actual or not self.horario_actual.genes:
            return

        filtro_idx = self.combo_filtro.currentIndex() + 1
        ver_todo = (self.combo_filtro.currentText() == "Ver Todo (Campus Global)")

        # Paleta de colores suaves por nivel (estilo Excel)
        colores_nivel = {
            1: ("#E3F2FD", "#1565C0", "#90CAF9"),  # Fondo, Texto, Borde (Azul)
            2: ("#E8F5E9", "#2E7D32", "#A5D6A7"),  # Verde
            3: ("#FFF8E1", "#F57F17", "#FFE082"),  # Amarillo/Ámbar
            4: ("#F3E5F5", "#6A1B9A", "#CE93D8"),  # Púrpura
            5: ("#FBE9E7", "#D84315", "#FFAB91")   # Naranja/Terracota
        }

        # Agrupar asignaciones por (bloque_inicio, dia)
        slots = {}
        for g in self.horario_actual.genes:
            if not ver_todo and g.nivel != filtro_idx:
                continue

            dia_col = g.dia  # 1 a 5 -> columnas 1 a 5
            if not (1 <= dia_col <= 5):
                continue

            r_inicio = g.bloque - 1  # 0 a 7
            if not (0 <= r_inicio < len(self.bloques_info)):
                continue

            key = (r_inicio, dia_col)
            if key not in slots:
                slots[key] = []
            slots[key].append(g)

        # Renderizar asignaciones combinando celdas (setSpan) como en Excel
        for (r_inicio, c_dia), lista_genes in slots.items():
            duracion = lista_genes[0].duracion  # 2 bloques de 45 min

            # Combinar las 2 filas de 45 min si cabe en la grilla
            filas_a_combinar = min(duracion, len(self.bloques_info) - r_inicio)
            if filas_a_combinar > 1:
                self.tabla.setSpan(r_inicio, c_dia, filas_a_combinar, 1)

            # Preparar contenido de la tarjeta
            hay_choque = len(lista_genes) > 1
            textos = []
            for g in lista_genes:
                textos.append(
                    f"<div style='font-weight: bold; font-size: 11px;'>{g.asignatura}</div>"
                    f"<div style='font-size: 10px; color: #455A64;'>{g.profesor}</div>"
                    f"<div style='font-size: 10px; font-weight: bold; color: #1565C0;'>[Sala: {g.sala}]</div>"
                )

            contenido_html = "<hr style='border: none; border-top: 1px dashed #B0BEC5; margin: 3px 0;'>".join(textos)
            if hay_choque:
                contenido_html = "<div style='color: #C62828; font-weight: bold; font-size: 9px;'>⚠️ TOPE DE HORARIO</div>" + contenido_html

            lbl = QLabel(f"<div style='text-align: center; padding: 2px;'>{contenido_html}</div>")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setWordWrap(True)

            # Color según nivel o alerta si hay choque
            nivel_rep = lista_genes[0].nivel
            bg_color, txt_color, border_color = colores_nivel.get(nivel_rep, ("#FFFFFF", "#000000", "#B0BEC5"))
            if hay_choque:
                bg_color = "#FFEBEE"
                border_color = "#EF5350"

            lbl.setStyleSheet(f"""
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 3px;
                margin: 1px;
            """)
            self.tabla.setCellWidget(r_inicio, c_dia, lbl)


def generar_captura(salida_path="docs/gui_preview.png"):
    """Renderiza la interfaz offscreen y guarda una captura para el informe."""
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance() or QApplication([])
    gui = EvoScheduleGUI()
    gui.ejecutar_greedy()
    gui.show()
    os.makedirs(os.path.dirname(salida_path), exist_ok=True)
    gui.grab().save(salida_path)
    print(f"Captura de matriz horaria guardada exitosamente en {salida_path}")


if __name__ == "__main__":
    if "--screenshot" in sys.argv:
        generar_captura()
    else:
        app = QApplication(sys.argv)
        gui = EvoScheduleGUI()
        gui.show()
        sys.exit(app.exec())

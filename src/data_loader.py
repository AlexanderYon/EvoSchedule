"""
Módulo de carga de datos para EvoSchedule.
Extrae el catálogo oficial de asignaturas, docentes e infraestructura:
- 45 asignaturas extraídas del archivo HorarioICI_2026-2.xlsx.
- Cada asignatura se dicta 2 veces por semana.
- Cada sesión dura 2 bloques de 40 minutos (80 minutos pedagógicos continuos).
- Por consiguiente, el modelo gestiona 90 sesiones semanales (genes).
- 17 salas físicas disponibles en una jornada de 5 días x 16 bloques (80 bloques).
"""

import zipfile
import xml.etree.ElementTree as ET
import re
import random
from typing import List, Dict, Any, Tuple


class DataLoader:
    def __init__(self, excel_path: str = "dataset/HorarioICI_2026-2.xlsx"):
        self.excel_path = excel_path
        self.ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
        self.shared_strings: List[str] = []
        self.sheets: List[Tuple[str, str]] = []
        self.asignaturas: List[Dict[str, Any]] = []
        self.sesiones: List[Dict[str, Any]] = []
        self.salas: List[str] = []
        self.total_bloques: int = 16
        self.dias_semana: int = 5

    def _load_shared_strings(self, z: zipfile.ZipFile):
        """Carga las cadenas de texto del archivo OpenXML."""
        sst_xml = ET.fromstring(z.read("xl/sharedStrings.xml"))
        self.shared_strings = []
        for si in sst_xml.findall(f"{self.ns}si"):
            text = "".join(t.text for t in si.iter(f"{self.ns}t") if t.text is not None)
            self.shared_strings.append(text)

    def _get_cell_value(self, c_elem) -> str:
        t = c_elem.attrib.get("t")
        v = c_elem.find(f"{self.ns}v")
        val = v.text if v is not None else ""
        if t == "s" and val.isdigit():
            idx = int(val)
            if 0 <= idx < len(self.shared_strings):
                return self.shared_strings[idx].strip()
        return val.strip()

    def extraer_datos(self) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Extrae las asignaturas y genera las sesiones atómicas para la planificación:
        - 45 asignaturas base en el catálogo.
        - 2 sesiones semanales por asignatura, de 2 bloques cada una (duración = 2).
        - Total: 90 sesiones a planificar en el cromosoma.
        """
        with zipfile.ZipFile(self.excel_path) as z:
            self._load_shared_strings(z)
            wb_xml = ET.fromstring(z.read("xl/workbook.xml"))
            self.sheets = [
                (s.attrib["name"], f"sheet{idx}.xml")
                for idx, s in enumerate(wb_xml.iter(f"{self.ns}sheet"), 1)
            ]

            self.asignaturas = []
            for sheet_idx, (sheet_name, sheet_filename) in enumerate(self.sheets, 1):
                sheet_xml = ET.fromstring(z.read(f"xl/worksheets/{sheet_filename}"))
                rows = sheet_xml.findall(f"{self.ns}sheetData/{self.ns}row")

                header_row = -1
                asig_col, doc_col = None, None
                for r in rows:
                    r_idx = int(r.attrib["r"])
                    if r_idx < 30:
                        continue
                    for c in r.findall(f"{self.ns}c"):
                        col = "".join([ch for ch in c.attrib.get("r", "") if ch.isalpha()])
                        val = self._get_cell_value(c).lower()
                        if "asignatura" in val:
                            asig_col = col
                            header_row = r_idx
                        elif "docente" in val:
                            doc_col = col
                    if header_row != -1:
                        break

                if header_row == -1:
                    continue

                for r in rows:
                    r_idx = int(r.attrib["r"])
                    if r_idx <= header_row:
                        continue

                    asig_val, doc_val = "", ""
                    for c in r.findall(f"{self.ns}c"):
                        col = "".join([ch for ch in c.attrib.get("r", "") if ch.isalpha()])
                        val = self._get_cell_value(c)
                        if col == asig_col:
                            asig_val = val
                        elif col == doc_col:
                            doc_val = val

                    if asig_val:
                        docente_clean = doc_val if doc_val else "Docente Por Asignar"
                        self.asignaturas.append({
                            "id": f"ASIG_{len(self.asignaturas) + 1:02d}",
                            "nombre": asig_val,
                            "profesor": docente_clean,
                            "nivel": sheet_idx,
                            "nivel_nombre": sheet_name,
                            "duracion": 2
                        })

            # Extraer salas físicas
            rooms_set = set()
            for s in self.shared_strings:
                for token in s.split():
                    token = token.strip(",.;:()\"'")
                    if re.match(r"^(B[0-9]|A[0-9]|C[0-9]|D[0-9]|E[0-9]|F[0-9]|LC[0-9]|LAB-[A-Z0-9]+)$", token):
                        rooms_set.add(token)

            self.salas = sorted(list(rooms_set))
            if not self.salas:
                self.salas = ["A3", "A6", "B4", "B7", "B8", "C3", "D1", "D4", "E1", "E2", "E3", "LAB-C", "LAB-E", "LAB-F", "LAB-Q", "LC1"]

        # Construir las 90 sesiones semanales (2 por asignatura, cada una de 2 bloques)
        self.sesiones = []
        # Escenario sintético reproducible: no son disponibilidades ni matrículas reales.
        rng = random.Random(2026)
        docentes = sorted({a["profesor"] for a in self.asignaturas})
        perfil = {p: (rng.randint(1, 5), rng.choice([True, False])) for p in docentes}
        self.capacidades = {s: 65 for s in self.salas}
        for asig in self.asignaturas:
            estudiantes = rng.randint(30, 65)
            # Supuesto: una sesión práctica en cursos de programación o talleres.
            practica = any(x in asig["nombre"].lower() for x in ("programación", "taller", "base de datos", "estructura de datos"))
            for s_idx in (1, 2):
                self.sesiones.append({
                    "id": f"{asig['id']}_S{s_idx}",
                    "asig_id": asig["id"],
                    "nombre": asig["nombre"],
                    "sesion": s_idx,
                    "profesor": asig["profesor"],
                    "nivel": asig["nivel"],
                    "nivel_nombre": asig["nivel_nombre"],
                    "duracion": 2,
                    "estudiantes": estudiantes,
                    "requiere_lab": practica and s_idx == 2,
                    "dia_no_disponible": perfil[asig["profesor"]][0],
                    "prefiere_manana": perfil[asig["profesor"]][1]
                })

        return self.sesiones, self.salas

    def resumen_eda(self) -> Dict[str, Any]:
        """Resumen estadístico de las dimensiones del problema."""
        if not self.asignaturas or not self.salas:
            self.extraer_datos()

        profesores = set(a["profesor"] for a in self.asignaturas)
        por_nivel = {}
        for a in self.asignaturas:
            por_nivel[a["nivel_nombre"]] = por_nivel.get(a["nivel_nombre"], 0) + 1

        prof_carga = {}
        for a in self.asignaturas:
            prof_carga[a["profesor"]] = prof_carga.get(a["profesor"], 0) + 1

        return {
            "total_asignaturas": len(self.asignaturas),
            "total_sesiones": len(self.sesiones),
            "total_profesores": len(profesores),
            "total_salas": len(self.salas),
            "salas": self.salas,
            "distribucion_por_nivel": por_nivel,
            "top_profesores_carga": sorted(prof_carga.items(), key=lambda x: x[1], reverse=True)[:5],
            "dias_semana": self.dias_semana,
            "bloques_jornada": self.total_bloques
        }


if __name__ == "__main__":
    loader = DataLoader()
    sesiones, salas = loader.extraer_datos()
    eda = loader.resumen_eda()
    print("=== EXTRACCIÓN DE DATOS ===")
    print(f"Total Asignaturas del Catálogo: {eda['total_asignaturas']}")
    print(f"Total Sesiones Semanales (2 por asignatura, duracion=2): {eda['total_sesiones']}")
    print(f"Total Profesores: {eda['total_profesores']}")
    print(f"Total Salas Disponibles: {eda['total_salas']}")
    print("Salas:", eda["salas"])
    print("Distribución de Asignaturas por Nivel:")
    for niv, cant in eda["distribucion_por_nivel"].items():
        print(f"  • {niv}: {cant} asignaturas ({cant * 2} sesiones semanales)")

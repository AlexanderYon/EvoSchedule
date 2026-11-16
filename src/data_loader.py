"""
Módulo de carga y extracción de datos para EvoSchedule.
Extrae la información académica desde el archivo Excel institucional (HorarioICI_2026-2.xlsx)
utilizando la biblioteca estándar (zipfile y xml.etree.ElementTree) para garantizar
compatibilidad sin dependencias externas pesadas.
"""

import zipfile
import xml.etree.ElementTree as ET
import re
from typing import List, Dict, Any, Tuple


class DataLoader:
    def __init__(self, excel_path: str = "dataset/HorarioICI_2026-2.xlsx"):
        self.excel_path = excel_path
        self.ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
        self.shared_strings: List[str] = []
        self.sheets: List[Tuple[str, str]] = []  # (sheet_name, filename)
        self.courses_catalog: List[Dict[str, Any]] = []
        self.available_rooms: List[str] = []
        self.time_blocks: List[str] = [
            "08:10 - 09:30",  # Bloque 1
            "09:40 - 11:00",  # Bloque 2
            "11:10 - 12:30",  # Bloque 3
            "12:40 - 14:00",  # Bloque 4
            "14:10 - 15:30",  # Bloque 5
            "15:40 - 17:00",  # Bloque 6
            "17:10 - 18:30",  # Bloque 7
            "18:40 - 20:00",  # Bloque 8
        ]

    def _load_shared_strings(self, z: zipfile.ZipFile):
        """Carga de forma precisa las cadenas compartidas (<si>) del OpenXML."""
        sst_xml = ET.fromstring(z.read("xl/sharedStrings.xml"))
        self.shared_strings = []
        for si in sst_xml.findall(f"{self.ns}si"):
            text = "".join(t.text for t in si.iter(f"{self.ns}t") if t.text is not None)
            self.shared_strings.append(text)

    def _load_sheet_names(self, z: zipfile.ZipFile):
        """Obtiene los nombres de todas las hojas de cálculo del libro."""
        wb_xml = ET.fromstring(z.read("xl/workbook.xml"))
        self.sheets = [
            (s.attrib["name"], f"sheet{idx}.xml")
            for idx, s in enumerate(wb_xml.iter(f"{self.ns}sheet"), 1)
        ]

    def extract_catalog(self) -> List[Dict[str, Any]]:
        """
        Extrae el catálogo oficial de asignaturas, docentes y cupos desde
        las tablas ubicadas en cada una de las 5 hojas de nivel académico.
        """
        with zipfile.ZipFile(self.excel_path) as z:
            self._load_shared_strings(z)
            self._load_sheet_names(z)

            self.courses_catalog = []
            for sheet_idx, (sheet_name, sheet_filename) in enumerate(self.sheets, 1):
                sheet_xml = ET.fromstring(z.read(f"xl/worksheets/{sheet_filename}"))
                rows = sheet_xml.findall(f"{self.ns}sheetData/{self.ns}row")

                # Detectar encabezados de la tabla de asignaturas (filas >= 30)
                header_row = -1
                asig_col, doc_col, cup_col = None, None, None
                for r in rows:
                    r_idx = int(r.attrib["r"])
                    if r_idx < 30:
                        continue
                    for c in r.findall(f"{self.ns}c"):
                        col = "".join([ch for ch in c.attrib.get("r", "") if ch.isalpha()])
                        val = self._get_cell_value(c)
                        val_lower = val.lower()
                        if "asignatura" in val_lower:
                            asig_col = col
                            header_row = r_idx
                        elif "docente" in val_lower:
                            doc_col = col
                        elif "cupo" in val_lower:
                            cup_col = col
                    if header_row != -1:
                        break

                if header_row == -1:
                    continue

                for r in rows:
                    r_idx = int(r.attrib["r"])
                    if r_idx <= header_row:
                        continue

                    asig_val, doc_val, cup_val = "", "", ""
                    for c in r.findall(f"{self.ns}c"):
                        col = "".join([ch for ch in c.attrib.get("r", "") if ch.isalpha()])
                        val = self._get_cell_value(c)
                        if col == asig_col:
                            asig_val = val
                        elif col == doc_col:
                            doc_val = val
                        elif col == cup_col:
                            cup_val = val

                    if asig_val:
                        cupos_int = 30
                        try:
                            cupos_int = int(re.sub(r"[^\d]", "", cup_val)) if cup_val else 30
                        except ValueError:
                            cupos_int = 30

                        docente_clean = doc_val if doc_val else "Docente Por Asignar"

                        # Número de sesiones semanales requeridas
                        num_sesiones = 2
                        if "laboratorio" in asig_val.lower() or "taller" in asig_val.lower():
                            num_sesiones = 1

                        self.courses_catalog.append({
                            "id": f"ASIG_{len(self.courses_catalog) + 1:02d}",
                            "nombre": asig_val,
                            "nivel": sheet_idx,
                            "nivel_nombre": sheet_name,
                            "docente": docente_clean,
                            "cupos": cupos_int,
                            "sesiones_semana": num_sesiones,
                            "duracion_bloques": 1,
                            "tipo_sala": "LAB" if ("lab" in asig_val.lower() or "taller" in asig_val.lower() or "computación" in asig_val.lower()) else "AULA"
                        })

        return self.courses_catalog

    def extract_rooms(self) -> List[str]:
        """Obtiene la lista de salas y laboratorios disponibles en el campus."""
        if not self.shared_strings:
            with zipfile.ZipFile(self.excel_path) as z:
                self._load_shared_strings(z)

        rooms_set = set()
        for s in self.shared_strings:
            for token in s.split():
                token = token.strip(",.;:()\"'")
                if re.match(r"^(B[0-9]|A[0-9]|C[0-9]|D[0-9]|E[0-9]|F[0-9]|LC[0-9]|LAB-[A-Z0-9]+)$", token):
                    rooms_set.add(token)

        self.available_rooms = sorted(list(rooms_set))
        if not self.available_rooms:
            self.available_rooms = ["A3", "A6", "B4", "B7", "B8", "C3", "D1", "D4", "E1", "E2", "E3", "LAB-C", "LAB-E", "LAB-F", "LAB-Q", "LC1"]
        return self.available_rooms

    def _get_cell_value(self, c_elem) -> str:
        """Obtiene el texto de una celda teniendo en cuenta el pool de cadenas compartidas."""
        t = c_elem.attrib.get("t")
        v = c_elem.find(f"{self.ns}v")
        val = v.text if v is not None else ""
        if t == "s" and val.isdigit():
            idx = int(val)
            if 0 <= idx < len(self.shared_strings):
                return self.shared_strings[idx].strip()
        return val.strip()

    def generate_sessions_workload(self) -> List[Dict[str, Any]]:
        """
        Desglosa las asignaturas del catálogo en las sesiones atómicas que deben
        ser agendadas por el Algoritmo Genético. Cada sesión representa un gen a asignar.
        """
        if not self.courses_catalog:
            self.extract_catalog()

        workload = []
        for course in self.courses_catalog:
            for s_idx in range(1, course["sesiones_semana"] + 1):
                workload.append({
                    "sesion_id": f"{course['id']}_S{s_idx}",
                    "asignatura_id": course["id"],
                    "asignatura_nombre": course["nombre"],
                    "nivel": course["nivel"],
                    "docente": course["docente"],
                    "cupos": course["cupos"],
                    "duracion": course["duracion_bloques"],
                    "tipo_sala": course["tipo_sala"]
                })
        return workload

    def eda_summary(self) -> Dict[str, Any]:
        """Genera estadísticas exploratorias del conjunto de datos (EDA)."""
        if not self.courses_catalog:
            self.extract_catalog()
        if not self.available_rooms:
            self.extract_rooms()

        workload = self.generate_sessions_workload()
        docentes = set(c["docente"] for c in self.courses_catalog)
        docentes_carga = {}
        for w in workload:
            docentes_carga[w["docente"]] = docentes_carga.get(w["docente"], 0) + 1

        niveles_conteo = {}
        for c in self.courses_catalog:
            niveles_conteo[c["nivel_nombre"]] = niveles_conteo.get(c["nivel_nombre"], 0) + 1

        return {
            "total_asignaturas": len(self.courses_catalog),
            "total_sesiones_atómicas": len(workload),
            "total_docentes": len(docentes),
            "total_salas_disponibles": len(self.available_rooms),
            "distribucion_por_nivel": niveles_conteo,
            "top_docentes_carga": sorted(docentes_carga.items(), key=lambda x: x[1], reverse=True)[:5],
            "salas": self.available_rooms,
            "total_bloques_diarios": len(self.time_blocks),
            "dias_semana": 5
        }


if __name__ == "__main__":
    loader = DataLoader()
    catalog = loader.extract_catalog()
    rooms = loader.extract_rooms()
    eda = loader.eda_summary()
    print("=== RESUMEN EDA (EXPLORATORY DATA ANALYSIS) ===")
    print(f"Total asignaturas: {eda['total_asignaturas']}")
    print(f"Total sesiones atómicas a agendar: {eda['total_sesiones_atómicas']}")
    print(f"Total docentes identificados: {eda['total_docentes']}")
    print(f"Total salas disponibles: {eda['total_salas_disponibles']}")
    print("Salas disponibles:", eda["salas"])

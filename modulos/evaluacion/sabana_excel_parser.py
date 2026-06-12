import pandas as pd
import re

class SabanaExcelParser:
    """
    Motor especializado para analizar y extraer datos de la "Sábana de Notas" del MPPE
    (Resumen Final Rendimiento Estudiantil).
    Extrae TODAS las materias simultáneamente para una sección completa.
    """

    # Diccionario oficial de traducción: Acrónimos MPPE -> Códigos de Materia del Sistema
    MPPE_TO_SISTEMA = {
        "CA": "CAST",      # Castellano
        "ILE": "ING",      # Inglés
        "MA": "MAT",       # Matemática
        "EF": "EDF",       # Educación Física
        "AP": "ART",       # Arte y Patrimonio
        "CN": "NAT",       # Ciencias Naturales
        "GHC": "GHC",      # Geografía, Historia y Ciudadanía
        "OC": "ORC",       # Orientación y Convivencia
        "PGCRP": "PGCRP",  # Grupos de Creación, Recreación y Producción
        "FIS": "FIS",      # Física
        "QMC": "QMC",      # Química
        "BIO": "BIO",      # Biología
        "CT": "CIT",       # Ciencias de la Tierra
        "FSM": "FSM",      # Formación para la Soberanía Nacional
    }

    @classmethod
    def parse(cls, file_stream):
        """
        Lee el Excel tipo Sábana y extrae las notas de múltiples materias.
        Retorna:
            resultados = [
                {
                    "cedula": "12345678", 
                    "apellidos": "Perez", 
                    "nombres": "Juan", 
                    "notas": { "CAST": 15, "MAT": 12, ... }
                }, ...
            ]
            diagnostico = dict con detalles
        """
        try:
            # Leer todo el excel sin header, forzando todas las columnas a string para evitar errores de tipo
            df = pd.read_excel(file_stream, header=None, dtype=str)
        except Exception as e:
            return {"error": f"El archivo no es un Excel válido o está corrupto. ({str(e)})"}

        diagnostico = {
            "total_filas_raw": len(df),
            "materias_detectadas": [],
            "materias_ignoradas": [],
            "advertencias": []
        }

        # 1. Buscar la fila que contiene los acrónimos de las materias (CA, ILE, MA...)
        # Normalmente está entre la fila 10 y 20
        subject_row_idx = -1
        subject_columns = {} # { col_idx: "CAST" }

        for i in range(min(30, len(df))):
            row_vals = df.iloc[i].fillna("").astype(str).str.strip().str.upper()
            found_subjects = {}
            for col_idx, val in enumerate(row_vals):
                if val in cls.MPPE_TO_SISTEMA:
                    found_subjects[col_idx] = cls.MPPE_TO_SISTEMA[val]
            
            # Si encontramos al menos 3 materias conocidas, asumimos que es la fila correcta
            if len(found_subjects) >= 3:
                subject_row_idx = i
                subject_columns = found_subjects
                
                # Reportar si hay algún acrónimo extraño que parece materia pero no lo mapeamos
                # Las materias del MPPE suelen estar de la columna 45 en adelante
                for col_idx, val in enumerate(row_vals):
                    if col_idx > 40 and val.isalpha() and len(val) <= 5 and val not in cls.MPPE_TO_SISTEMA and val != "":
                        if val not in ["GRUPO", "SEXO", "DIA", "MES"]:
                            diagnostico["materias_ignoradas"].append(val)
                break

        if subject_row_idx == -1:
            return {
                "error": "No se detectó la estructura oficial del MPPE. "
                         "No se encontraron los acrónimos de materias (CA, ILE, MA) en las primeras 30 filas."
            }

        diagnostico["materias_detectadas"] = list(subject_columns.values())

        # 2. Extraer estudiantes (Empiezan inmediatamente después de la fila de materias)
        estudiantes = []
        filas_estudiantes = df.iloc[subject_row_idx + 1 :]

        for idx, row in filas_estudiantes.iterrows():
            row = row.fillna("").astype(str)
            
            # Ubicación estándar en MPPE:
            # Col 1: Cédula, Col 14: Apellidos, Col 23: Nombres
            cedula_raw = row.iloc[1].strip()
            apellidos = row.iloc[14].strip()
            nombres = row.iloc[23].strip()

            # Si no hay cédula, buscamos heurísticamente en las primeras 5 columnas
            if not cedula_raw or len(cedula_raw) < 5:
                for c in range(5):
                    if len(row.iloc[c].strip()) >= 5 and any(char.isdigit() for char in row.iloc[c].strip()):
                        cedula_raw = row.iloc[c].strip()
                        break

            # Limpiar cédula
            cedula = re.sub(r'[^0-9]', '', cedula_raw)

            # Si sigue sin cédula, ignoramos la fila (puede ser fila de firmas o totales)
            if not cedula or len(cedula) < 5:
                continue

            # Si no hay nombres en la pos 23, heurística: buscar en columnas 5 a 30
            if not nombres or not apellidos:
                posibles_nombres = []
                for c in range(5, 40):
                    val = row.iloc[c].strip()
                    if val and len(val) > 2 and not any(char.isdigit() for char in val):
                        if c not in [14, 23]: # Evitar las que ya leimos vacias
                            posibles_nombres.append(val)
                
                if posibles_nombres:
                    if not apellidos: apellidos = posibles_nombres[0]
                    if not nombres and len(posibles_nombres) > 1: nombres = posibles_nombres[1]

            nombre_completo = f"{apellidos} {nombres}".strip() or f"Estudiante CI {cedula}"

            # 3. Extraer las notas para este estudiante
            notas_estudiante = {}
            for col_idx, cod_materia in subject_columns.items():
                nota_str = row.iloc[col_idx].strip()
                # Extraer número (soporta 15, 15.5, 15,5)
                m_nota = re.search(r'([0-9]+[.,]?[0-9]*)', nota_str)
                if m_nota:
                    try:
                        nota_val = float(m_nota.group(1).replace(',', '.'))
                        if 0 <= nota_val <= 20:
                            notas_estudiante[cod_materia] = nota_val
                    except ValueError:
                        pass
            
            if notas_estudiante:
                estudiantes.append({
                    "cedula": cedula,
                    "apellidos": apellidos,
                    "nombres": nombres,
                    "nombre_completo": nombre_completo,
                    "notas": notas_estudiante,
                    "fila_excel": idx + 1
                })

        if not estudiantes:
            return {"error": "Se detectó la cabecera del MPPE, pero no se encontraron estudiantes válidos con notas."}

        return {
            "estudiantes": estudiantes,
            "diagnostico": diagnostico
        }

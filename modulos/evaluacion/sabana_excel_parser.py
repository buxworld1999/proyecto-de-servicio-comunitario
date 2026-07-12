import pandas as pd
import re

class SabanaExcelParser:
    """
    Motor especializado para analizar y extraer datos de la "Sábana de Notas" del MPPE
    (Resumen Final Rendimiento Estudiantil).
    Extrae TODAS las materias simultáneamente para una sección completa de forma segura.
    """

    # Diccionario oficial de traducción: Acrónimos MPPE -> PREFIJO real de materia en la BD.
    # OJO: estos son solo el prefijo. El código real en la tabla `materia` lleva además
    # el número de año pegado al final (ej: "CAST3", "MAT4", "ING1"), por eso el número
    # de grado se agrega después, dentro de parse(), usando el parámetro `codigo_grado`.
    MPPE_TO_SISTEMA = {
        "CA": "CAST",      # Castellano
        "ILE": "ING",      # Inglés
        "MA": "MAT",       # Matemática
        "EF": "EDFI",      # Educación Física
        "AP": "ARTE",      # Arte y Patrimonio
        "CN": "CNAT",      # Ciencias Naturales
        "GHC": "GHC",      # Geografía, Historia y Ciudadanía
        "OC": "OC",        # Orientación y Convivencia
        "PGCRP": "GCRP",   # Grupos de Creación, Recreación y Producción
        "FIS": "FIS",      # Física
        "QMC": "QUI",      # Química
        "BIO": "BIO",      # Biología
        "CT": "CT",        # Ciencias de la Tierra
        "FSM": "FSN",      # Formación para la Soberanía Nacional
    }

    @classmethod
    def parse(cls, file_stream, codigo_grado=None):
        """
        Lee el Excel tipo Sábana y extrae las notas de múltiples materias sin caerse por out-of-bounds.

        codigo_grado: número de año/grado de la sección que se está cargando (ej: "3" para 3er año).
        Es OBLIGATORIO para poder armar el código real de materia (ej: "CAST" + "3" = "CAST3"),
        ya que en la BD cada materia tiene un código distinto por cada grado.
        """
        if not codigo_grado:
            return {"error": "No se pudo determinar el grado/año de la sección seleccionada. "
                              "No es posible construir los códigos de materia sin esto."}
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
        subject_row_idx = -1
        subject_columns = {} # { col_idx: "CAST" }
        
        # Guardaremos también los índices de control de datos básicos si coinciden por texto explícito
        col_cedula_idx = -1
        col_apellidos_idx = -1
        col_nombres_idx = -1

        for i in range(min(30, len(df))):
            row_vals = df.iloc[i].fillna("").astype(str).str.strip().str.upper()
            found_subjects = {}
            
            # Buscar mapeos de columnas críticas por nombre directo en la fila de cabeceras
            for col_idx, val in enumerate(row_vals):
                if "CÉDULA" in val or "CEDULA" in val:
                    col_cedula_idx = col_idx
                elif "APELLIDO" in val:
                    col_apellidos_idx = col_idx
                elif "NOMBRE" in val:
                    col_nombres_idx = col_idx
                elif val in cls.MPPE_TO_SISTEMA:
                    # Código real = prefijo + número de grado (ej: "CAST" + "3" = "CAST3")
                    found_subjects[col_idx] = f"{cls.MPPE_TO_SISTEMA[val]}{codigo_grado}"
            
            # Si encontramos al menos 3 materias conocidas, asumimos que es la fila correcta
            if len(found_subjects) >= 3:
                subject_row_idx = i
                subject_columns = found_subjects
                
                # Reportar si hay algún acrónimo extraño
                for col_idx, val in enumerate(row_vals):
                    if col_idx > 5 and val.isalpha() and len(val) <= 5 and val not in cls.MPPE_TO_SISTEMA and val != "":
                        if val not in ["GRUPO", "SEXO", "DIA", "MES", "TOTAL"]:
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
            # Total de columnas de esta fila real para evitar desbordamiento
            max_cols = len(row)
            
            # Asignación inteligente de índices: Prioriza lo detectado, usa el estándar del MPPE si cabe, o el fallback del archivo corto
            idx_cedula = col_cedula_idx if col_cedula_idx != -1 else (1 if max_cols > 1 else 0)
            idx_apellidos = col_apellidos_idx if col_apellidos_idx != -1 else (14 if max_cols > 14 else (1 if max_cols > 1 else 0))
            idx_nombres = col_nombres_idx if col_nombres_idx != -1 else (23 if max_cols > 23 else (2 if max_cols > 2 else 0))

            # Extracción segura controlando que no acceda a índices inexistentes
            cedula_raw = row.iloc[idx_cedula].strip() if idx_cedula < max_cols else ""
            apellidos = row.iloc[idx_apellidos].strip() if idx_apellidos < max_cols else ""
            nombres = row.iloc[idx_nombres].strip() if idx_nombres < max_cols else ""

            # Búsqueda heurística de seguridad para la cédula si vino vacía
            if not cedula_raw or len(cedula_raw) < 5:
                for c in range(min(5, max_cols)):
                    val_c = str(row.iloc[c]).strip()
                    if len(val_c) >= 5 and any(char.isdigit() for char in val_c):
                        cedula_raw = val_c
                        break

            # Limpiar cédula dejando solo dígitos numéricos
            # IMPORTANTE: primero se descarta la parte decimal (ej: "31000389.0" -> "31000389")
            # antes de eliminar caracteres no numéricos. Si se hace al revés, el "0" que
            # queda después del punto se pega al final y corrompe la cédula
            # (ej: "31000389.0" -> "310003890", un número totalmente distinto).
            cedula_raw_str = str(cedula_raw).strip()
            if '.' in cedula_raw_str:
                cedula_raw_str = cedula_raw_str.split('.')[0]
            cedula = re.sub(r'[^0-9]', '', cedula_raw_str)

            # Si sigue sin tener una cédula válida, saltamos la línea de forma segura (totales, firmas, etc.)
            if not cedula or len(cedula) < 5:
                continue

            # Heurística para recuperar nombres/apellidos en formatos compactos
            if (not nombres or not apellidos) and max_cols > 2:
                posibles_nombres = []
                for c in range(min(40, max_cols)):
                    val = str(row.iloc[c]).strip()
                    if val and len(val) > 2 and not any(char.isdigit() for char in val):
                        if c not in [idx_apellidos, idx_nombres]:
                            posibles_nombres.append(val)
                
                if posibles_nombres:
                    if not apellidos: apellidos = posibles_nombres[0]
                    if not nombres and len(posibles_nombres) > 1: nombres = posibles_nombres[1]

            nombre_completo = f"{apellidos} {nombres}".strip() or f"Estudiante CI {cedula}"

            # 3. Extraer las notas para este estudiante de forma controlada
            notas_estudiante = {}
            for col_idx, cod_materia in subject_columns.items():
                if col_idx >= max_cols:
                    continue  # Evita el desbordamiento posicional si el Excel termina antes
                
                nota_str = str(row.iloc[col_idx]).strip()
                
                # Extraer número (soporta enteros y decimales 15, 15.5, 15,5)
                m_nota = re.search(r'([0-9]+[.,]?[0-9]*)', nota_str)
                if m_nota:
                    try:
                        nota_val = float(m_nota.group(1).replace(',', '.'))
                        if 0 <= nota_val <= 20:
                            # Guardamos la nota como entero si no tiene decimales significativos (.0)
                            notas_estudiante[cod_materia] = int(nota_val) if nota_val.is_integer() else nota_val
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
            return {"error": "Se detectó la cabecera de materias, pero no se encontraron registros de estudiantes con notas válidas."}

        return {
            "estudiantes": estudiantes,
            "diagnostico": diagnostico
        }
"""
notas_excel_parser.py — Motor de Parsing de Excel para Carga Masiva de Notas
PRISMA — Sistema de Gestión Escolar | Unidad Educativa Carmen Ruíz

Diseñado para planillas de notas venezolanas con estructura variable.
Soporte: celdas combinadas, encabezados multi-fila, alias locales (C.I., Ced, etc.)
"""

import re
import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


# ─── Alias de columnas ───────────────────────────────────────────────────────

COLUMN_ALIASES = {
    'num_lista': ['N°', 'NO.', 'NUM', 'LISTA', '#', 'NRO', 'ORD', 'N'],
    'cedula':    ['CEDULA', 'CÉDULA', 'C.I.', 'C. I.', 'CED', 'CI'],
    'apellidos': ['APELLIDOS', 'APELLIDO', 'APELL'],
    'nombres':   ['NOMBRES', 'NOMBRE', 'NOMB'],
    'nombre_completo': ['NOMBRE COMPLETO', 'ALUMNO', 'ESTUDIANTE', 'N C', 'NC'],
    'nota':      ['NOTA', 'CALIFICACION', 'CALIFICACIÓN', 'CALIF', 'CAL',
                  'PUNTAJE', 'PUNTUACION', 'PUNTUACIÓN'],
}

# Palabras que indican que una fila es un encabezado real
HEADER_KEYWORDS = [
    'CEDULA', 'CÉDULA', 'C.I', 'APELLIDOS', 'NOMBRES', 'NOTA',
    'CALIF', 'LISTA', 'N°', 'NOMBRE', 'ALUMNO', 'ESTUDIANTE',
]

# Palabras que indican basura (totales, firmas, etc.)
BASURA_KEYWORDS = [
    'PROMEDIO', 'TOTAL', 'FIRMA', 'DIRECTOR', 'SECRETARIA', 'SELLO',
    'OBSERVACIONES', 'APROBADO', 'REPROBADO', 'PROMOVIDO',
    'NOMBRE Y APELLIDO', 'APELLIDOS Y NOMBRES', 'CÉDULA IDENTIDAD',
    'EJEMPLO', 'MODELO',
]


# ─── Resultado del parser ────────────────────────────────────────────────────

class NotasParserResult:
    def __init__(self):
        self.registros = []          # Lista de dicts con datos de cada fila
        self.diagnostico = {
            'total_filas_raw': 0,
            'filas_omitidas': 0,
            'columnas_detectadas': [],
            'columnas_faltantes': [],
            'header_row_index': None,
            'advertencias': [],
        }


# ─── Motor principal ─────────────────────────────────────────────────────────

class NotasExcelParser:
    """
    Motor de Parsing Adaptativo para planillas de notas escolares venezolanas.
    Soporta estructura visual no normalizada y alias de columnas comunes.
    """

    def __init__(self, file_object):
        self.file_object = file_object
        self.result = NotasParserResult()
        self._df_raw = None
        self._col_map = {}
        self._header_row = None
        self._data_start_row = None

    def parse(self) -> NotasParserResult:
        try:
            self._fase0_cargar()
            self._fase1_detectar_encabezado()
            self._fase2_construir_mapa_columnas()
            self._fase3_extraer_registros()
        except Exception as e:
            logger.error(f"[NotasExcelParser] Error crítico: {e}", exc_info=True)
            self.result.diagnostico['advertencias'].append(
                f"Error crítico de motor: {str(e)}"
            )
        return self.result

    # ─── FASE 0: CARGA ───────────────────────────────────────────────────────
    def _fase0_cargar(self):
        self._df_raw = pd.read_excel(self.file_object, header=None, dtype=str)
        self._df_raw = self._df_raw.fillna('')
        self.result.diagnostico['total_filas_raw'] = len(self._df_raw)

    # ─── FASE 1: DETECCIÓN DEL ENCABEZADO ────────────────────────────────────
    def _fase1_detectar_encabezado(self):
        """Detecta la fila con mayor concentración de palabras clave de encabezado."""
        scan_limit = min(30, len(self._df_raw))
        best_row, best_score = 0, 0

        for i in range(scan_limit):
            row_vals = [str(v).upper().strip() for v in self._df_raw.iloc[i]]
            score = sum(
                1 for kw in HEADER_KEYWORDS
                if any(kw in cell for cell in row_vals)
            )
            if score > best_score:
                best_score = score
                best_row = i

        self._header_row = best_row
        self._data_start_row = best_row + 1
        self.result.diagnostico['header_row_index'] = best_row

        if best_score < 2:
            self.result.diagnostico['advertencias'].append(
                "Encabezado no claro. Parsing en modo fallback."
            )

    # ─── FASE 2: MAPA DE COLUMNAS ────────────────────────────────────────────
    def _fase2_construir_mapa_columnas(self):
        """Mapea alias de columnas a su índice en el DataFrame."""
        if self._header_row is None:
            return

        n_cols = len(self._df_raw.columns)
        scan_end = min(self._header_row + 3, self._data_start_row)

        # Texto combinado por columna (hasta 3 filas encabezadoras)
        header_texts = {}
        for col_idx in range(n_cols):
            parts = []
            for row_i in range(self._header_row, scan_end):
                cell = str(self._df_raw.iloc[row_i, col_idx]).upper().strip()
                if cell and cell not in ('NAN', ''):
                    parts.append(cell)
            header_texts[col_idx] = ' '.join(parts)

        def _match(alias, text):
            return bool(re.search(
                r'(?<![A-ZÁÉÍÓÚÑ])' + re.escape(alias) + r'(?![A-ZÁÉÍÓÚÑ])', text
            ))

        for field, aliases in COLUMN_ALIASES.items():
            for col_idx, text in header_texts.items():
                for alias in aliases:
                    if _match(alias, text) and field not in self._col_map:
                        self._col_map[field] = col_idx
                        break

        detected = set(self._col_map.keys())
        self.result.diagnostico['columnas_detectadas'] = sorted(detected)
        self.result.diagnostico['columnas_faltantes'] = [
            f for f in COLUMN_ALIASES if f not in detected
        ]

    # ─── FASE 3: EXTRACCIÓN DE REGISTROS ─────────────────────────────────────
    def _fase3_extraer_registros(self):
        if self._data_start_row is None:
            return

        omitidos = 0
        for row_idx in range(self._data_start_row, len(self._df_raw)):
            row = self._df_raw.iloc[row_idx]
            registro = self._procesar_fila(row, row_idx)
            if registro is None:
                omitidos += 1
            else:
                self.result.registros.append(registro)

        self.result.diagnostico['filas_omitidas'] = omitidos

    def _procesar_fila(self, row, row_idx) -> Optional[dict]:
        def get(field):
            col = self._col_map.get(field)
            if col is None or col >= len(row):
                return ''
            val = str(row.iloc[col]).strip()
            return '' if val.upper() in ('NAN', 'NONE', '') else val

        # Filtro: fila casi vacía
        non_empty = [str(v).strip() for v in row if str(v).strip() not in ('', 'nan', 'NaN')]
        if len(non_empty) < 2:
            return None

        # Filtro: fila de totales/firmas/etc.
        combined = ' '.join(str(v).upper() for v in row)
        if any(kw in combined for kw in BASURA_KEYWORDS):
            return None

        cedula_raw   = get('cedula')
        apellidos    = get('apellidos')
        nombres      = get('nombres')
        nombre_comp  = get('nombre_completo')
        nota_raw     = get('nota')
        num_lista    = get('num_lista')

        # Normalizar cédula
        cedula = self._normalizar_cedula(cedula_raw)

        # Separar nombre completo si faltan apellidos/nombres
        if nombre_comp and not apellidos and not nombres:
            apellidos, nombres = self._split_nombre_completo(nombre_comp)
        elif apellidos and nombres and not nombre_comp:
            nombre_comp = f"{apellidos} {nombres}"

        # Filtro: sin ningún dato personal mínimo
        if not cedula and not (apellidos or nombres or nombre_comp):
            return None

        # Validar y normalizar nota
        nota_val, nota_error = self._normalizar_nota(nota_raw)

        adv = []
        if not cedula:     adv.append('Sin cédula')
        if not apellidos:  adv.append('Sin apellidos')
        if not nombres:    adv.append('Sin nombres')
        if nota_error:     adv.append(nota_error)

        return {
            'num_lista':       num_lista,
            'cedula':          cedula,
            'apellidos':       apellidos.upper() if apellidos else '',
            'nombres':         nombres.upper() if nombres else '',
            'nombre_completo': nombre_comp.upper() if nombre_comp else '',
            'nota':            nota_val,
            'advertencias':    adv,
            'fila_excel':      row_idx + 1,
        }

    # ─── HELPERS ─────────────────────────────────────────────────────────────

    def _normalizar_cedula(self, raw: str) -> str:
        if not raw:
            return ''
        upper = raw.upper().strip()
        if any(x in upper for x in ('S/C', 'SC', 'S.C', 'SIN')):
            return ''
        digits = re.sub(r'\D', '', raw)
        return digits if len(digits) >= 6 else ''

    def _normalizar_nota(self, raw: str):
        """Retorna (float|None, error_msg|None)."""
        if not raw:
            return None, 'Sin nota'
        try:
            n = float(raw.replace(',', '.'))
            if 0 <= n <= 20:
                return round(n, 2), None
            else:
                return None, f'Nota fuera de rango (0-20): {raw}'
        except (ValueError, TypeError):
            return None, f'Nota inválida: {raw}'

    def _limpiar_texto(self, texto: str) -> str:
        if not texto:
            return ''
        return re.sub(r'[^\w\s\-\'.]', '', texto, flags=re.UNICODE).strip()

    def _split_nombre_completo(self, nc: str) -> tuple:
        """Convención venezolana: primeras 2 palabras = apellidos, resto = nombres."""
        parts = nc.strip().split()
        if len(parts) >= 4:
            return ' '.join(parts[:2]), ' '.join(parts[2:])
        elif len(parts) == 3:
            return parts[0], ' '.join(parts[1:])
        elif len(parts) == 2:
            return parts[0], parts[1]
        return nc, ''

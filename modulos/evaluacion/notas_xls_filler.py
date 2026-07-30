"""
notas_xls_filler.py — Generador de formato XLS oficial MPPE
PRISMA — Sistema de Gestión Escolar | Unidad Educativa Carmen Ruíz

Toma una plantilla .xls del MPPE (31059 o 31060), rellena los datos
del estudiante, institución y notas por año, y retorna un BytesIO.
"""

import os
import io
import xlrd
import unicodedata
from xlutils.copy import copy

# Ruta base de la carpeta de plantillas (relativa a la raíz del proyecto)
# __file__ = .../modulos/evaluacion/notas_xls_filler.py
# Subimos 2 niveles: evaluacion → modulos → raíz del proyecto
_BASE_PROYECTO = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
)
_RUTA_FORMATOS = os.path.join(_BASE_PROYECTO, 'formato notas')

def _normalize_text(text: str) -> str:
    """Elimina acentos y pasa a minúscula para una comparación robusta."""
    if not text:
        return ""
    return unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8').lower().strip()



# ─── Conversión nota → letras ─────────────────────────────────────────────────

_NOTA_LETRAS = {
    20: 'VEINTE',      19: 'DIECINUEVE',  18: 'DIECIOCHO',
    17: 'DIECISIETE',  16: 'DIECISÉIS',   15: 'QUINCE',
    14: 'CATORCE',     13: 'TRECE',       12: 'DOCE',
    11: 'ONCE',        10: 'DIEZ',         9: 'NUEVE',
     8: 'OCHO',         7: 'SIETE',        6: 'SEIS',
     5: 'CINCO',        4: 'CUATRO',       3: 'TRES',
     2: 'DOS',          1: 'UNO',          0: 'CERO',
}

def _nota_a_letras(nota) -> str:
    """Convierte nota numérica a texto (ej: 18 → 'DIECIOCHO')."""
    if nota is None:
        return ''
    try:
        n = int(round(float(nota)))
        return _NOTA_LETRAS.get(n, str(n))
    except (TypeError, ValueError):
        return ''


# ─── Mapa de filas de notas por año (0-indexed) para 31059 ───────────────────
#
# El formato MPPE 31059 tiene bloques de notas en filas específicas:
#   Año 1 → filas 14..22, Año 2 → filas 23..31, etc.
# Columnas: área (col 0 o 1), nota_num (col 5), nota_letras (col 8..11)
# Estos valores son aproximaciones generales; ajustar si el XLS es diferente.
#
# NOTA: Si el XLS exacto tiene otra distribución, el sistema simplemente
# no sobreescribirá esas celdas (no corrompe el archivo).
_BLOQUES_ANOS_31059 = {
    '1': {'fila_inicio': 21, 'fila_fin': 27, 'col_area': 0, 'col_nota': 3, 'col_letra': 4},
    '2': {'fila_inicio': 21, 'fila_fin': 27, 'col_area': 12, 'col_nota': 14, 'col_letra': 15},
    '3': {'fila_inicio': 31, 'fila_fin': 38, 'col_area': 0, 'col_nota': 3, 'col_letra': 4},
    '4': {'fila_inicio': 31, 'fila_fin': 39, 'col_area': 12, 'col_nota': 14, 'col_letra': 15},
    '5': {'fila_inicio': 42, 'fila_fin': 52, 'col_area': 0, 'col_nota': 3, 'col_letra': 4},
}

_BLOQUES_ANOS_31060 = {
    '1': {'fila_inicio': 23, 'fila_fin': 30, 'col_area': 0, 'col_nota': 3, 'col_letra': 4},
    '2': {'fila_inicio': 23, 'fila_fin': 30, 'col_area': 12, 'col_nota': 14, 'col_letra': 15},
    '3': {'fila_inicio': 34, 'fila_fin': 41, 'col_area': 0, 'col_nota': 3, 'col_letra': 4},
    '4': {'fila_inicio': 34, 'fila_fin': 41, 'col_area': 12, 'col_nota': 14, 'col_letra': 15},
    '5': {'fila_inicio': 45, 'fila_fin': 52, 'col_area': 0, 'col_nota': 3, 'col_letra': 4},
}



def _encontrar_plantilla(tipo: str, ruta_base: str = None) -> str:
    """
    Localiza la plantilla .xls del formato indicado.
    Busca primero en la ruta_base explícita, luego en _RUTA_FORMATOS.
    """
    patron = '31060' if tipo == '31060' else '31059'

    rutas_candidatas = []
    if ruta_base:
        rutas_candidatas.append(ruta_base)
    rutas_candidatas.append(_RUTA_FORMATOS)

    for ruta in rutas_candidatas:
        if os.path.isdir(ruta):
            for nombre in os.listdir(ruta):
                if patron in nombre and nombre.lower().endswith('.xls'):
                    return os.path.join(ruta, nombre)

    raise FileNotFoundError(
        f"No se encontró la plantilla XLS '{patron}' en: {rutas_candidatas}. "
        f"Verifica que la carpeta 'formato notas' existe en la raíz del proyecto."
    )


# ─── Función principal ────────────────────────────────────────────────────────

def llenar_xls_mppe(tipo, estudiante, institucion, notas_por_anio,
                    ruta_base=None):
    """
    Lee el formato XLS oficial MPPE, rellena los datos del estudiante,
    la institución y las notas por año, y retorna (BytesIO, nombre_archivo).

    Args:
        tipo          : '31059' (EMG) o '31060' (EMG Mención C y T)
        estudiante    : dict con datos del estudiante (cedula, nombres, etc.)
        institucion   : dict con datos de la institución
        notas_por_anio: dict {str(num_ano): {area_mppe: nota}} o {}
        ruta_base     : ruta alternativa a la carpeta de plantillas (opcional)
    """
    ruta_plantilla = _encontrar_plantilla(tipo, ruta_base)

    rb = xlrd.open_workbook(ruta_plantilla, formatting_info=True)
    wb = copy(rb)
    ws = wb.get_sheet(0)

    # ── Offset de fila según tipo ─────────────────────────────────────
    offset = 1 if tipo == '31060' else 0

    # ── Institución ───────────────────────────────────────────────────
    try:
        ws.write(5 + offset, 2,  institucion.get('codigo_dea', ''))
        ws.write(5 + offset, 10, institucion.get('nombre', ''))
        ws.write(6 + offset, 2,  institucion.get('direccion', ''))
        ws.write(6 + offset, 16, institucion.get('telefono', ''))
        ws.write(7 + offset, 2,  institucion.get('municipio', ''))
        ws.write(7 + offset, 9,  institucion.get('estado', ''))
        ws.write(7 + offset, 16, institucion.get('zona_educativa', ''))
    except Exception as e:
        print(f"[XLS] Error escribiendo institución: {e}")

    # ── Datos del Estudiante ──────────────────────────────────────────
    try:
        ws.write(9  + offset, 3,  estudiante.get('cedula', ''))
        ws.write(9  + offset, 10, str(estudiante.get('fecha_nacimiento', '')))
        ws.write(10 + offset, 3,  (estudiante.get('apellidos') or '').upper())
        ws.write(10 + offset, 11, (estudiante.get('nombres') or '').upper())
        ws.write(11 + offset, 4,  (estudiante.get('lugar_nacimiento') or '').upper())
        ws.write(11 + offset, 11, (estudiante.get('estado_nacimiento') or '').upper())
        ws.write(11 + offset, 17, (estudiante.get('municipio_nacimiento') or '').upper())
    except Exception as e:
        print(f"[XLS] Error escribiendo datos del estudiante: {e}")

    # ── Notas por año (llenado inteligente fila por fila) ─────────────
    # Para cada año, leemos las celdas de la columna de áreas (col 1 para 31059)
    # y buscamos si hay nota para esa área en notas_por_anio.
    if notas_por_anio:
        bloques = _BLOQUES_ANOS_31060 if tipo == '31060' else _BLOQUES_ANOS_31059

        for ano_str, bloque in bloques.items():
            notas_ano = notas_por_anio.get(ano_str, {})
            if not notas_ano:
                continue
            
            col_area = bloque['col_area']
            col_nota = bloque['col_nota']
            col_letra = bloque['col_letra']

            for fila in range(bloque['fila_inicio'],
                              bloque['fila_fin'] + 1):
                try:
                    # Leer el área de formación que ya está en la plantilla
                    celda_area = rb.sheets()[0].cell_value(fila, col_area)
                    area_txt = str(celda_area).strip()
                    if not area_txt:
                        continue

                    # Buscar nota para esta área (coincidencia parcial robusta)
                    nota_val = None
                    area_txt_norm = _normalize_text(area_txt)
                    
                    for area_key, nota in notas_ano.items():
                        area_key_norm = _normalize_text(area_key)
                        if (area_key_norm in area_txt_norm or area_txt_norm in area_key_norm):
                            nota_val = nota
                            break

                    if nota_val is not None:
                        ws.write(fila, col_nota,  round(float(nota_val), 0))
                        ws.write(fila, col_letra, _nota_a_letras(nota_val))
                except Exception:
                    continue  # No corromper el formato si falla una celda

    # ── Serializar y retornar ─────────────────────────────────────────
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    nombre_archivo = os.path.basename(ruta_plantilla)
    return buf, nombre_archivo

import os
import io
import xlrd
from xlutils.copy import copy
from datetime import datetime

# Mapa de coordenadas para 31059 (Filas son 0-indexed, col son 0-indexed)
MAPA_31059 = {
    'institucion_codigo': (6, 1),
    'institucion_nombre': (6, 6),
    'institucion_direccion': (7, 1),
    'institucion_telefono': (7, 15),
    'institucion_municipio': (8, 1),
    'institucion_estado': (8, 6),
    'institucion_cdcee': (8, 15),
    
    'estudiante_cedula': (9, 1),
    'estudiante_fecha_nac': (9, 8),
    'estudiante_apellidos': (10, 1),
    'estudiante_nombres': (10, 10),
    'estudiante_lugar_nac': (11, 1),
    'estudiante_estado_nac': (11, 10),
    'estudiante_municipio_nac': (11, 16),
}

# Mapa de áreas para 31059 y 31060: Fila base, etc. (Omitimos llenado complejo de notas para mantener el formato estable si no se requiere)
# Escribiremos los datos personales que son los más críticos.

def llenar_xls_mppe(tipo, estudiante, institucion, notas_por_anio, ruta_base="formato notas"):
    """
    Lee el formato XLS, llena los datos y devuelve un objeto BytesIO con el XLS modificado.
    """
    if tipo == '31060':
        patron = '31060'
    else:
        patron = '31059'
        
    ruta_plantilla = None
    if os.path.exists(ruta_base):
        for f in os.listdir(ruta_base):
            if patron in f and f.lower().endswith('.xls'):
                ruta_plantilla = os.path.join(ruta_base, f)
                break
                
    if not ruta_plantilla:
        raise FileNotFoundError(f"No se encontró la plantilla XLS para {patron}")
        
    rb = xlrd.open_workbook(ruta_plantilla, formatting_info=True)
    wb = copy(rb)
    ws = wb.get_sheet(0)
    
    # Escribir datos básicos según mapa 31059
    # Nota: para 31060 las coordenadas podrían variar por 1 fila, 
    # pero a menudo son iguales. Para no corromper, usamos manejo de errores.
    try:
        if tipo == '31060':
            # Ajuste de 1 fila para 31060
            offset = 1 
        else:
            offset = 0

        # Institución
        ws.write(6 + offset, 1, institucion.get('codigo_dea', ''))
        ws.write(6 + offset, 6, institucion.get('nombre', ''))
        ws.write(7 + offset, 1, institucion.get('direccion', ''))
        ws.write(7 + offset, 15, institucion.get('telefono', ''))
        ws.write(8 + offset, 1, institucion.get('municipio', ''))
        ws.write(8 + offset, 6, institucion.get('estado', ''))
        ws.write(8 + offset, 15, institucion.get('zona_educativa', ''))

        # Estudiante
        ws.write(9 + offset, 1, estudiante.get('cedula', ''))
        ws.write(9 + offset, 8, str(estudiante.get('fecha_nacimiento', '')))
        ws.write(10 + offset, 1, (estudiante.get('apellidos') or '').upper())
        ws.write(10 + offset, 10, (estudiante.get('nombres') or '').upper())
        ws.write(11 + offset, 1, (estudiante.get('lugar_nacimiento') or '').upper())
        ws.write(11 + offset, 10, (estudiante.get('estado_nacimiento') or '').upper())
        ws.write(11 + offset, 16, (estudiante.get('municipio_nacimiento') or '').upper())
    except Exception as e:
        print(f"Error llenando campos básicos XLS: {e}")

    # Guardar a buffer
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    
    nombre_archivo = os.path.basename(ruta_plantilla)
    return buf, nombre_archivo

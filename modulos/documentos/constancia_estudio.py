import os
import io
from datetime import datetime
from flask import render_template, request, send_from_directory, send_file
from docxtpl import DocxTemplate

from db import supabase

MESES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
         "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


def _enriquecer_alumno(alumno):
    """Agrega campos formateados al dict del alumno."""
    # Cédula con puntos
    ced_str = str(alumno.get('cedula', ''))
    alumno['cedula_formateada'] = (
        '{:,}'.format(int(ced_str)).replace(',', '.')
        if ced_str.isdigit() else ced_str
    )

    # Desglosar fecha de nacimiento
    fecha_nac = alumno.get('fecha_nacimiento')
    if fecha_nac and isinstance(fecha_nac, str) and len(fecha_nac) >= 10:
        partes = fecha_nac.split('-')
        if len(partes) == 3:
            alumno['anio_nac'] = int(partes[0])
            mes_num = int(partes[1])
            alumno['dia_nac'] = int(partes[2])
            if 1 <= mes_num <= 12:
                alumno['mes_nac'] = MESES[mes_num]

    # Valores por defecto
    alumno['lugar_nacimiento'] = alumno.get('lugar_nacimiento') or 'SAN FERNANDO'
    alumno['estado_nacimiento'] = alumno.get('estado_nacimiento') or 'APURE'
    return alumno


def constancia_estudio():
    alumno = None
    error_busqueda = None

    # Formatos manuales (se descargan en blanco, para llenar a mano)
    MANUALES = {
        'ACTA DE EVALUACIÓN FINAL para llenar.docx',
        'Inscripcion Inicial para llenar.docx',
    }

    ruta_formatos = 'formato constancias'
    formatos_auto    = []
    formatos_manuales = []
    if os.path.exists(ruta_formatos):
        todos = sorted(
            f for f in os.listdir(ruta_formatos)
            if f.lower().endswith(('.docx', '.doc'))
        )
        for f in todos:
            if f in MANUALES:
                formatos_manuales.append(f)
            else:
                formatos_auto.append(f)

    if request.method == 'POST':
        cedula_buscar = request.form.get('cedula_estudiante', '').strip()
        if cedula_buscar:
            try:
                resp = supabase.table("estudiante").select("*").eq("cedula", cedula_buscar).execute()
                if resp.data:
                    alumno = _enriquecer_alumno(resp.data[0])
                else:
                    error_busqueda = "Estudiante no registrado."
            except Exception as e:
                error_busqueda = f"Error al consultar: {str(e)}"

    return render_template(
        'documentos/constancia_estudio.html',
        alumno=alumno,
        error_busqueda=error_busqueda,
        formatos=formatos_auto,
        formatos_manuales=formatos_manuales
    )


def descargar_formato(nombre_archivo):
    ruta_formatos = 'formato constancias'
    cedula = request.args.get('cedula', '').strip()

    if cedula and nombre_archivo.lower().endswith('.docx'):
        try:
            resp = supabase.table("estudiante").select("*").eq("cedula", cedula).execute()
            if resp.data:
                alumno = _enriquecer_alumno(resp.data[0])

                # Construir contexto para docxtpl
                context = dict(alumno)
                context['fecha_actual']     = datetime.now().strftime('%d/%m/%Y')
                context['dia_actual']       = datetime.now().day
                context['mes_actual']       = MESES[datetime.now().month]
                context['anio_actual']      = datetime.now().year
                context['autoridad_nombre'] = request.args.get('autoridad', 'Gabriel Inojosa')
                context['autoridad_cedula'] = request.args.get('autoridad_cedula', '11.843.656')
                context['autoridad_cargo']  = request.args.get('autoridad_cargo', 'Director')
                context['anio_escolar']     = request.args.get('anio_escolar', '2025-2026')

                doc_path = os.path.join(ruta_formatos, nombre_archivo)
                if os.path.exists(doc_path):
                    doc = DocxTemplate(doc_path)
                    doc.render(context)

                    buf = io.BytesIO()
                    doc.save(buf)
                    buf.seek(0)

                    nombre_descarga = f"{nombre_archivo.replace('.docx', '')}_{cedula}.docx"
                    return send_file(
                        buf,
                        as_attachment=True,
                        download_name=nombre_descarga,
                        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    )
        except Exception as e:
            print(f"[descargar_formato] Error al llenar '{nombre_archivo}': {e}")

    # Fallback: descarga el archivo tal cual
    return send_from_directory(ruta_formatos, nombre_archivo, as_attachment=True)
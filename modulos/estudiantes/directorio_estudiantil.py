from flask import render_template, request, redirect, url_for, flash
from db import supabase

def directorio_estudiantil_view():
    """
    Ruta para listar todos los estudiantes.
    """
    try:
        response = supabase.table("estudiante").select("*").execute()
        estudiantes = response.data

        # Find active year
        ano_resp = supabase.table("ano_escolar").select("codigo").eq("activo", True).limit(1).execute()
        ano_activo = ano_resp.data[0]['codigo'] if ano_resp.data else None

        matriculados_cedulas = set()
        if ano_activo:
            mat_resp = supabase.table("matricula").select("cedula_estudiante").eq("codigo_ano_escolar", ano_activo).eq("estado_matricula", "A").execute()
            if mat_resp.data:
                matriculados_cedulas = {m['cedula_estudiante'] for m in mat_resp.data}

        for est in estudiantes:
            est['is_matriculado'] = est['cedula'] in matriculados_cedulas

    except Exception as e:
        estudiantes = []
        flash(f"Error al obtener estudiantes: {str(e)}", "danger")

    return render_template('estudiantes/directorio.html', estudiantes=estudiantes)



from flask import render_template, request, redirect, url_for, flash
from db import supabase

def representantes_view():
    """
    Ruta de Representantes: Captura formulario y registra en 
    'representante' y 'estudiante_representante' usando Supabase.
    """
    if request.method == 'POST':
        # 1. Preparar datos del representante
        datos_representante = {
            "cedula": request.form.get('cedula'),
            "nacionalidad": request.form.get('nacionalidad'),
            "nombres": request.form.get('nombres'),
            "apellidos": request.form.get('apellidos'),
            "parentesco": request.form.get('parentesco'),
            "ocupacion": request.form.get('ocupacion'),
            "direccion": request.form.get('direccion'),
            "telefono": request.form.get('telefono'),
            "correo": request.form.get('correo'),
            "fecha_nacimiento": request.form.get('fecha_nacimiento') or None,
            "genero": request.form.get('genero', 'M'),
            "es_madre": 'es_madre' in request.form,
            "es_padre": 'es_padre' in request.form,
            "es_representante_legal": 'es_representante_legal' in request.form
        }

        try:
            # 2. Insertar Representante
            supabase.table("representante").insert(datos_representante).execute()

            # 3. Insertar Relaciones (Estudiantes)
            lista_estudiantes = request.form.getlist('estudiantes[]')
            for cedula_est in lista_estudiantes:
                if cedula_est:
                    relacion = {
                        "cedula_estudiante": cedula_est,
                        "cedula_representante": datos_representante["cedula"],
                        "parentesco": datos_representante["parentesco"],
                        "es_representante_legal": datos_representante["es_representante_legal"]
                    }
                    supabase.table("estudiante_representante").insert(relacion).execute()
            
            flash(f"Representante {datos_representante['nombres']} registrado exitosamente.")
        except Exception as e:
            flash(f"Error al registrar: {str(e)}")

        return redirect(url_for('representantes'))

    # Lógica GET para búsqueda (API interna)
    # Se recomienda tener un endpoint separado para la consulta AJAX
    return render_template('estudiantes/representantes.html')

def buscar_representante_api(cedula):
    """Endpoint para buscar por cédula"""
    try:
        # Consulta join simulada: Obtener representante y sus estudiantes
        rep = supabase.table("representante").select("*").eq("cedula", cedula).single().execute()
        est = supabase.table("estudiante_representante").select("cedula_estudiante").eq("cedula_representante", cedula).execute()
        return {"representante": rep.data, "estudiantes": est.data}
    except Exception as e:
        return {"error": str(e)}, 404
from flask import render_template, request, redirect, url_for, flash

# Importar supabase desde db.py — sin importaciones circulares
from db import supabase


def personal():
    """
    Ruta de Personal: Captura el formulario y registra un trabajador
    en la tabla 'trabajador' de Supabase controlando la longitud de los tipos char(1).
    """
    if request.method == 'POST':
        v_genero = request.form.get('genero', 'M')
        genero_filtrado = v_genero.strip().upper()[0] if v_genero else 'M'  # Asegura 'M' o 'F'

        v_estado = request.form.get('estado', 'A')
        estado_filtrado = v_estado.strip().upper()[0] if v_estado else 'A'  # Asegura 'A' o 'I'

        # Conversión de la Carga Horaria a entero de forma segura
        v_carga = request.form.get('carga_horaria')
        carga_filtrada = int(v_carga) if v_carga and v_carga.isdigit() else None

        # Recopilación estructurada mapeando los nombres de los inputs del HTML
        datos_personal = {
            "cedula":           request.form.get('cedula'),
            "nombres":          request.form.get('nombres'),
            "apellidos":        request.form.get('apellidos'),
            "especialidad":     request.form.get('especialidad'),
            "telefono":         request.form.get('telefono') or None,
            "correo":           request.form.get('correo') or None,
            "fecha_nacimiento": request.form.get('fecha_nacimiento') or None,
            "genero":           genero_filtrado,    # Forzado a longitud 1
            "fecha_ingreso":    request.form.get('fecha_ingreso') or None,
            "turno":            request.form.get('turno'),
            "carga_horaria":    carga_filtrada,     # Guardado como número entero
            "estado":           estado_filtrado,    # Forzado a longitud 1
            "observaciones":    request.form.get('observaciones') or None
        }

        try:
            response = supabase.table("personal").insert(datos_personal).execute()
            flash(f"Personal {datos_personal['nombres']} guardado de forma exitosa.")
        except Exception as e:
            flash(f"Error al registrar personal: {str(e)}")

        return redirect(url_for('personal'))

    # GET: renderiza el formulario con la tabla de personal
    lista_personal = []
    try:
        response = supabase.table("personal").select("*").execute()
        lista_personal = response.data
    except Exception as e:
        flash(f"Error al obtener la lista de personal: {str(e)}")

    return render_template('personal.html', lista_personal=lista_personal)
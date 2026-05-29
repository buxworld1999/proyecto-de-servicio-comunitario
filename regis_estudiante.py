from flask import render_template, request, redirect, url_for, flash

# Importar supabase desde db.py — sin importaciones circulares
from db import supabase


def registro_estudiantes():
    """
    Ruta de Estudiantes: Captura el formulario y registra un estudiante
    en la tabla 'estudiante' de Supabase controlando la longitud de los tipos char(1).
    """
    if request.method == 'POST':
        # Captura y normalización estricta a 1 carácter para evitar el error 22001
        v_genero = request.form.get('genero', 'M')
        genero_filtrado = v_genero.strip().upper()[0] if v_genero else 'M'  # Asegura 'M' o 'F'

        v_estado = request.form.get('estado', 'A')
        estado_filtrado = v_estado.strip().upper()[0] if v_estado else 'A'  # Asegura 'A' o 'I'

        # Recopilación estructurada mapeando el esquema de producción
        datos_estudiante = {
            "cedula":           request.form.get('cedula'),
            "nacionalidad":     request.form.get('nacionalidad'),
            "nombres":          request.form.get('nombres'),
            "apellidos":        request.form.get('apellidos'),
            "fecha_nacimiento": request.form.get('fecha_nacimiento') or None,
            "genero":           genero_filtrado,    # Forzado a longitud 1
            "telefono":         request.form.get('telefono') or None,
            "correo":           request.form.get('correo') or None,
            "direccion":        request.form.get('direccion') or None,
            "estado":           estado_filtrado,    # Forzado a longitud 1
            "foto":             None
        }

        try:
            response = supabase.table("estudiante").insert(datos_estudiante).execute()
            flash(f"Estudiante {datos_estudiante['nombres']} guardado de forma exitosa.")
        except Exception as e:
            flash(f"Error al registrar estudiante: {str(e)}")

        return redirect(url_for('registro_estudiantes'))

    return render_template('registro_estudiantes.html')
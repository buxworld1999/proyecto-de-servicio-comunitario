from flask import render_template, request, redirect, url_for, flash

# Importar supabase desde db.py — sin importaciones circulares
from db import supabase


def registro_estudiantes():
    """
    Ruta: Captura el formulario completo y registra un estudiante
    en la tabla 'estudiante' de Supabase controlando longitudes bpchar.
    """
    if request.method == 'POST':
        # Captura y normalización estricta a 1 carácter para evitar el error 22001
        v_genero = request.form.get('genero', 'M')
        genero_filtrado = v_genero.strip().upper()[0] if v_genero else 'M'
        
        v_estado = request.form.get('estado_estudiante', 'A')
        estado_filtrado = v_estado.strip().upper()[0] if v_estado else 'A'

        # Recopilación estructurada mapeando el esquema de la base de datos
        datos_estudiante = {
            # 1. Identificación y Personales Básicos
            "cedula": request.form.get('cedula'),
            "nacionalidad": request.form.get('nacionalidad'),
            "nombres": request.form.get('nombres'),
            "apellidos": request.form.get('apellidos'),
            "genero": genero_filtrado,
            
            # 2. Información de Nacimiento
            "fecha_nacimiento": request.form.get('fecha_nacimiento') or None,
            "lugar_nacimiento": request.form.get('lugar_nacimiento') or None,
            "estado_nacimiento": request.form.get('estado_nacimiento') or None,
            "municipio_nacimiento": request.form.get('municipio_nacimiento') or None,
            
            # 3. Contacto y Ubicación
            "direccion": request.form.get('direccion') or None,
            "telefono": request.form.get('telefono') or None,
            "correo": request.form.get('correo') or None,
            
            # 4. Datos Antropométricos y Salud (Convertidos a float o None)
            "estatura": float(request.form.get('estatura')) if request.form.get('estatura') else None,
            "peso": float(request.form.get('peso')) if request.form.get('peso') else None,
            "talla_camisa": request.form.get('talla_camisa') or None,
            "talla_pantalon": request.form.get('talla_pantalon') or None,
            "talla_zapatos": request.form.get('talla_zapatos') or None,
            "condiciones_medicas": request.form.get('conditions_medicas') or None,
            "medicamentos": request.form.get('medicamentos') or None,
            
            # 5. Historial Académico, Año, Sección y Estado
            "plantel_procedencia": request.form.get('plantel_procedencia') or None,
            "fecha_ingreso": request.form.get('fecha_ingreso') or None,
            "anio": request.form.get('anio'),
            "seccion": request.form.get('seccion'),
            "estado_estudiante": estado_filtrado,
            "fecha_retiro": request.form.get('fecha_retiro') or None,
            "motivo_retiro": request.form.get('motivo_retiro') or None
        }

        try:
            # Inserción en la tabla de Supabase
            response = supabase.table("estudiante").insert(datos_estudiante).execute()
            flash(f"Estudiante {datos_estudiante['nombres']} {datos_estudiante['apellidos']} guardado de forma exitosa.", "success")
        except Exception as e:
            flash(f"Error al registrar estudiante: {str(e)}", "danger")
            
        return redirect(url_for('registro_estudiantes'))

    return render_template('registro_estudiantes.html')
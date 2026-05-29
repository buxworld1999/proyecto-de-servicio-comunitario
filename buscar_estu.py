from flask import Flask, render_template, request, redirect, url_for, flash, session
from db import supabase


def buscar_estu():
    """
    Ruta de la Prueba 3: Busca un estudiante en Supabase por su número de cédula.
    """
    estudiante = None
    error_busqueda = None

    if request.method == 'POST':
        v_cedula = request.form.get('cedula_buscar')

        if not v_cedula:
            error_busqueda = "Por favor, introduce un número de cédula."
        else:
            try:
                # Línea clave: Consulta filtrada a Supabase eliminando espacios en blanco accidentales
                response = supabase.table("estudiante").select("*").eq("cedula", v_cedula.strip()).execute()

                #Supabase devuelve los registros dentro de una lista en response.data
                if response.data:
                    estudiante = response.data[0]  # Extraemos el primer diccionario (estudiante) encontrado
                else:
                    error_busqueda = f"No se encontró ningún estudiante con la cédula: {v_cedula}"

            except Exception as e:
                error_busqueda = f"Error al conectar con la base de datos: {str(e)}"

    # Retorna la plantilla pasándole las variables (estén llenas o vacías)
    return render_template('buscar_estu.html', estudiante=estudiante, error=error_busqueda)
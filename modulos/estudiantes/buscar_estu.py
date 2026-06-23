from flask import render_template, request, redirect, url_for, flash, session
from db import supabase

def buscar_estu():
    """
    Ruta que cumple doble función:
    1. (GET) Muestra la lista completa de estudiantes o filtrada por año/sección.
    2. (POST) Busca un estudiante específico por cédula e incluye los datos de su representante.
    """
    estudiante_buscado = None
    lista_estudiantes = []
    error_busqueda = None

    # =========================================================================
    # LÓGICA 1: BÚSQUEDA ESPECÍFICA DE UN ESTUDIANTE Y SU REPRESENTANTE (POST)
    # =========================================================================
    if request.method == 'POST':
        v_cedula = request.form.get('cedula_buscar')

        if not v_cedula:
            error_busqueda = "Por favor, introduce un número de cédula."
        else:
            try:
                # Consulta relacional cruzando: estudiante -> estudiante_representante -> representante
                response_busqueda = supabase.table("estudiante") \
                    .select("""
                        *,
                        estudiante_representante (
                            parentesco,
                            es_representante_legal,
                            representante (
                                cedula,
                                nombres,
                                apellidos,
                                telefono,
                                correo
                            )
                        )
                    """) \
                    .eq("cedula", v_cedula.strip()) \
                    .execute()

                if response_busqueda.data:
                    estudiante_buscado = response_busqueda.data[0]
                else:
                    error_busqueda = f"No se encontró ningún estudiante con la cédula: {v_cedula}"

            except Exception as e:
                # Respaldo por si la estructura relacional es diferente o no hay FK directa
                try:
                    response_busqueda = supabase.table("estudiante").select("*").eq("cedula", v_cedula.strip()).execute()
                    if response_busqueda.data:
                        estudiante_buscado = response_busqueda.data[0]
                        error_busqueda = "Estudiante encontrado, pero verifica la relación con la tabla de representantes."
                    else:
                        error_busqueda = f"No se encontró ningún estudiante con la cédula: {v_cedula}"
                except Exception:
                    error_busqueda = f"Error al conectar con la base de datos: {str(e)}"

    # =========================================================================
    # LÓGICA 2: MOSTRAR TODOS LOS ESTUDIANTES O FILTRAR EN EL DIRECTORIO (GET)
    # =========================================================================
    # Capturamos los filtros que viajan de forma segura a través de los parámetros URL (?seccion=A&anio=1)
    filtro_seccion = request.args.get('seccion')
    filtro_anio = request.args.get('anio')

    try:
        # Iniciamos la consulta base para el directorio
        query_general = supabase.table("estudiante").select("*")

        # Aplicamos los filtros dinámicamente si el usuario hizo clic en los botones de filtrado
        if filtro_seccion and filtro_seccion.strip() != "":
            query_general = query_general.eq("seccion", filtro_seccion.strip())
        
        if filtro_anio and filtro_anio.strip() != "":
            # Cambiar "anio" si tu columna en PostgreSQL utiliza la letra 'ñ' ("año")
            query_general = query_general.eq("anio", filtro_anio.strip())

        # Ejecutamos la consulta general y ordenamos alfabéticamente o por cédula
        response_lista = query_general.order("cedula").execute()
        
        if response_lista.data:
            lista_estudiantes = response_lista.data

    except Exception as e:
        # Solo asignamos este error si no ocurrió un fallo en la búsqueda por POST previamente
        if not error_busqueda:
            error_busqueda = f"Error al cargar la lista de estudiantes: {str(e)}"

    # Retorna la misma plantilla inyectando tanto la información del estudiante consultado 
    # como la lista completa/filtrada del directorio escolar.
    return render_template(
        'estudiantes/buscar_estu.html', 
        estudiante=estudiante_buscado, 
        lista_estudiantes=lista_estudiantes, 
        error=error_busqueda
    )


import os
from flask import render_template, request

from db import supabase

def constancia_estudio():
    alumno = None
    error_busqueda = None
    alerta_estado = None

    if request.method == 'POST':
        cedula_buscar = request.form.get('cedula_estudiante')
        if cedula_buscar:
            try:
                response = supabase.table("estudiante").select("*").eq("cedula", cedula_buscar.strip()).execute()
                resultado = response.data
                
                if resultado:
                    alumno = resultado[0]
                    
                    # OPCIÓN A: Formatear Cédula con puntos (Ej: 27123456 -> 27.123.456)
                    ced_str = str(alumno.get('cedula', ''))
                    if ced_str.isdigit():
                        alumno['cedula_formateada'] = '{:,}'.format(int(ced_str)).replace(',', '.')
                    else:
                        alumno['cedula_formateada'] = ced_str

                    # OPCIÓN B: Lógica para separar Fecha de Nacimiento
                    # Asume que en tu BD tienes una columna 'fecha_nacimiento' tipo 'YYYY-MM-DD'
                    fecha_nac = alumno.get('fecha_nacimiento')
                    if fecha_nac and isinstance(fecha_nac, str) and len(fecha_nac) >= 10:
                        partes_fecha = fecha_nac.split('-')
                        if len(partes_fecha) == 3:
                            alumno['anio_nac'] = int(partes_fecha[0])
                            mes_num = int(partes_fecha[1])
                            alumno['dia_nac'] = int(partes_fecha[2])
                            
                            meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                            if 1 <= mes_num <= 12:
                                alumno['mes_nac'] = meses[mes_num]

                    # Validar Lugar y Estado (si no existen en BD, pone valores por defecto para no romper el diseño)
                    alumno['lugar_nacimiento'] = alumno.get('lugar_nacimiento') or "SAN FERNANDO"
                    alumno['estado_nacimiento'] = alumno.get('estado_nacimiento') or "APURE"

                    alerta_estado = "Constancia cargada exitosamente. Lista para imprimir."
                else:
                    error_busqueda = "Estudiante no registrado."
            except Exception as e:
                error_busqueda = f"Error: {str(e)}"

    return render_template('constancia_estudio.html', alumno=alumno, error_busqueda=error_busqueda, alerta_estado=alerta_estado)
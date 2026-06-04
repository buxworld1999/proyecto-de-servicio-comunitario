from flask import render_template, flash
from db import supabase

def secciones_view():
    """
    Ruta para visualizar a los estudiantes organizados por Año y Sección.
    """
    try:
        # Obtenemos directamente a los estudiantes (ya traen anio y seccion)
        response = supabase.table("estudiante").select(
            "cedula, nombres, apellidos, genero, anio, seccion"
        ).execute()
        
        datos = response.data or []
        
        # Agrupar los datos: 
        # estructura = { "1er Año": { "A": [est1, est2], "B": [...] }, "2do Año": ... }
        agrupacion = {}
        
        # Años predefinidos para mantener el orden
        anios_orden = ["1er Año", "2do Año", "3er Año", "4to Año", "5to Año"]
        for anio in anios_orden:
            agrupacion[anio] = {}
            
        for registro in datos:
            # Si el estudiante no tiene año o sección, lo saltamos o lo agrupamos en "No Asignado"
            anio = registro.get("anio")
            seccion = registro.get("seccion")
            
            if not anio or not seccion:
                continue
                
            if anio not in agrupacion:
                agrupacion[anio] = {}
                
            if seccion not in agrupacion[anio]:
                agrupacion[anio][seccion] = []
                
            nombre_completo = f"{registro.get('nombres', '')} {registro.get('apellidos', '')}".strip()
                
            agrupacion[anio][seccion].append({
                "cedula": registro.get("cedula"),
                "nombre_completo": nombre_completo,
                "genero": registro.get("genero", "N/A")
            })
            
        # Ordenar las secciones alfabéticamente dentro de cada año
        for anio in agrupacion:
            agrupacion[anio] = dict(sorted(agrupacion[anio].items()))
            # Ordenar estudiantes por nombre
            for seccion in agrupacion[anio]:
                agrupacion[anio][seccion].sort(key=lambda x: x['nombre_completo'])
                
    except Exception as e:
        flash(f"Error al cargar secciones: {str(e)}")
        agrupacion = {}

    return render_template('secciones.html', agrupacion=agrupacion)

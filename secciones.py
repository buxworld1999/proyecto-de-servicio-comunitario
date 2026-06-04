from flask import render_template, flash
from db import supabase

def secciones_view():
    """
    Ruta para visualizar a los estudiantes organizados por Año y Sección.
    """
    try:
        # Hacemos JOIN entre matricula, estudiante y seccion
        response = supabase.table("matricula").select(
            "codigo_ano_escolar, estudiante (cedula, nombres, apellidos, genero), seccion (codigo_grado, letra)"
        ).execute()
        
        datos = response.data or []
        
        agrupacion = {}
        
        anios_orden = ["1", "2", "3", "4", "5"]
        nombres_anios = {"1": "1er Año", "2": "2do Año", "3": "3er Año", "4": "4to Año", "5": "5to Año"}
        
        for num in anios_orden:
            agrupacion[nombres_anios[num]] = {}
            
        for registro in datos:
            # Obtener datos de las relaciones
            estudiante = registro.get("estudiante")
            seccion = registro.get("seccion")
            
            if not estudiante or not seccion:
                continue
                
            grado_num = seccion.get("codigo_grado")
            letra = seccion.get("letra")
            
            anio = nombres_anios.get(grado_num, "Desconocido")
            
            if anio not in agrupacion:
                agrupacion[anio] = {}
                
            if letra not in agrupacion[anio]:
                agrupacion[anio][letra] = []
                
            nombre_completo = f"{estudiante.get('nombres', '')} {estudiante.get('apellidos', '')}".strip()
                
            agrupacion[anio][letra].append({
                "cedula": estudiante.get("cedula"),
                "nombre_completo": nombre_completo,
                "genero": estudiante.get("genero", "N/A")
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

from flask import render_template, flash
from db import supabase

def secciones_view():
    """
    Ruta para visualizar a los estudiantes organizados por Año y Sección.
    """
    try:
        # Buscar cuál es el año escolar activo actualmente
        res_ano = supabase.table("ano_escolar").select("codigo").eq("activo", True).execute()
        anos_activos = res_ano.data or []
        codigo_ano_activo = anos_activos[0]['codigo'] if anos_activos else None

        # 1. FILTRADO EN BD: Traemos solo las matrículas con estado Activo ('A')
        # del año escolar VIGENTE. Sin el filtro de año, un estudiante ya promovido
        # sigue apareciendo en su grado viejo porque su matrícula anterior nunca
        # se desactivó (bug del script de promoción original, ya corregido, pero
        # las matrículas de años pasados siguen marcadas 'A' de por vida).
        query = supabase.table("matricula").select(
            "codigo_ano_escolar, estudiante (cedula, nombres, apellidos, genero), seccion (codigo_grado, letra)"
        ).eq("estado_matricula", "A")

        if codigo_ano_activo:
            query = query.eq("codigo_ano_escolar", codigo_ano_activo)

        response = query.execute()
        
        datos = response.data or []
        
        agrupacion = {}
        anios_orden = ["1", "2", "3", "4", "5"]
        nombres_anios = {"1": "1er Año", "2": "2do Año", "3": "3er Año", "4": "4to Año", "5": "5to Año"}
        
        for num in anios_orden:
            agrupacion[nombres_anios[num]] = {}
            
        # 2. ESCUDO ANTI-DUPLICADOS EN PYTHON: Evita clones si la BD tiene registros repetidos
        estudiantes_procesados = set()
        
        for registro in datos:
            estudiante = registro.get("estudiante")
            seccion = registro.get("seccion")
            
            if not estudiante or not seccion:
                continue
                
            cedula = estudiante.get("cedula")
            grado_num = seccion.get("codigo_grado")
            letra = seccion.get("letra")
            
            anio = nombres_anios.get(grado_num, "Desconocido")
            
            # Llave única por Año, Sección y Cédula
            llave_duplicado = (anio, letra, cedula)
            
            # Si este alumno ya se agregó en esta sección, lo saltamos
            if llave_duplicado in estudiantes_procesados:
                continue
                
            # Si es la primera vez que lo vemos, lo registramos en el set
            estudiantes_procesados.add(llave_duplicado)
            
            if anio not in agrupacion:
                agrupacion[anio] = {}
                
            if letra not in agrupacion[anio]:
                agrupacion[anio][letra] = []
                
            nombre_completo = f"{estudiante.get('nombres', '')} {estudiante.get('apellidos', '')}".strip()
                
            agrupacion[anio][letra].append({
                "cedula": cedula,
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

    return render_template('academico/secciones.html', agrupacion=agrupacion) 
from flask import Blueprint, render_template, request, flash, redirect, url_for
from db import supabase

def get_estudiantes():
    res = supabase.table("estudiante").select("cedula, nombres, apellidos").execute()
    return res.data or []

def get_anos_escolares():
    res = supabase.table("ano_escolar").select("codigo, descripcion").eq("activo", True).execute()
    return res.data or []

def get_secciones():
    res = supabase.table("seccion").select("codigo, letra, codigo_grado").execute()
    return res.data or []

def matricula_view():
    if request.method == 'POST':
        cedula = request.form.get('cedula')
        codigo_ano = request.form.get('codigo_ano_escolar')
        codigo_seccion = request.form.get('codigo_seccion')
        condicion = request.form.get('condicion_ingreso')
        
        datos_matricula = {
            "cedula_estudiante": cedula,
            "codigo_ano_escolar": codigo_ano,
            "codigo_seccion": codigo_seccion,
            "condicion_ingreso": condicion,
            "estado_matricula": 'A'
        }
        
        try:
            supabase.table("matricula").insert(datos_matricula).execute()
            
            # Actualizar perfil base del estudiante
            if codigo_seccion and len(codigo_seccion) >= 2:
                grado = codigo_seccion[0]
                letra = codigo_seccion[1:]
                mapa = {'1': '1er Año', '2': '2do Año', '3': '3er Año', '4': '4to Año', '5': '5to Año'}
                nombre_anio = mapa.get(grado)
                if nombre_anio:
                    supabase.table("estudiante").update({"anio": nombre_anio, "seccion": letra}).eq("cedula", cedula).execute()

            flash("Matrícula procesada correctamente", "success")
        except Exception as e:
            flash(f"Error al matricular: {str(e)}", "danger")
            
        return redirect(url_for('proceso_matricula'))
        
    # GET
    estudiantes = get_estudiantes()
    anos = get_anos_escolares()
    secciones = get_secciones()
    return render_template('estudiantes/matricula.html', estudiantes=estudiantes, anos=anos, secciones=secciones)

def matricula_automatica_view():
    """Realiza la matrícula masiva basada en los campos anio y seccion de los estudiantes."""
    if request.method == 'POST':
        try:
            # Obtener el año escolar activo
            resp_ano = supabase.table("ano_escolar").select("codigo").eq("activo", True).limit(1).execute()
            ano_activo = resp_ano.data[0]['codigo'] if resp_ano.data else None
            
            if not ano_activo:
                flash("No hay un año escolar activo configurado.", "danger")
                return redirect(url_for('proceso_matricula'))
            
            # Obtener estudiantes
            res_est = supabase.table("estudiante").select("cedula, anio, seccion").execute()
            estudiantes = res_est.data or []
            
            # Mapear años de texto a códigos de grado
            mapa_anios = {
                "1er Año": "1",
                "2do Año": "2",
                "3er Año": "3",
                "4to Año": "4",
                "5to Año": "5"
            }
            # Por si están guardados directamente como '1', '2', etc.
            mapa_anios.update({"1": "1", "2": "2", "3": "3", "4": "4", "5": "5"})
            
            # Obtener matrículas existentes para el año activo para no duplicar
            res_mat = supabase.table("matricula").select("cedula_estudiante").eq("codigo_ano_escolar", ano_activo).execute()
            matriculados = {m['cedula_estudiante'] for m in (res_mat.data or [])}
            
            nuevos = 0
            
            for est in estudiantes:
                cedula = est.get("cedula")
                anio_val = est.get("anio")
                letra_seccion = est.get("seccion")
                
                # Si ya está matriculado, ignorar
                if cedula in matriculados:
                    continue
                
                if not anio_val or not letra_seccion:
                    continue
                
                grado_codigo = mapa_anios.get(anio_val)
                if not grado_codigo:
                    continue
                    
                codigo_seccion = f"{grado_codigo}{letra_seccion.upper()}"
                
                datos = {
                    "cedula_estudiante": cedula,
                    "codigo_ano_escolar": ano_activo,
                    "codigo_seccion": codigo_seccion,
                    "condicion_ingreso": "R",  # Regular por defecto en migración
                    "estado_matricula": "A"
                }
                
                supabase.table("matricula").insert(datos).execute()
                nuevos += 1
                
            flash(f"Matrícula automática completada. {nuevos} estudiantes matriculados en {ano_activo}.", "success")
        except Exception as e:
            flash(f"Error en la matrícula automática: {str(e)}", "danger")
            
        return redirect(url_for('proceso_matricula'))

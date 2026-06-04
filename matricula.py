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
            flash("Matrícula procesada correctamente", "success")
        except Exception as e:
            flash(f"Error al matricular: {str(e)}", "error")
            
        return redirect(url_for('proceso_matricula'))
        
    # GET
    estudiantes = get_estudiantes()
    anos = get_anos_escolares()
    secciones = get_secciones()
    return render_template('matricula.html', estudiantes=estudiantes, anos=anos, secciones=secciones)

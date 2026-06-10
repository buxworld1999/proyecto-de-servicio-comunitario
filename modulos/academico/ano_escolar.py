from flask import render_template, request, redirect, url_for, flash
from db import supabase

def ano_escolar_view():
    """
    Controlador principal para el módulo de Año Escolar.
    Soporta el registro (POST) y la visualización del historial (GET).
    """
    if request.method == 'POST':
        # 1. Recoger datos del formulario HTML
        codigo = request.form.get('codigo')          # Ej: "2026-2027"
        descripcion = request.form.get('descripcion')  # Ej: "Periodo Regular Institucional"
        ano_inicio = request.form.get('ano_inicio')    # Ej: 2026
        ano_fin = request.form.get('ano_fin')          # Ej: 2027
        fecha_inicio = request.form.get('fecha_inicio')# Ej: "2026-09-15"
        fecha_fin = request.form.get('fecha_fin')      # Ej: "2027-07-15"

        try:
            # 2. Construir el paquete de datos alineado a tu tabla.
            nuevo_periodo = {
                "codigo": codigo,
                "descripcion": descripcion,
                "ano_inicio": int(ano_inicio) if ano_inicio else None,
                "ano_fin": int(ano_fin) if ano_fin else None,
                "fecha_inicio": fecha_inicio if fecha_inicio else None,
                "fecha_fin": fecha_fin if fecha_fin else None,
                "estado": "I",       # 'I' de Inactivo por defecto al crearse
                "activo": False      # False (apagado) hasta que se decida activar
            }

            # 3. Guardar en BD.
            supabase.table("ano_escolar").insert(nuevo_periodo).execute()
            flash(f"¡Periodo Escolar {codigo} registrado con éxito!", "success")
            
        except Exception as e:
            flash(f"Error al guardar en Supabase: {str(e)}", "error")
        
        return redirect(url_for('anio_escolar'))

    # --- MÉTODO GET: Leer datos de Supabase para llenar tu tabla ---
    try:
        # Traemos todos los años ordenados por código descendente (el más nuevo arriba)
        respuesta = supabase.table("ano_escolar").select("*").order("codigo", desc=True).execute()
        periodos_registrados = respuesta.data
    except Exception as e:
        periodos_registrados = []
        flash(f"Error al cargar el historial desde Supabase: {str(e)}", "error")

    return render_template('ano_escolar.html', periodos=periodos_registrados)


def activar_ano_logic(codigo_ano):
    """
    Aplica la Regla de Oro: Desactiva el año vigente actual 
    y activa el nuevo periodo seleccionado.
    """
    try:
        # PASO 1: "Apagar el viejo" -> Pone en Inactivo (False / 'I') al que esté activo
        supabase.table("ano_escolar").update({"activo": False, "estado": "I"}).eq("activo", True).execute()

        # PASO 2: "Prender el nuevo" -> Pone en Activo (True / 'A') al código seleccionado
        supabase.table("ano_escolar").update({"activo": True, "estado": "A"}).eq("codigo", codigo_ano).execute()

        flash(f"¡El periodo {codigo_ano} ahora es el Año Escolar Activo del Liceo!", "success")
    except Exception as e:
        flash(f"No se pudo cambiar el año activo: {str(e)}", "error")
    
    return redirect(url_for('anio_escolar'))
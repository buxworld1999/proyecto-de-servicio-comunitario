from flask import render_template, request, redirect, url_for, flash, session

# Importar supabase desde db.py — sin importaciones circulares
from db import supabase

def reportes():
    if request.method == 'POST':
        accion = request.form.get('accion')
        
        # --- NUEVA ACCIÓN: ACTUALIZAR ESTADO ---
        if accion == 'cambiar_estado':
            reporte_id = request.form.get('reporte_id')
            nuevo_estado = request.form.get('nuevo_estado', 'Resuelto')
            
            try:
                supabase.table("acontecimientos") \
                    .update({"estado": nuevo_estado}) \
                    .eq("id", reporte_id) \
                    .execute()
                flash(f"Acontecimiento #{reporte_id} marcado como {nuevo_estado}.", "success")
            except Exception as e:
                flash(f"Error al actualizar el estado: {str(e)}", "danger")
                
            return redirect(url_for('reportes'))

        # --- ACCIÓN EXISTENTE: NUEVO ACONTECIMIENTO ---
        if accion == 'nuevo_acontecimiento':
            titulo = request.form.get('titulo', '').strip()
            motivo = request.form.get('motivo', '').strip()
            responsables = request.form.get('responsables', '').strip()

            if not titulo or not motivo:
                flash("El título y el motivo son campos obligatorios.", "danger")
            else:
                nuevo_reporte = {
                    "usuario_nombre": session.get('nombre', 'Usuario'),
                    "usuario_rol": session.get('rol', 'anonimo'),
                    "titulo": titulo,
                    "motivo": motivo,
                    "responsables": responsables if responsables else "Por asignar",
                    "estado": "Pendiente"
                }
                try:
                    supabase.table("acontecimientos").insert(nuevo_reporte).execute()
                    flash("Acontecimiento registrado exitosamente en el muro.", "success")
                except Exception as e:
                    flash(f"Error al registrar en la base de datos: {str(e)}", "danger")
            
            return redirect(url_for('reportes'))

    # Método GET
    acontecimientos = []
    try:
        response = supabase.table("acontecimientos").select("*").order("creado_at", desc=True).execute()
        acontecimientos = response.data
    except Exception as e:
        flash(f"Error al cargar el feed de acontecimientos: {str(e)}", "danger")

    return render_template(
        'reportes/reportes.html', 
        usuario_nombre=session.get('nombre', 'Usuario'),
        usuario_rol=session.get('rol', ''),
        acontecimientos=acontecimientos
    )
def _modulo_en_desarrollo(nombre: str, icono: str) -> str:
    """ Renderiza la plantilla de modulos en desarrollo """
    return render_template('en_desarrollo.html', nombre=nombre, icono=icono)
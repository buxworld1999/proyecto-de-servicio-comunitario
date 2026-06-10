# gestion_usuarios.py
# Módulo de Gestión de Usuarios para PRISMA
# Unidad Educativa Carmen Ruíz

from flask import render_template, request, redirect, url_for, flash
from db import supabase

def gestion_usuarios():
    # ── CARGAR DATOS ──
    # 1. Obtener la lista de usuarios desde la base de datos
    try:
        usuarios_resp = supabase.table("usuario").select("*").execute()
        usuarios_lista = usuarios_resp.data or []
    except Exception as e:
        flash(f"Error al obtener usuarios: {str(e)}")
        usuarios_lista = []

    # 2. Obtener todo el personal para mapear los nombres reales de los usuarios
    try:
        personal_resp = supabase.table("personal").select("cedula, nombres, apellidos").execute()
        personal_lista = personal_resp.data or []
    except Exception as e:
        flash(f"Error al obtener personal: {str(e)}")
        personal_lista = []

    # Mapear cédula a nombre completo en un diccionario
    personal_dict = {p['cedula']: f"{p['nombres']} {p['apellidos']}" for p in personal_lista}

    # Cruzar datos de personal con los usuarios
    for u in usuarios_lista:
        u['nombre_personal'] = personal_dict.get(u['cedula_personal'], "No asociado")

    # 3. Filtrar personal que NO tiene un usuario creado aún
    cedulas_con_usuario = {u['cedula_personal'] for u in usuarios_lista if u.get('cedula_personal')}
    personal_disponible = [p for p in personal_lista if p['cedula'] not in cedulas_con_usuario]

    # ── PROCESAR ACCIONES (POST) ──
    if request.method == 'POST':
        accion = request.form.get('accion')

        # Acción A: Crear un nuevo usuario
        if accion == 'crear':
            v_cedula = request.form.get('cedula_personal')
            v_codigo = request.form.get('codigo_usuario', '').strip()
            v_clave = request.form.get('clave', '').strip()
            v_rol = request.form.get('rol', 'docente').strip().lower()
            v_estado = request.form.get('estado', 'A')

            if not v_cedula or not v_codigo or not v_clave:
                flash("Todos los campos obligatorios son requeridos.")
                return redirect(url_for('usuarios'))

            datos_nuevo = {
                "cedula_personal": v_cedula,
                "codigo_usuario": v_codigo,
                "clave_hash": v_clave,
                "rol": v_rol,
                "estado": v_estado
            }
            try:
                supabase.table("usuario").insert(datos_nuevo).execute()
                flash(f"Usuario '{v_codigo}' creado correctamente.")
            except Exception as e:
                flash(f"Error al crear usuario: {str(e)}")

        # Acción B: Cambiar el estado (Activar/Desactivar)
        elif accion == 'cambiar_estado':
            v_usuario_id = request.form.get('usuario_id')
            v_estado_actual = request.form.get('estado_actual')
            nuevo_estado = 'I' if v_estado_actual == 'A' else 'A'

            try:
                supabase.table("usuario").update({"estado": nuevo_estado}).eq("id", v_usuario_id).execute()
                flash("Estado del usuario actualizado.")
            except Exception as e:
                flash(f"Error al cambiar estado: {str(e)}")

        # Acción C: Cambiar la contraseña
        elif accion == 'cambiar_clave':
            v_usuario_id = request.form.get('usuario_id')
            v_nueva_clave = request.form.get('nueva_clave', '').strip()

            if not v_nueva_clave:
                flash("La contraseña no puede estar vacía.")
                return redirect(url_for('usuarios'))

            try:
                supabase.table("usuario").update({"clave_hash": v_nueva_clave}).eq("id", v_usuario_id).execute()
                flash("Contraseña actualizada correctamente.")
            except Exception as e:
                flash(f"Error al actualizar la contraseña: {str(e)}")

        return redirect(url_for('usuarios'))

    return render_template(
        'usuarios.html',
        usuarios=usuarios_lista,
        personal_disponible=personal_disponible
    )

# gestion_usuarios.py
# Módulo de Gestión de Usuarios para PRISMA
# Unidad Educativa Carmen Ruíz
#
# Acceso: exclusivo para el rol 'admin'.
# Toda la lógica de restricción por rol director fue eliminada —
# el decorador @rol_required('admin') en principal.py garantiza que
# SOLO el administrador llega a este módulo.

from flask import render_template, request, redirect, url_for, flash, session
from db import supabase
from auth import ROLES_VALIDOS, ROLES_ETIQUETAS
from werkzeug.security import generate_password_hash


# Roles que pueden asignarse desde la interfaz (excluye 'admin' para seguridad)
# El administrador puede crear admins directamente en la base de datos si es necesario.
ROLES_ASIGNABLES = [
    'director',
    'subdirector_academico',
    'secretaria_direccion',
    'coordinador_evaluacion',
    'coordinador_registro',
    'secretaria_registro',
    'coordinador_seccional',
    'secretaria_seccional',
    'docente',
    'admin',  # Solo un admin puede crear otro admin
]


def gestion_usuarios():

    # ── CARGAR DATOS ──────────────────────────────────────────────────────────
    try:
        usuarios_resp = supabase.table("usuario").select("*").execute()
        usuarios_lista = usuarios_resp.data or []
        cedulas_con_usuario = {u['cedula_personal'] for u in usuarios_lista if u.get('cedula_personal')}
    except Exception as e:
        flash(f"Error al obtener usuarios: {str(e)}", "danger")
        usuarios_lista = []
        cedulas_con_usuario = set()

    # Obtener personal para mapear nombres reales
    try:
        personal_resp = supabase.table("personal").select(
            "cedula, nombres, apellidos, cargo, especialidad"
        ).execute()
        personal_lista = personal_resp.data or []
    except Exception as e:
        flash(f"Error al obtener personal: {str(e)}", "danger")
        personal_lista = []

    personal_dict = {p['cedula']: f"{p['nombres']} {p['apellidos']}" for p in personal_lista}

    # Enriquecer usuarios con nombre de personal y etiqueta de rol
    for u in usuarios_lista:
        u['nombre_personal'] = personal_dict.get(u['cedula_personal'], "No asociado")
        u['etiqueta_rol'] = ROLES_ETIQUETAS.get(u.get('rol', ''), u.get('rol', ''))

    # Personal disponible para crear cuenta (sin usuario aún)
    personal_disponible = [p for p in personal_lista if p['cedula'] not in cedulas_con_usuario]

    # ── PROCESAR ACCIONES (POST) ──────────────────────────────────────────────
    if request.method == 'POST':
        accion = request.form.get('accion')

        # ── Acción A: Crear nuevo usuario ────────────────────────────────────
        if accion == 'crear':
            v_rol    = request.form.get('rol', 'docente').strip().lower()
            v_codigo = request.form.get('codigo_usuario', '').strip()
            v_clave  = request.form.get('clave', '').strip()
            v_estado = request.form.get('estado', 'A')
            v_cedula = request.form.get('cedula_personal', '').strip()

            # Validar rol
            if v_rol not in ROLES_VALIDOS:
                flash(f"Rol '{v_rol}' no es válido.", "danger")
                return redirect(url_for('usuarios'))

            if not v_cedula or not v_codigo or not v_clave:
                flash("Todos los campos obligatorios son requeridos.", "danger")
                return redirect(url_for('usuarios'))

            # Hashear la contraseña antes de guardar
            clave_hash = generate_password_hash(v_clave)

            datos_nuevo = {
                "cedula_personal": v_cedula,
                "codigo_usuario":  v_codigo,
                "clave_hash":      clave_hash,
                "rol":             v_rol,
                "estado":          v_estado,
            }
            try:
                supabase.table("usuario").insert(datos_nuevo).execute()
                flash(f"Usuario '{v_codigo}' creado correctamente con rol '{ROLES_ETIQUETAS.get(v_rol, v_rol)}'.", "success")
            except Exception as e:
                flash(f"Error al crear usuario: {str(e)}", "danger")

        # ── Acción B: Cambiar estado (Activar/Desactivar) ────────────────────
        elif accion == 'cambiar_estado':
            v_usuario_id   = request.form.get('usuario_id')
            v_estado_actual = request.form.get('estado_actual')
            nuevo_estado = 'I' if v_estado_actual == 'A' else 'A'
            try:
                supabase.table("usuario").update({"estado": nuevo_estado}).eq("id", v_usuario_id).execute()
                flash("Estado del usuario actualizado.", "success")
            except Exception as e:
                flash(f"Error al cambiar estado: {str(e)}", "danger")

        # ── Acción C: Cambiar contraseña ─────────────────────────────────────
        elif accion == 'cambiar_clave':
            v_usuario_id  = request.form.get('usuario_id')
            v_nueva_clave = request.form.get('nueva_clave', '').strip()

            if not v_nueva_clave:
                flash("La contraseña no puede estar vacía.", "danger")
                return redirect(url_for('usuarios'))

            # Guardar siempre con hash seguro
            nuevo_hash = generate_password_hash(v_nueva_clave)
            try:
                supabase.table("usuario").update({"clave_hash": nuevo_hash}).eq("id", v_usuario_id).execute()
                flash("Contraseña actualizada correctamente.", "success")
            except Exception as e:
                flash(f"Error al actualizar la contraseña: {str(e)}", "danger")

        # ── Acción D: Cambiar rol ────────────────────────────────────────────
        elif accion == 'cambiar_rol':
            v_usuario_id = request.form.get('usuario_id')
            v_nuevo_rol  = request.form.get('nuevo_rol', '').strip().lower()

            if v_nuevo_rol not in ROLES_VALIDOS:
                flash(f"Rol '{v_nuevo_rol}' no es válido.", "danger")
                return redirect(url_for('usuarios'))

            try:
                supabase.table("usuario").update({"rol": v_nuevo_rol}).eq("id", v_usuario_id).execute()
                flash(f"Rol actualizado a '{ROLES_ETIQUETAS.get(v_nuevo_rol, v_nuevo_rol)}'.", "success")
            except Exception as e:
                flash(f"Error al cambiar el rol: {str(e)}", "danger")

        # ── Acción E: Eliminar usuario ───────────────────────────────────────
        elif accion == 'eliminar':
            v_usuario_id = request.form.get('usuario_id')

            # Protección: no se puede eliminar la propia cuenta
            if str(v_usuario_id) == str(session.get('usuario_id')):
                flash("No puedes eliminar tu propio usuario.", "warning")
                return redirect(url_for('usuarios'))

            try:
                supabase.table("usuario").delete().eq("id", v_usuario_id).execute()
                flash("Usuario eliminado correctamente.", "success")
            except Exception as e:
                flash(f"Error al eliminar usuario: {str(e)}", "danger")

        return redirect(url_for('usuarios'))

    return render_template(
        'admin/usuarios.html',
        usuarios           = usuarios_lista,
        personal_disponible = personal_disponible,
        roles_asignables   = ROLES_ASIGNABLES,
        roles_etiquetas    = ROLES_ETIQUETAS,
        rol_usuario        = session.get('rol', ''),
    )

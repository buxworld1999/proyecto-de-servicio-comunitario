from flask import render_template, request, redirect, url_for, flash, session

# Importar supabase desde db.py — sin importaciones circulares
from db import supabase



def login():
    """
    Procesa el formulario de inicio de sesión.
    """
    v_codigo = request.form.get('codigo_usuario', '').strip()
    v_clave  = request.form.get('clave', '').strip()

    # Validación básica de campos vacíos
    if not v_codigo or not v_clave:
        return render_template('index.html', error="Por favor ingresa tu código y contraseña.")

    try:
        # ── PASO 1: Verificar credenciales ───────────────────────────
        response = supabase.table("usuario") \
            .select("id, codigo_usuario, rol, cedula_personal, estado") \
            .eq("codigo_usuario", v_codigo) \
            .eq("clave_hash", v_clave) \
            .execute()

        if not response.data:
            return render_template('index.html', error="Código de usuario o contraseña incorrectos.")

        u = response.data[0]

        # ── PASO 2: Verificar cuenta activa ──────────────────────────
        if u.get('estado') == 'I':
            return render_template('index.html',
                error="Tu cuenta está inactiva. Contacta al administrador.")

        # ── PASO 3: Obtener nombre desde tabla 'personal' (JOIN) ─────
        nombre_display = u['codigo_usuario']
        try:
            personal_resp = supabase.table("personal") \
                .select("nombres, apellidos") \
                .eq("cedula", u['cedula_personal']) \
                .execute()
            if personal_resp.data:
                p = personal_resp.data[0]
                nombre_display = f"{p['nombres']} {p['apellidos']}"
        except Exception:
            pass

        # ── PASO 4: Establecer sesión (rol normalizado a minúsculas) ─
        rol_normalizado = (u.get('rol') or 'sin_rol').strip().lower()
        session.clear()
        session.permanent     = True
        session['usuario_id'] = u['id']
        session['codigo']     = u['codigo_usuario']
        session['rol']        = rol_normalizado
        session['nombre']     = nombre_display

        return redirect(url_for('menu'))

    except Exception as e:
        return render_template('index.html', error=f"Error del servidor: {str(e)}")
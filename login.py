"""
login.py — Módulo de Inicio de Sesión
PRISMA — Sistema de Gestión Escolar | Unidad Educativa Carmen Ruíz

Seguridad:
    - Verificación de contraseña con werkzeug.security (bcrypt)
    - Compatibilidad con contraseñas antiguas en texto plano (migración gradual)
    - Al iniciar sesión con clave plana, se migra automáticamente al hash seguro
    - Normalización del rol a minúsculas
"""

from flask import render_template, request, redirect, url_for, session

from werkzeug.security import check_password_hash, generate_password_hash

# Importar supabase desde db.py — sin importaciones circulares
from db import supabase


def _verificar_clave(clave_ingresada: str, clave_bd: str) -> bool:
    """
    Verifica la contraseña del usuario con soporte para:
    1. Contraseñas hasheadas con werkzeug (pbkdf2:sha256 / scrypt)
    2. Contraseñas en texto plano (legacy — se migran al primer login)

    Args:
        clave_ingresada: Contraseña enviada por el formulario.
        clave_bd:        Hash (o texto plano) almacenado en la BD.

    Returns:
        True si las contraseñas coinciden.
    """
    if not clave_ingresada or not clave_bd:
        return False

    # Detectar si está hasheada (los hashes de werkzeug comienzan con 'pbkdf2:' o 'scrypt:')
    if clave_bd.startswith(('pbkdf2:', 'scrypt:')):
        return check_password_hash(clave_bd, clave_ingresada)

    # Contraseña en texto plano (legacy) — comparación directa
    return clave_ingresada == clave_bd


def _migrar_clave_a_hash(usuario_id: int, clave_plana: str) -> None:
    """
    Migra automáticamente una contraseña en texto plano a hash seguro
    la primera vez que el usuario inicia sesión exitosamente.

    Esta función es silenciosa — si falla, el login continúa normal.

    Args:
        usuario_id:  ID del usuario en la tabla 'usuario'.
        clave_plana: Contraseña en texto plano a hashear.
    """
    try:
        nuevo_hash = generate_password_hash(clave_plana)
        supabase.table("usuario") \
            .update({"clave_hash": nuevo_hash}) \
            .eq("id", usuario_id) \
            .execute()
    except Exception as e:
        print(f"[LOGIN] Advertencia: No se pudo migrar la clave del usuario {usuario_id}: {e}")


def login():
    """
    Procesa el formulario de inicio de sesión.

    Flujo:
    1. Validar campos obligatorios
    2. Buscar usuario por código (sin comparar clave en BD directamente)
    3. Verificar clave con soporte legacy + auto-migración a hash
    4. Verificar cuenta activa
    5. Obtener nombre real desde tabla 'personal'
    6. Establecer sesión segura
    """
    v_codigo = request.form.get('codigo_usuario', '').strip()
    v_clave  = request.form.get('clave', '').strip()

    # ── Validación básica de campos vacíos ─────────────────────────────
    if not v_codigo or not v_clave:
        return render_template('index.html', error="Por favor ingresa tu código y contraseña.")

    try:
        # ── PASO 1: Buscar usuario por código (sin exponer hash en log) ─
        response = supabase.table("usuario") \
            .select("id, codigo_usuario, rol, cedula_personal, estado, clave_hash") \
            .eq("codigo_usuario", v_codigo) \
            .execute()

        if not response.data:
            return render_template('index.html', error="Código de usuario o contraseña incorrectos.")

        u = response.data[0]

        # ── PASO 2: Verificar contraseña (hash o legacy) ────────────────
        clave_bd = u.get('clave_hash', '')
        if not _verificar_clave(v_clave, clave_bd):
            return render_template('index.html', error="Código de usuario o contraseña incorrectos.")

        # ── PASO 3: Verificar cuenta activa ─────────────────────────────
        if u.get('estado') == 'I':
            return render_template('index.html',
                error="Tu cuenta está inactiva. Contacta al administrador.")

        # ── PASO 4: Migración automática de clave plana a hash ──────────
        if clave_bd and not clave_bd.startswith(('pbkdf2:', 'scrypt:')):
            _migrar_clave_a_hash(u['id'], v_clave)

        # ── PASO 5: Obtener nombre desde tabla 'personal' (JOIN) ─────────
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
            pass  # Usar el código como nombre si falla el JOIN

        # ── PASO 6: Establecer sesión (rol normalizado a minúsculas) ─────
        rol_normalizado = (u.get('rol') or 'sin_rol').strip().lower()
        session.clear()
        session.permanent          = True
        session['usuario_id']      = u['id']
        session['codigo']          = u['codigo_usuario']
        session['rol']             = rol_normalizado
        session['nombre']          = nombre_display
        session['cedula_personal'] = u.get('cedula_personal')

        return redirect(url_for('menu'))

    except Exception as e:
        return render_template('index.html', error=f"Error del servidor: {str(e)}")
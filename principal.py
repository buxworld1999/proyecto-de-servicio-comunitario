"""
principal.py — Aplicación principal PRISMA
Sistema de Gestión Escolar | Unidad Educativa Carmen Ruíz

Arquitectura:
    - Autenticación con Flask Sessions
    - Control de acceso por roles (RBAC) via auth.py
    - Dashboard único (menu.html) con menú dinámico por rol
    - Protección de rutas con decoradores @login_required y @rol_required
"""

import os
from datetime import timedelta
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session

# Módulo RBAC centralizado
from auth import get_menu_items, login_required, rol_required

# Módulos del Sistema


# Cargar variables de entorno
load_dotenv()


# Cliente de Supabase centralizado en db.py (evita importaciones circulares)
from db import supabase


# ===================================================================
# CONFIGURACIÓN DE FLASK
# ===================================================================

app = Flask(__name__)

# Clave secreta para firmar las cookies de sesión
app.secret_key = os.environ.get("SECRET_KEY", "prisma_secret_key_ueecr_2025_segura!")

# La sesión dura 8 horas (turno escolar completo)
app.permanent_session_lifetime = timedelta(hours=8)


# ===================================================================
# MANEJADORES DE ERROR
# ===================================================================

@app.errorhandler(403)
def forbidden(e):
    """
    HTTP 403 — Acceso denegado por rol insuficiente.
    Muestra el error en la página de login como mensaje de aviso.
    """
    rol = session.get('rol', 'sin sesión')
    return render_template(
        'index.html',
        error=f"⚠ Acceso denegado: tu rol '{rol}' no tiene permiso para esa sección."
    ), 403


@app.errorhandler(404)
def not_found(e):
    return render_template('index.html', error="Página no encontrada."), 404


# ===================================================================
# RUTAS PÚBLICAS (sin autenticación requerida)
# ===================================================================

@app.route('/', methods=['GET'])
def inicio():
    """Página de login. Siempre muestra el formulario de acceso."""
    return render_template('index.html')

from login import login as login_func

@app.route('/login', methods=['POST'])
@login_required
def login():
    return login_func()
       
@app.route('/logout')
def logout():
    """Cierra la sesión activa y redirige al login."""
    session.clear()
    return redirect(url_for('inicio'))


# ===================================================================
# DASHBOARD PRINCIPAL — Menú dinámico por rol
# ===================================================================

@app.route('/menu')
@login_required
def menu():
    """
    Dashboard principal único (menu.html).
    Construye el menú dinámicamente según session['rol'].
    No hay menu_admin.html, menu_docente.html, etc.
    Todo se renderiza desde este único endpoint.
    """
    menu_items = get_menu_items(session['rol'])
    return render_template(
        'menu.html',
        menu_items     = menu_items,
        usuario_nombre = session.get('nombre', 'Usuario'),
        usuario_rol    = session.get('rol', ''),
        usuario_codigo = session.get('codigo', '')
    )


# ===================================================================
# MÓDULOS IMPLEMENTADOS
# ===================================================================

from regis_estudiante import registro_estudiantes as registrar_estudiantes_func

@app.route('/registro_estu', methods=['GET', 'POST'])
@login_required
def registro_estudiantes():
    return registrar_estudiantes_func()


from registrar_personal import personal as registrar_personal_func

@app.route('/personal', methods=['GET', 'POST'])
@login_required
def personal():
    return registrar_personal_func()


from buscar_estu import buscar_estu as buscar_estu_func

@app.route('/buscar_estu', methods=['GET', 'POST'])
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def ruta_buscar_estu():
    return buscar_estu_func()

from gestion_usuarios import gestion_usuarios as gestion_usuarios_func

@app.route('/usuarios', methods=['GET', 'POST'])
@login_required
@rol_required('admin')
def usuarios():
    return gestion_usuarios_func()



@app.route('/matricula')
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def matricula():
    return _modulo_en_desarrollo("Proceso de Matrícula", "fa-file-signature")


@app.route('/secciones')
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def secciones():
    return _modulo_en_desarrollo("Secciones", "fa-layer-group")


@app.route('/anio_escolar')
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def anio_escolar():
    return _modulo_en_desarrollo("Año Escolar", "fa-calendar-alt")


@app.route('/representantes')
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def representantes():
    return _modulo_en_desarrollo("Representantes", "fa-people-roof")


@app.route('/evaluaciones')
@login_required
@rol_required('admin', 'director', 'coordinador', 'docente')
def evaluaciones():
    return _modulo_en_desarrollo("Evaluaciones y Notas", "fa-star-half-stroke")


@app.route('/boletines')
@login_required
@rol_required('admin', 'director', 'coordinador', 'docente')
def boletines():
    return _modulo_en_desarrollo("Boletines", "fa-newspaper")

from constancia_estudio import constancia_estudio as constancia_estudio_func

@app.route('/constancias', methods=['GET', 'POST'])
@login_required
@rol_required('admin', 'secretaria')
def constancias():
    return constancia_estudio_func()


@app.route('/citaciones')
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def citaciones():
    return _modulo_en_desarrollo("Citaciones", "fa-bell")


@app.route('/labor_social')
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria', 'docente')
def labor_social():
    return _modulo_en_desarrollo("Labor Social", "fa-hands-holding-child")


@app.route('/materias')
@login_required
@rol_required('admin', 'director', 'coordinador', 'docente')
def materias():
    return _modulo_en_desarrollo("Materias", "fa-book-open")


@app.route('/asignacion_docente')
@login_required
@rol_required('admin', 'director', 'coordinador', 'docente')
def asignacion_docente():
    return _modulo_en_desarrollo("Asignación Docente", "fa-chalkboard-user")


@app.route('/reportes')
@login_required
def reportes():
    return _modulo_en_desarrollo("Reportes", "fa-chart-bar")


def _modulo_en_desarrollo(nombre: str, icono: str) -> str:
    """ Renderiza la plantilla de modulos en desarrollo """
    return render_template('en_desarrollo.html', nombre=nombre, icono=icono)

# ===================================================================
# PUNTO DE ENTRADA
# ===================================================================

if __name__ == '__main__':
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=puerto, debug=True)
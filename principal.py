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

# Módulo Académico
from modulos.evaluacion.registro_notas        import registro_notas_view
from modulos.evaluacion.boletines_mod         import boletines_view, boletin_ver_view
from modulos.evaluacion.momentos_evaluativos  import momentos_view
from modulos.evaluacion.notas_certificadas_mod import notas_certificadas_view, nota_certificada_ver_view, descargar_nota_xls_view
from modulos.evaluacion.carga_masiva_notas    import carga_masiva_notas_view
from modulos.academico.materias_mod          import materias_view
from modulos.academico.asignacion_docente_view import asignacion_docente_view as asignacion_docente_view_func

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

# Instalar interceptores de logs para el módulo Terminal Admin
from modulos.admin.admin_terminal import instalar_interceptores, vista_terminal, sse_stream
instalar_interceptores()


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

@app.route('/descargar_nota_xls')
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def descargar_nota_xls():
    return descargar_nota_xls_view()


# ===================================================================
# MÓDULOS IMPLEMENTADOS
# ===================================================================

from modulos.estudiantes.regis_estudiante import registro_estudiantes as registrar_estudiantes_func, descargar_plantilla_estudiantes_view, cargar_estudiantes_masivo_view

@app.route('/registro_estu', methods=['GET', 'POST'])
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def registro_estudiantes():
    return registrar_estudiantes_func()

@app.route('/descargar_plantilla_estudiantes', methods=['GET'])
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def descargar_plantilla_estudiantes():
    return descargar_plantilla_estudiantes_view()

@app.route('/cargar_estudiantes_masivo', methods=['POST'])
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def cargar_estudiantes_masivo():
    return cargar_estudiantes_masivo_view()
from modulos.personal.registrar_personal import personal as registrar_personal_func

@app.route('/personal', methods=['GET', 'POST'])
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def personal():
    return registrar_personal_func()


from modulos.estudiantes.buscar_estu import buscar_estu as buscar_estu_func

@app.route('/buscar_estu', methods=['GET', 'POST'])
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def ruta_buscar_estu():
    return buscar_estu_func()

from modulos.admin.gestion_usuarios import gestion_usuarios as gestion_usuarios_func

@app.route('/usuarios', methods=['GET', 'POST'])
@login_required
@rol_required('admin')
def usuarios():
    return gestion_usuarios_func()


from modulos.academico.matricula import matricula_view, matricula_automatica_view

@app.route('/matricula', methods=['GET', 'POST'])
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def proceso_matricula():
    return matricula_view()

@app.route('/matricula_automatica', methods=['POST'])
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def matricula_automatica():
    return matricula_automatica_view()


from modulos.academico.configuracion_ano import configuracion_ano_view

@app.route('/configuracion_ano', methods=['GET', 'POST'])
@login_required
@rol_required('admin', 'director')
def configuracion_ano():
    return configuracion_ano_view()


from modulos.academico.secciones import secciones_view

@app.route('/secciones')
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def secciones():
    return secciones_view()

from modulos.academico.ano_escolar import ano_escolar_view as ano_escolar_view_func, activar_ano_logic

@app.route('/anio_escolar', methods=['GET', 'POST'])
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def anio_escolar():
    return ano_escolar_view_func()

@app.route('/activar_ano/<codigo_ano>', methods=['POST'])
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def activar_ano(codigo_ano):
    return activar_ano_logic(codigo_ano)

from modulos.academico.promocion_automatica import promover_ano

@app.route('/ejecutar_promocion', methods=['POST'])
@login_required
@rol_required('admin', 'director')
def ejecutar_promocion():
    resultado = promover_ano()
    flash("Promoción Automática ejecutada. Revisa los periodos para verificar el nuevo año activo.", "success")
    return redirect(url_for('anio_escolar'))


@app.route('/representantes')
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def representantes():
    return _modulo_en_desarrollo("Representantes", "fa-people-roof")

# ===================================================================
# MÓDULO DE ACTIVOS (INVENTARIO DE BIENES DE LA INSTITUCIÓN)
# ===================================================================


from modulos.admin.gestion_activos import activos_institucion as activos_institucion_func
# Nota: Ajusta el "from" según el nombre que le diste al archivo del Paso 1

@app.route('/activos', methods=['GET', 'POST'])
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def activos():
    """
    Endpoint único para el Sistema de Control de Activos de la institución.
    """
    return activos_institucion_func()

@app.route('/registro_notas', methods=['GET', 'POST'])
@login_required
@rol_required('admin', 'director', 'coordinador', 'docente')
def registro_notas():
    """Módulo de registro de calificaciones por momento."""
    return registro_notas_view()


@app.route('/carga_masiva_notas', methods=['GET', 'POST'])
@login_required
@rol_required('admin', 'director', 'coordinador', 'docente')
def carga_masiva_notas():
    """Carga masiva de notas mediante archivo Excel."""
    return carga_masiva_notas_view()


@app.route('/evaluaciones', methods=['GET', 'POST'])
@login_required
@rol_required('admin', 'director', 'coordinador', 'docente')
def evaluaciones():
    """Alias de compatibilidad hacia registro_notas."""
    return redirect(url_for('registro_notas'))


@app.route('/boletines', methods=['GET', 'POST'])
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria', 'docente')
def boletines():
    """Listado y generación de boletines de calificaciones."""
    return boletines_view()


@app.route('/boletin/<int:boletin_id>')
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria', 'docente')
def boletin_ver(boletin_id):
    """Vista imprimible de un boletin individual."""
    return boletin_ver_view(boletin_id)


@app.route('/momentos', methods=['GET', 'POST'])
@login_required
@rol_required('admin', 'director')
def momentos():
    """Gestión de momentos evaluativos (lapsos)."""
    return momentos_view()


@app.route('/notas_certificadas', methods=['GET', 'POST'])
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def notas_certificadas():
    """Historial académico y emisión de notas certificadas."""
    return notas_certificadas_view()


@app.route('/nota_certificada_ver')
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def nota_certificada_ver():
    """Vista imprimible del certificado de notas."""
    return nota_certificada_ver_view()

from modulos.documentos.constancia_estudio import constancia_estudio as constancia_estudio_func, descargar_formato

@app.route('/constancias', methods=['GET', 'POST'])
@login_required
@rol_required('admin', 'secretaria','director')
def constancias():
    return constancia_estudio_func()

@app.route('/descargar_formato/<path:nombre_archivo>')
@login_required
@rol_required('admin', 'secretaria','director')
def ruta_descargar_formato(nombre_archivo):
    return descargar_formato(nombre_archivo)


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


@app.route('/materias', methods=['GET', 'POST'])
@login_required
@rol_required('admin', 'director', 'coordinador', 'docente')
def materias():
    """CRUD de materias/asignaturas del plan de estudios."""
    return materias_view()


@app.route('/asignacion_docente', methods=['GET', 'POST'])
@login_required
@rol_required('admin', 'director', 'coordinador', 'docente')
def asignacion_docente():
    """Gestión de asignaciones docente-materia-sección."""
    return asignacion_docente_view_func()


# ===================================================================
# MÓDULO DE REPORTES (CONEXIÓN ACTIVA A SUPABASE)
# ===================================================================
from modulos.reportes.reportes import reportes as reportes_func

@app.route('/reportes', methods=['GET', 'POST'])
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def reportes():
    return reportes_func()

def _modulo_en_desarrollo(nombre: str, icono: str) -> str:
    """ Renderiza la plantilla de modulos en desarrollo """
    return render_template('en_desarrollo.html', nombre=nombre, icono=icono)


# ===================================================================
# MÓDULO TERMINAL ADMIN (solo admin)
# ===================================================================

@app.route('/admin/terminal')
@login_required
@rol_required('admin')
def admin_terminal():
    """Terminal de logs del servidor en tiempo real."""
    return vista_terminal()

@app.route('/admin/terminal/stream')
@login_required
@rol_required('admin')
def admin_terminal_stream():
    """Endpoint SSE que transmite logs en vivo."""
    return sse_stream()

# ===================================================================
# PUNTO DE ENTRADA
# ===================================================================

if __name__ == '__main__':
    puerto = int(os.environ.get("PORT", 5000))
    print(f"\n Link para entrar: http://127.0.0.1:{puerto}\n")
    app.run(host="0.0.0.0", port=puerto, debug=True, threaded=True)

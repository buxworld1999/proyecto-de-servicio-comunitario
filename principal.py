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
from modulos.admin.bitacora import bitacora_view, registrar_accion

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
# BITÁCORA — Hook automático: registra toda actividad relevante
# ===================================================================

@app.after_request
def log_actividad(response):
    """
    Se ejecuta después de CADA request.
    Registra en Supabase las acciones importantes de los usuarios.
    """
    try:
        ruta = request.path
        metodo = request.method
        codigo = response.status_code
        # Solo registrar si hay sesión activa (no login page)
        if 'usuario_id' in session:
            registrar_accion(ruta, metodo, codigo)
    except Exception:
        pass  # Nunca interrumpir el flujo por un error de bitácora
    return response


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

    # ── Estadísticas del dashboard ─────────────────────────────────────────
    stats = {}
    try:
        # Total estudiantes registrados
        r = supabase.table('estudiante').select('cedula').execute()
        estudiantes_data = r.data or []
        todas_cedulas = set(e['cedula'] for e in estudiantes_data)
        stats['total_estudiantes'] = len(todas_cedulas)

        # Año escolar activo
        r_ano = supabase.table('ano_escolar').select('codigo').eq('activo', True).limit(1).execute()
        ano_activo = r_ano.data[0]['codigo'] if r_ano.data else None
        stats['ano_activo'] = ano_activo or '—'

        if ano_activo:
            # Matriculados en el año activo
            r_mat = supabase.table('matricula').select('cedula_estudiante, estado_matricula').eq('codigo_ano_escolar', ano_activo).execute()
            matriculas_data = r_mat.data or []
            
            cedulas_matriculadas = set(m['cedula_estudiante'] for m in matriculas_data)
            cedulas_activas = set(m['cedula_estudiante'] for m in matriculas_data if m.get('estado_matricula') == 'A')
            
            # Intersección para evitar contar matrículas huérfanas o duplicadas
            valid_matriculados = todas_cedulas.intersection(cedulas_matriculadas)
            valid_activos = todas_cedulas.intersection(cedulas_activas)

            stats['matriculados'] = len(valid_matriculados)
            stats['activos'] = len(valid_activos)

            # Estudiantes sin matrícula este año
            stats['sin_matricula'] = stats['total_estudiantes'] - stats['matriculados']
        else:
            stats['matriculados'] = 0
            stats['activos'] = 0
            stats['sin_matricula'] = stats['total_estudiantes']

        # Total personal
        r_per = supabase.table('personal').select('cedula', count='exact').execute()
        stats['total_personal'] = r_per.count or 0

        # Total docentes asignados este año
        if ano_activo:
            r_doc = supabase.table('asignacion_docente').select('id', count='exact').eq('codigo_ano_escolar', ano_activo).execute()
            stats['docentes_asignados'] = r_doc.count or 0
        else:
            stats['docentes_asignados'] = 0

        # Secciones activas
        r_sec = supabase.table('seccion').select('codigo', count='exact').execute()
        stats['total_secciones'] = r_sec.count or 0

        # Boletines generados este año
        if ano_activo:
            r_bol = supabase.table('boletin').select('id', count='exact').eq('codigo_ano_escolar', ano_activo).execute()
            stats['boletines'] = r_bol.count or 0
        else:
            stats['boletines'] = 0

    except Exception as e:
        print(f"[MENU] Error cargando estadísticas: {e}")
        stats = {
            'total_estudiantes': '—', 'matriculados': '—', 'activos': '—',
            'sin_matricula': '—', 'total_personal': '—', 'docentes_asignados': '—',
            'total_secciones': '—', 'boletines': '—', 'ano_activo': '—'
        }
    # ──────────────────────────────────────────────────────────────────────────

    # ── Actividad Reciente (solo si es admin) ──────────────────────────────────
    actividad_reciente = []
    if session.get('rol') == 'admin':
        try:
            from datetime import datetime, timezone, timedelta
            r_act = supabase.table('bitacora').select(
                'usuario_nombre, usuario_rol, accion, icono, categoria, fecha_hora'
            ).order('fecha_hora', desc=True).limit(8).execute()

            ahora = datetime.now(timezone.utc)
            for item in (r_act.data or []):
                fh = item.get('fecha_hora', '')
                try:
                    dt = datetime.fromisoformat(fh.replace('Z', '+00:00'))
                    diff = ahora - dt
                    mins = int(diff.total_seconds() / 60)
                    if mins < 1:
                        item['hace'] = 'ahora mismo'
                    elif mins < 60:
                        item['hace'] = f'{mins} min atrás'
                    elif mins < 1440:
                        item['hace'] = f'{mins // 60}h atrás'
                    else:
                        item['hace'] = f'{mins // 1440}d atrás'
                except Exception:
                    item['hace'] = '—'
                actividad_reciente.append(item)
        except Exception as e:
            print(f"[MENU] Error cargando actividad: {e}")
    # ──────────────────────────────────────────────────────────────────────────

    return render_template(
        'menu.html',
        menu_items          = menu_items,
        usuario_nombre      = session.get('nombre', 'Usuario'),
        usuario_rol         = session.get('rol', ''),
        usuario_codigo      = session.get('codigo', ''),
        stats               = stats,
        actividad_reciente  = actividad_reciente
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

from modulos.estudiantes.directorio_estudiantil import directorio_estudiantil_view
from modulos.estudiantes.regis_estudiante import editar_estudiante_view

@app.route('/directorio_estudiantil', methods=['GET'])
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def directorio_estudiantil():
    return directorio_estudiantil_view()

@app.route('/editar_estu/<cedula>', methods=['GET', 'POST'])
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def editar_estu(cedula):
    return editar_estudiante_view(cedula)
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
@rol_required('admin', 'director')
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

from modulos.academico.registrar_representantes import representantes_view

@app.route('/representantes', methods=['GET', 'POST'])
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def representantes():
    return representantes_view()

from modulos.academico.registrar_representantes import buscar_representante_api

@app.route('/api/consultar_representante/<cedula>', methods=['GET'])
@login_required
def consultar_representante(cedula):
    return buscar_representante_api(cedula)


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
# MÓDULO BITÁCORA (solo admin)
# ===================================================================

@app.route('/bitacora')
@login_required
@rol_required('admin')
def bitacora():
    """Bitácora de actividad del sistema — solo administradores."""
    return bitacora_view()


# ===================================================================
# PUNTO DE ENTRADA
# ===================================================================

if __name__ == '__main__':
    puerto = int(os.environ.get("PORT", 5000))
    print(f"\n Link para entrar: http://127.0.0.1:{puerto}\n")
    app.run(host="0.0.0.0", port=puerto, debug=True, threaded=True)

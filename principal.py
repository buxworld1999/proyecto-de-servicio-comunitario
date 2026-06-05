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

# Instalar interceptores de logs para el módulo Terminal Admin
from admin_terminal import instalar_interceptores, vista_terminal, sse_stream
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


# ===================================================================
# MÓDULOS IMPLEMENTADOS
# ===================================================================

from regis_estudiante import registro_estudiantes as registrar_estudiantes_func

@app.route('/registro_estu', methods=['GET', 'POST'])
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def registro_estudiantes():
    return registrar_estudiantes_func()


from registrar_personal import personal as registrar_personal_func

@app.route('/personal', methods=['GET', 'POST'])
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
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


from matricula import matricula_view

@app.route('/matricula', methods=['GET', 'POST'])
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def proceso_matricula():
    return matricula_view()


from configuracion_ano import configuracion_ano_view

@app.route('/configuracion_ano', methods=['GET', 'POST'])
@login_required
@rol_required('admin', 'director')
def configuracion_ano():
    return configuracion_ano_view()


from secciones import secciones_view

@app.route('/secciones')
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def secciones():
    return secciones_view()


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

# ===================================================================
# MÓDULO DE ACTIVOS (INVENTARIO DE BIENES DE LA INSTITUCIÓN)
# ===================================================================


from gestion_activos import activos_institucion as activos_institucion_func
# Nota: Ajusta el "from" según el nombre que le diste al archivo del Paso 1

@app.route('/activos', methods=['GET', 'POST'])
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def activos():
    """
    Endpoint único para el Sistema de Control de Activos de la institución.
    """
    return activos_institucion_func()

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

from constancia_estudio import constancia_estudio as constancia_estudio_func, descargar_formato

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


@app.route('/materias')
@login_required
@rol_required('admin', 'director', 'coordinador', 'docente')
def materias():
    return render_template('materias.html')


@app.route('/asignacion_docente')
@login_required
@rol_required('admin', 'director', 'coordinador', 'docente')
def asignacion_docente():
    return _modulo_en_desarrollo("Asignación Docente", "fa-chalkboard-user")


# ===================================================================
# MÓDULO DE REPORTES (CONEXIÓN ACTIVA A SUPABASE)
# ===================================================================

@app.route('/reportes', methods=['GET', 'POST'])
@login_required
@rol_required('admin', 'director', 'coordinador', 'secretaria')
def reportes():
    """
    Controlador para el módulo de reportes.
    Consulta directamente las tablas de Supabase según el formulario enviado.
    """
    # Inicializamos variables para mandar a la plantilla en caso de consulta exitosa
    resultados = None
    tipo_reporte = None

    if request.method == 'POST':
        # Identificamos qué formulario se envió por medio de un campo oculto o el botón presionado
        accion = request.form.get('accion')

        try:
            # --- CASO 1: REPORTE DE MATRÍCULA ---
            if accion == 'matricula':
                grado_seleccionado = request.form.get('grado')
                
                # Construimos la consulta base a la tabla estudiante
                query = supabase.table("estudiante").select("cedula, nacionalidad, nombres, apellidos, genero, estado_estudiante")
                
                # Si el usuario seleccionó un grado específico (asumiendo que manejas el campo o filtro similar)
                # NOTA: Si en tu tabla 'estudiante' guardas el grado o año, puedes aplicar el filtro aquí:
                # if grado_seleccionado != 'todos':
                #     query = query.eq("grado", grado_seleccionado)
                
                response = query.execute()
                resultados = response.data
                tipo_reporte = 'matricula'
                
                if not resultados:
                    flash("No se encontraron estudiantes registrados para los filtros seleccionados.", "warning")

            # --- CASO 2: CONSTANCIAS DE ESTUDIO ---
            elif accion == 'constancia':
                v_cedula = request.form.get('cedula_buscar', '').strip()
                v_motivo = request.form.get('motivo', '').strip() or "Trámite General"

                # Buscamos al estudiante por su cédula
                response = supabase.table("estudiante") \
                    .select("cedula, nacionalidad, nombres, apellidos, estado_estudiante") \
                    .eq("cedula", v_cedula) \
                    .execute()

                if response.data:
                    estudiante = response.data[0]
                    # Validar si está activo
                    if estudiante.get('estado_estudiante') == 'A':
                        # Pasamos los datos del estudiante directo a una plantilla de constancia limpia
                        return render_template(
                            'constancia_imprimible.html',
                            estudiante=estudiante,
                            motivo=v_motivo,
                            fecha_hoy=os.popen('date +"%d-%m-%Y"').read().strip() # Fecha del sistema
                        )
                    else:
                        flash("El estudiante se encuentra Inactivo (Retirado). No se puede emitir la constancia.", "danger")
                else:
                    flash(f"No se encontró ningún estudiante con la cédula '{v_cedula}'.", "danger")

        except Exception as e:
            flash(f"Error en la base de datos al generar reporte: {str(e)}", "danger")

    # Si es GET o si fue un POST que no redirigió, muestra el panel con los resultados (si existen)
    return render_template(
        'reportes.html', 
        usuario_nombre=session.get('nombre', 'Usuario'),
        usuario_rol=session.get('rol', ''),
        resultados=resultados,
        tipo_reporte=tipo_reporte
    )


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
    app.run(host="0.0.0.0", port=puerto, debug=True)
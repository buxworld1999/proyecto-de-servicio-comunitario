"""
auth.py — Módulo Central de Autenticación y Control de Acceso por Roles (RBAC)
PRISMA — Sistema de Gestión Escolar | Unidad Educativa Carmen Ruíz

Arquitectura:
    - 10 roles institucionales (admin + 9 roles reales)
    - Permisos granulares por acción: ver, crear, editar, eliminar,
      imprimir, exportar, registrar_notas, modificar_notas, certificar
    - Menú dinámico filtrado automáticamente por rol
    - Decoradores: @login_required, @rol_required, @permiso_required
    - Función puede(modulo, accion) usable en código Python y plantillas Jinja2
"""

from functools import wraps
from flask import session, redirect, url_for, abort, g


# ============================================================
# CATÁLOGO DE ROLES VÁLIDOS DEL SISTEMA
# ============================================================

ROLES_VALIDOS = {
    'admin',
    'director',
    'subdirector_academico',
    'secretaria_direccion',
    'coordinador_evaluacion',
    'coordinador_registro',
    'secretaria_registro',
    'coordinador_seccional',
    'secretaria_seccional',
    'docente',
}

# Etiquetas legibles para mostrar en la interfaz
ROLES_ETIQUETAS = {
    'admin':                  'Administrador',
    'director':               'Director',
    'subdirector_academico':  'Subdirector Académico',
    'secretaria_direccion':   'Secretaria de Dirección',
    'coordinador_evaluacion': 'Coordinador de Evaluación',
    'coordinador_registro':   'Coordinador de Registro y Control',
    'secretaria_registro':    'Secretaria de Registro y Control',
    'coordinador_seccional':  'Coordinador Seccional',
    'secretaria_seccional':   'Secretaria Seccional',
    'docente':                'Docente',
}


# ============================================================
# MATRIZ DE PERMISOS GRANULARES
#
# Estructura: PERMISOS[rol][modulo] = set de acciones permitidas
#
# Acciones disponibles:
#   ver              → Puede visualizar el módulo y su información
#   crear            → Puede crear/registrar nuevos registros
#   editar           → Puede editar registros existentes
#   eliminar         → Puede eliminar registros
#   imprimir         → Puede imprimir documentos
#   exportar         → Puede exportar datos (Excel, PDF)
#   registrar_notas  → Puede cargar notas nuevas
#   modificar_notas  → Puede cambiar una nota ya registrada
#   certificar       → Puede emitir documentos certificados
# ============================================================

PERMISOS = {

    # ─── ADMINISTRADOR — Acceso total ────────────────────────────────────────
    'admin': {
        'usuarios':               {'ver', 'crear', 'editar', 'eliminar'},
        'personal':               {'ver', 'crear', 'editar', 'eliminar', 'exportar'},
        'estudiantes':            {'ver', 'crear', 'editar', 'eliminar', 'exportar', 'imprimir'},
        'matricula':              {'ver', 'crear', 'editar', 'eliminar'},
        'evaluaciones':           {'ver', 'crear', 'editar', 'eliminar', 'registrar_notas', 'modificar_notas', 'exportar'},
        'momentos':               {'ver', 'crear', 'editar', 'eliminar'},
        'notas_certificadas':     {'ver', 'crear', 'imprimir', 'exportar', 'certificar'},
        'constancias':            {'ver', 'crear', 'imprimir', 'exportar'},
        'materias':               {'ver', 'crear', 'editar', 'eliminar'},
        'asignacion_docente':     {'ver', 'crear', 'editar', 'eliminar'},
        'reportes':               {'ver', 'crear', 'exportar'},
        'activos':                {'ver', 'crear', 'editar', 'eliminar'},
        'terminal':               {'ver'},
        'bitacora':               {'ver', 'exportar'},
        'representantes':         {'ver', 'crear', 'editar', 'eliminar'},
    },

    # ─── DIRECTOR — Solo lectura global ──────────────────────────────────────
    'director': {
        'personal':               {'ver'},
        'estudiantes':            {'ver', 'imprimir'},
        'matricula':              {'ver'},
        'evaluaciones':           {'ver'},
        'notas_certificadas':     {'ver', 'imprimir'},
        'constancias':            {'ver'},
        'materias':               {'ver'},
        'asignacion_docente':     {'ver'},
        'reportes':               {'ver', 'exportar'},
        'activos':                {'ver'},
        'bitacora':               {'ver'},
    },

    # ─── SUBDIRECTOR ACADÉMICO — Solo lectura global ──────────────────────────
    'subdirector_academico': {
        'personal':               {'ver'},
        'estudiantes':            {'ver'},
        'matricula':              {'ver'},
        'evaluaciones':           {'ver'},
        'notas_certificadas':     {'ver'},
        'materias':               {'ver'},
        'asignacion_docente':     {'ver'},
        'reportes':               {'ver', 'exportar'},
    },

    # ─── SECRETARIA DE DIRECCIÓN — Consulta administrativa ───────────────────
    'secretaria_direccion': {
        'personal':               {'ver', 'exportar'},
        'estudiantes':            {'ver', 'crear', 'editar', 'imprimir', 'exportar'},
        'matricula':              {'ver'},
        'evaluaciones':           {'ver'},          # Solo lectura en notas
        'notas_certificadas':     {'ver', 'imprimir'},
        'constancias':            {'ver', 'crear', 'imprimir'},
        'reportes':               {'ver', 'exportar'},
        'activos':                {'ver'},
        'representantes':         {'ver'},
    },

    # ─── COORDINADOR DE EVALUACIÓN — Control total sobre calificaciones ───────
    'coordinador_evaluacion': {
        'evaluaciones':           {'ver', 'crear', 'editar', 'registrar_notas', 'modificar_notas', 'exportar'},
        'momentos':               {'ver', 'crear', 'editar'},
        'notas_certificadas':     {'ver'},
        'materias':               {'ver', 'crear', 'editar'},
        'asignacion_docente':     {'ver', 'crear', 'editar'},
        'reportes':               {'ver', 'exportar'},
        'estudiantes':            {'ver'},
    },

    # ─── COORDINADOR DE REGISTRO Y CONTROL — Administración académica/documental
    'coordinador_registro': {
        'estudiantes':            {'ver', 'crear', 'editar', 'imprimir', 'exportar'},
        'matricula':              {'ver', 'crear', 'editar'},
        'representantes':         {'ver', 'crear', 'editar'},
        'notas_certificadas':     {'ver', 'crear', 'imprimir', 'exportar', 'certificar'},
        'constancias':            {'ver', 'crear', 'imprimir'},
        'evaluaciones':           {'ver', 'registrar_notas'},  # Puede registrar, NO modificar
        'materias':               {'ver', 'editar'},
        'asignacion_docente':     {'ver'},
        'reportes':               {'ver', 'exportar'},
    },

    # ─── SECRETARIA DE REGISTRO Y CONTROL — Gestión operativa de estudiantes ─
    'secretaria_registro': {
        'estudiantes':            {'ver', 'crear', 'editar', 'imprimir', 'exportar'},
        'matricula':              {'ver', 'crear', 'editar'},
        'representantes':         {'ver', 'crear', 'editar'},
        'notas_certificadas':     {'ver', 'crear', 'imprimir', 'certificar'},
        'constancias':            {'ver', 'crear', 'imprimir'},
        'evaluaciones':           {'ver', 'registrar_notas'},  # Puede registrar, NO modificar
    },

    # ─── COORDINADOR SECCIONAL — Consulta académica y seguimiento ────────────
    'coordinador_seccional': {
        'estudiantes':            {'ver'},
        'matricula':              {'ver'},
        'evaluaciones':           {'ver'},
        'notas_certificadas':     {'ver'},
    },

    # ─── SECRETARIA SECCIONAL — Matrícula exclusiva ───────────────────────────
    'secretaria_seccional': {
        'estudiantes':            {'ver', 'crear'},
        'matricula':              {'ver', 'crear'},
        'representantes':         {'ver', 'crear'},
    },

    # ─── DOCENTE — Solo sus notas asignadas ───────────────────────────────────
    # El docente SOLO puede registrar notas de las secciones/materias
    # a las que está asignado. La lógica de filtro está en registro_notas.py.
    'docente': {
        'evaluaciones':           {'ver', 'registrar_notas'},
    },
}


# ============================================================
# FUNCIÓN CENTRAL DE VERIFICACIÓN DE PERMISOS
# ============================================================

def puede(modulo: str, accion: str) -> bool:
    """
    Verifica si el usuario en sesión tiene permiso para realizar
    una acción específica sobre un módulo.

    Esta función es usable tanto en código Python como en plantillas Jinja2
    (se registra como global en principal.py con:
        app.jinja_env.globals['puede'] = puede)

    Args:
        modulo: Clave del módulo (ej: 'evaluaciones', 'matricula')
        accion: Acción a verificar (ej: 'ver', 'registrar_notas', 'modificar_notas')

    Returns:
        True si tiene permiso, False si no.

    Uso en Python:
        from auth import puede
        if not puede('evaluaciones', 'modificar_notas'):
            abort(403)

    Uso en Jinja2:
        {% if puede('matricula', 'crear') %}
            <button>Nueva Matrícula</button>
        {% endif %}
    """
    rol = session.get('rol', '')
    if not rol or rol not in ROLES_VALIDOS:
        return False
    permisos_rol = PERMISOS.get(rol, {})
    acciones_modulo = permisos_rol.get(modulo, set())
    return accion in acciones_modulo


def tiene_acceso_modulo(modulo: str) -> bool:
    """
    Verifica si el rol en sesión tiene al menos la acción 'ver' en un módulo.
    Útil para lógica condicional de visualización.

    Args:
        modulo: Clave del módulo (ej: 'reportes', 'matricula')

    Returns:
        True si tiene al menos permiso de ver, False si no.
    """
    return puede(modulo, 'ver')


# ============================================================
# ÍTEMS POR MÓDULO
# Define label, URL, ícono (FontAwesome) y acción requerida de cada sub-página.
# Si no se especifica 'accion', por defecto requiere 'ver'.
# ============================================================

MODULOS_ITEMS = {
    'usuarios': [
        {
            'label': 'Gestión de Usuarios',
            'url':   '/usuarios',
            'icono': 'fa-solid fa-users-gear',
            'accion': 'ver'
        },
    ],
    'personal': [
        {
            'label': 'Registro de Personal',
            'url':   '/personal',
            'icono': 'fa-solid fa-id-badge',
            'accion': 'ver'
        },
    ],
    'estudiantes': [
        {
            'label': 'Registro Estudiantil',
            'url':   '/registro_estu',
            'icono': 'fa-solid fa-user-graduate',
            'accion': 'crear'  # Requiere permiso de creación
        },
        {
            'label': 'Buscar Estudiante',
            'url':   '/buscar_estu',
            'icono': 'fa-solid fa-magnifying-glass',
            'accion': 'ver'
        },
        {
            'label': 'Directorio Estudiantil',
            'url':   '/directorio_estudiantil',
            'icono': 'fa-solid fa-address-book',
            'accion': 'ver'
        },
    ],
    'matricula': [
        {
            'label': 'Proceso de Matrícula',
            'url':   '/matricula',
            'icono': 'fa-solid fa-file-signature',
            'accion': 'ver'
        },
        {
            'label': 'Secciones',
            'url':   '/secciones',
            'icono': 'fa-solid fa-layer-group',
            'accion': 'editar'  # Configuración, requiere editar
        },
        {
            'label': 'Año Escolar',
            'url':   '/anio_escolar',
            'icono': 'fa-solid fa-calendar-alt',
            'accion': 'eliminar'  # Solo admin (eliminar en matrícula)
        },
        {
            'label': 'Representantes',
            'url':   '/representantes',
            'icono': 'fa-solid fa-people-roof',
            'accion': 'ver'
        },
    ],
    'evaluaciones': [
        {
            'label': 'Registro de Notas',
            'url':   '/registro_notas',
            'icono': 'fa-solid fa-star-half-stroke',
            'accion': 'registrar_notas'  # Requiere registrar notas
        },
        {
            'label': 'Carga Masiva de Notas',
            'url':   '/carga_masiva_notas',
            'icono': 'fa-solid fa-file-excel',
            'accion': 'modificar_notas'  # Solo admin y coord_eval
        },
        {
            'label': 'Boletines',
            'url':   '/boletines',
            'icono': 'fa-solid fa-newspaper',
            'accion': 'ver'  # Requiere ver en evaluaciones
        },
    ],
    'momentos': [
        {
            'label': 'Momentos Evaluativos',
            'url':   '/momentos',
            'icono': 'fa-solid fa-calendar-check',
            'accion': 'ver'
        },
    ],
    'notas_certificadas': [
        {
            'label': 'Notas Certificadas',
            'url':   '/notas_certificadas',
            'icono': 'fa-solid fa-certificate',
            'accion': 'ver'
        },
    ],
    'constancias': [
        {
            'label': 'Constancias',
            'url':   '/constancias',
            'icono': 'fa-solid fa-file-circle-check',
            'accion': 'ver'
        },
    ],
    'materias': [
        {
            'label': 'Materias',
            'url':   '/materias',
            'icono': 'fa-solid fa-book-open',
            'accion': 'ver'
        },
    ],
    'asignacion_docente': [
        {
            'label': 'Asignación Docente',
            'url':   '/asignacion_docente',
            'icono': 'fa-solid fa-chalkboard-user',
            'accion': 'ver'
        },
    ],
    'reportes': [
        {
            'label': 'Reportes',
            'url':   '/reportes',
            'icono': 'fa-solid fa-chart-bar',
            'accion': 'ver'
        },
    ],
    'activos': [
        {
            'label': 'Control de Activos',
            'url':   '/activos',
            'icono': 'fa-solid fa-boxes-stacked',
            'accion': 'ver'
        },
    ],
    'terminal': [
        {
            'label': 'Terminal del Sistema',
            'url':   '/admin/terminal',
            'icono': 'fa-solid fa-terminal',
            'accion': 'ver'
        },
    ],
    'bitacora': [
        {
            'label': 'Bitácora de Actividad',
            'url':   '/bitacora',
            'icono': 'fa-solid fa-shield-halved',
            'accion': 'ver'
        },
    ],
    'representantes': [
        {
            'label': 'Representantes',
            'url':   '/representantes',
            'icono': 'fa-solid fa-people-roof',
            'accion': 'ver'
        },
    ],
}


# ============================================================
# GRUPOS VISUALES DEL MENÚ
# Controla el orden y agrupación visual del sidebar.
# ============================================================

MENU_GRUPOS = [
    {'titulo': 'Administración',       'modulos': ['usuarios']},
    {'titulo': 'Personal',             'modulos': ['personal']},
    {'titulo': 'Estudiantes',          'modulos': ['estudiantes']},
    {'titulo': 'Matrícula',            'modulos': ['matricula']},
    {'titulo': 'Evaluaciones',         'modulos': ['evaluaciones', 'momentos', 'notas_certificadas']},
    {'titulo': 'Documentos',           'modulos': ['constancias']},
    {'titulo': 'Académico',            'modulos': ['materias', 'asignacion_docente']},
    {'titulo': 'Bienes e Inventario',  'modulos': ['activos']},
    {'titulo': 'Reportes',             'modulos': ['reportes']},
    {'titulo': 'Sistema',              'modulos': ['terminal', 'bitacora']},
]


# ============================================================
# CONSTRUCTOR DEL MENÚ DINÁMICO
# ============================================================

def get_menu_items(rol: str) -> list:
    """
    Construye la lista de grupos del menú para el rol indicado.
    Solo incluye grupos que tengan al menos un módulo con permiso 'ver'.

    Los ítems individuales se filtran según la acción requerida.

    Args:
        rol: El rol del usuario autenticado.

    Returns:
        Lista de grupos con sus ítems visibles.
    """
    permisos_rol = PERMISOS.get(rol, {})
    
    # Módulos donde el rol tiene al menos permiso de ver
    modulos_con_ver = {
        mod for mod, acciones in permisos_rol.items()
        if 'ver' in acciones
    }

    menu = []

    for grupo in MENU_GRUPOS:
        items_del_grupo = []

        for modulo in grupo['modulos']:
            if modulo not in modulos_con_ver:
                continue

            items_modulo = MODULOS_ITEMS.get(modulo, [])
            items_filtrados = []

            for item in items_modulo:
                accion_requerida = item.get('accion', 'ver')
                
                # Verificar si el rol tiene permiso específico para este ítem
                if puede(modulo, accion_requerida):
                    # Exclusión para docentes en Boletines y Carga Masiva
                    if rol == 'docente' and modulo == 'evaluaciones' and item['url'] != '/registro_notas':
                        continue
                    
                    items_filtrados.append(item)

            items_del_grupo.extend(items_filtrados)

        if items_del_grupo:
            menu.append({
                'titulo': grupo['titulo'],
                'items':  items_del_grupo
            })

    return menu


# ============================================================
# DECORADORES DE SEGURIDAD
# ============================================================

def login_required(f):
    """
    Protege una ruta requiriendo sesión activa.
    Si no hay sesión iniciada, redirige al login (/).

    Uso:
        @app.route('/menu')
        @login_required
        def menu():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('inicio'))
        return f(*args, **kwargs)
    return decorated_function


def rol_required(*roles):
    """
    Protege una ruta requiriendo uno de los roles especificados.
    - Sin sesión → redirige al login.
    - Rol no autorizado → HTTP 403.

    Uso:
        @app.route('/usuarios')
        @login_required
        @rol_required('admin')
        def usuarios():
            ...

        @app.route('/registro_notas')
        @login_required
        @rol_required('admin', 'coordinador_evaluacion', 'coordinador_registro',
                      'secretaria_registro', 'docente')
        def registro_notas():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'usuario_id' not in session:
                return redirect(url_for('inicio'))
            rol_actual = session.get('rol', '')
            if rol_actual not in roles:
                # Registrar intento de acceso denegado en bitácora
                try:
                    from modulos.admin.bitacora import registrar_acceso_denegado
                    registrar_acceso_denegado(rol_actual)
                except Exception:
                    pass
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def permiso_required(modulo: str, accion: str):
    """
    Decorador granular: protege una ruta verificando una acción específica.
    Complementa a @rol_required cuando se necesita control de acción.

    Uso:
        @app.route('/notas/editar')
        @login_required
        @permiso_required('evaluaciones', 'modificar_notas')
        def editar_nota():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'usuario_id' not in session:
                return redirect(url_for('inicio'))
            if not puede(modulo, accion):
                try:
                    from modulos.admin.bitacora import registrar_acceso_denegado
                    registrar_acceso_denegado(session.get('rol', ''))
                except Exception:
                    pass
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

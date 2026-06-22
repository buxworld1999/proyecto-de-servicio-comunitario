"""
auth.py — Módulo Central de Autenticación y Control de Acceso por Roles (RBAC)
PRISMA — Sistema de Gestión Escolar | Unidad Educativa Carmen Ruíz
"""

from functools import wraps
from flask import session, redirect, url_for, abort


# ============================================================
# MAPA DE PERMISOS POR ROL
# Cada rol tiene acceso exclusivo a una lista de módulos.
# Para agregar/quitar acceso a un rol, edita SOLO este dict.
# ============================================================

PERMISOS = {
    'admin': [
        'usuarios', 'personal', 'estudiantes', 'matricula',
        'evaluaciones', 'momentos', 'notas_certificadas',
        'constancias', 'citaciones', 'labor_social',
        'materias', 'asignacion_docente', 'reportes', 'configuracion', 'activos',
        'terminal', 'bitacora'
    ],
    'director': [
        'personal', 'estudiantes', 'matricula',
        'evaluaciones', 'momentos', 'notas_certificadas',
        'citaciones', 'labor_social',
        'materias', 'asignacion_docente', 'reportes', 'configuracion', 'activos', 'usuarios'
    ],
    'coordinador': [
        'personal', 'estudiantes', 'matricula',
        'evaluaciones', 'notas_certificadas',
        'citaciones', 'labor_social',
        'materias', 'asignacion_docente', 'reportes', 'activos'
    ],
    'secretaria': [
        'personal', 'estudiantes', 'matricula',
        'notas_certificadas', 'constancias', 'citaciones', 'reportes', 'activos'
    ],
    'docente': [
        'estudiantes', 'evaluaciones',
        'labor_social', 'materias', 'asignacion_docente'
    ],
}


# ============================================================
# ÍTEMS POR MÓDULO
# Define label, URL e ícono (FontAwesome) de cada sub-página.
# ============================================================

MODULOS_ITEMS = {
    'usuarios': [
        {
            'label': 'Gestión de Usuarios',
            'url':   '/usuarios',
            'icono': 'fa-solid fa-users-gear'
        },
    ],
    'personal': [
        {
            'label': 'Registro de Personal',
            'url':   '/personal',
            'icono': 'fa-solid fa-id-badge'
        },
    ],
    'estudiantes': [
        {
            'label': 'Registro Estudiantil',
            'url':   '/registro_estu',
            'icono': 'fa-solid fa-user-graduate'
        },
        {
            'label': 'Buscar Estudiante',
            'url':   '/buscar_estu',
            'icono': 'fa-solid fa-magnifying-glass'
        },
    ],
    'matricula': [
        {
            'label': 'Proceso de Matrícula',
            'url':   '/matricula',
            'icono': 'fa-solid fa-file-signature'
        },
        {
            'label': 'Secciones',
            'url':   '/secciones',
            'icono': 'fa-solid fa-layer-group'
        },
        {
            'label': 'Año Escolar',
            'url':   '/anio_escolar',
            'icono': 'fa-solid fa-calendar-alt'
        },
        {
            'label': 'Representantes',
            'url':   '/representantes',
            'icono': 'fa-solid fa-people-roof'
        },
    ],
    'evaluaciones': [
        {
            'label': 'Registro de Notas',
            'url':   '/registro_notas',
            'icono': 'fa-solid fa-star-half-stroke'
        },
        {
            'label': 'Carga Masiva de Notas',
            'url':   '/carga_masiva_notas',
            'icono': 'fa-solid fa-file-excel'
        },
        {
            'label': 'Boletines',
            'url':   '/boletines',
            'icono': 'fa-solid fa-newspaper'
        },
    ],
    'momentos': [
        {
            'label': 'Momentos Evaluativos',
            'url':   '/momentos',
            'icono': 'fa-solid fa-calendar-check'
        },
    ],
    'notas_certificadas': [
        {
            'label': 'Notas Certificadas',
            'url':   '/notas_certificadas',
            'icono': 'fa-solid fa-certificate'
        },
    ],
    'constancias': [
        {
            'label': 'Constancias',
            'url':   '/constancias',
            'icono': 'fa-solid fa-file-circle-check'
        },
    ],
    'materias': [
        {
            'label': 'Materias',
            'url':   '/materias',
            'icono': 'fa-solid fa-book-open'
        },
    ],
    'asignacion_docente': [
        {
            'label': 'Asignación Docente',
            'url':   '/asignacion_docente',
            'icono': 'fa-solid fa-chalkboard-user'
        },
    ],
    'reportes': [
        {
            'label': 'Reportes',
            'url':   '/reportes',
            'icono': 'fa-solid fa-chart-bar'
        },
    ],
    'activos': [
        {
            'label': 'Control de Activos',
            'url':   '/activos',
            'icono': 'fa-solid fa-boxes-stacked'
        },
    ],
    'terminal': [
        {
            'label': 'Terminal del Sistema',
            'url':   '/admin/terminal',
            'icono': 'fa-solid fa-terminal'
        },
    ],
    'bitacora': [
        {
            'label': 'Bitácora de Actividad',
            'url':   '/bitacora',
            'icono': 'fa-solid fa-shield-halved'
        },
    ],
}


# ============================================================
# GRUPOS VISUALES DEL MENÚ
# Controla el orden y agrupación visual del sidebar.
# Un grupo puede contener varios módulos (ej: Documentos).
# ============================================================

MENU_GRUPOS = [
    {'titulo': 'Administración', 'modulos': ['usuarios']},
    {'titulo': 'Personal',       'modulos': ['personal']},
    {'titulo': 'Estudiantes',    'modulos': ['estudiantes']},
    {'titulo': 'Matrícula',      'modulos': ['matricula']},
    {'titulo': 'Evaluaciones',   'modulos': ['evaluaciones', 'momentos', 'notas_certificadas']},
    {'titulo': 'Documentos',     'modulos': ['constancias', 'citaciones']},
    {'titulo': 'Labor Social',   'modulos': ['labor_social']},
    {'titulo': 'Académico',      'modulos': ['materias', 'asignacion_docente']},
    {'titulo': 'Bienes e Inventario', 'modulos': ['activos']},
    {'titulo': 'Reportes',       'modulos': ['reportes']},
    {'titulo': 'Sistema',        'modulos': ['configuracion', 'terminal', 'bitacora']},
]


# ============================================================
# CONSTRUCTOR DEL MENÚ DINÁMICO
# ============================================================

def get_menu_items(rol: str) -> list:
    """
    Construye la lista de grupos del menú para el rol indicado.
    Solo incluye grupos que tengan al menos un módulo permitido.

    Args:
        rol: El rol del usuario autenticado (ej: 'admin', 'docente').

    Returns:
        Lista de grupos con sus ítems visibles.
        Ejemplo:
        [
            {
                'titulo': 'Matrícula',
                'items': [
                    {'label': 'Proceso de Matrícula', 'url': '/matricula', 'icono': '...'},
                    ...
                ]
            },
            ...
        ]
    """
    modulos_permitidos = set(PERMISOS.get(rol, []))
    menu = []

    for grupo in MENU_GRUPOS:
        items_del_grupo = []

        for modulo in grupo['modulos']:
            if modulo in modulos_permitidos:
                items_del_grupo.extend(MODULOS_ITEMS.get(modulo, []))

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

        @app.route('/evaluaciones')
        @login_required
        @rol_required('admin', 'coordinador', 'docente')
        def evaluaciones():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'usuario_id' not in session:
                return redirect(url_for('inicio'))
            if session.get('rol') not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def tiene_permiso_modulo(modulo: str) -> bool:
    """
    Verifica si el rol en sesión tiene acceso a un módulo específico.
    Útil para lógica condicional dentro de una función de vista.

    Args:
        modulo: Clave del módulo (ej: 'reportes', 'matricula').

    Returns:
        True si tiene acceso, False si no.

    Uso dentro de una vista:
        if not tiene_permiso_modulo('reportes'):
            abort(403)
    """
    rol = session.get('rol', '')
    return modulo in PERMISOS.get(rol, [])

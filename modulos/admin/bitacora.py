"""
bitacora.py — Módulo de Bitácora de Actividad del Sistema
PRISMA — Sistema de Gestión Escolar | Unidad Educativa Carmen Ruíz

Registra y visualiza todas las acciones importantes realizadas por los usuarios.
Solo accesible para el rol 'admin'.
"""

from flask import session, request, render_template
from db import supabase
from datetime import datetime, timezone


# ── Acciones que se muestran con nombre amigable ──────────────────────────────
_RUTAS_DESCRIPCIONES = {
    # Autenticación
    '/login':                   ('Inicio de Sesión',          'fa-right-to-bracket',  'login'),
    '/logout':                  ('Cierre de Sesión',           'fa-right-from-bracket', 'logout'),
    # Estudiantes
    '/registro_estu':           ('Registro de Estudiante',     'fa-user-plus',          'estudiante'),
    '/cargar_estudiantes_masivo':('Carga Masiva de Estudiantes','fa-file-excel',         'estudiante'),
    '/buscar_estu':             ('Búsqueda de Estudiante',     'fa-magnifying-glass',   'consulta'),
    # Matrícula
    '/matricula':               ('Proceso de Matrícula',       'fa-file-signature',     'matricula'),
    '/matricula_automatica':    ('Matrícula Automática',       'fa-wand-magic-sparkles', 'matricula'),
    # Personal
    '/personal':                ('Gestión de Personal',        'fa-id-badge',           'personal'),
    # Usuarios
    '/usuarios':                ('Gestión de Usuarios',        'fa-users-gear',         'usuario'),
    # Notas
    '/registro_notas':          ('Registro de Notas',          'fa-star-half-stroke',   'notas'),
    '/carga_masiva_notas':      ('Carga Masiva de Notas',      'fa-file-excel',         'notas'),
    '/boletines':               ('Generación de Boletines',    'fa-newspaper',          'boletin'),
    '/notas_certificadas':      ('Notas Certificadas',         'fa-certificate',        'certificado'),
    '/descargar_nota_xls':      ('Descarga Formato MPPE',      'fa-download',           'certificado'),
    # Académico
    '/materias':                ('Gestión de Materias',        'fa-book-open',          'academico'),
    '/asignacion_docente':      ('Asignación Docente',         'fa-chalkboard-user',    'academico'),
    '/secciones':               ('Gestión de Secciones',       'fa-layer-group',        'academico'),
    '/anio_escolar':            ('Año Escolar',                'fa-calendar-alt',       'academico'),
    '/configuracion_ano':       ('Configuración Año Escolar',  'fa-calendar-days',      'academico'),
    # Documentos
    '/constancias':             ('Constancias',                'fa-file-circle-check',  'documento'),
    '/citaciones':              ('Citaciones',                 'fa-envelope',           'documento'),
    # Sistema
    '/activos':                 ('Control de Activos',         'fa-boxes-stacked',      'sistema'),
    '/reportes':                ('Reportes',                   'fa-chart-bar',          'reporte'),
    '/menu':                    ('Acceso al Dashboard',        'fa-house',              'sistema'),
    '/momentos':                ('Momentos Evaluativos',       'fa-calendar-check',     'academico'),
    '/ejecutar_promocion':      ('Promoción Automática',       'fa-graduation-cap',     'sistema'),
    '/descargar_plantilla_estudiantes': ('Descarga Plantilla Estudiantes', 'fa-download', 'estudiante'),
}

# Métodos que NO registramos (solo GET puros de lectura en rutas de consulta)
_RUTAS_IGNORAR = {'/menu', '/buscar_estu'}

# Colores por categoría
_CATEGORIA_COLOR = {
    'login':      '#10b981',
    'logout':     '#64748b',
    'estudiante': '#3b82f6',
    'matricula':  '#8b5cf6',
    'personal':   '#f59e0b',
    'usuario':    '#ef4444',
    'notas':      '#06b6d4',
    'boletin':    '#14b8a6',
    'certificado':'#a78bfa',
    'academico':  '#6366f1',
    'documento':  '#ec4899',
    'sistema':    '#64748b',
    'reporte':    '#f97316',
    'consulta':   '#94a3b8',
}


def registrar_accion(ruta: str, metodo: str, codigo_http: int, detalle: str = ''):
    """
    Inserta un registro en la tabla `bitacora` de Supabase.
    Se llama desde el hook after_request de Flask.
    """
    if 'usuario_id' not in session:
        return

    # Solo registrar rutas conocidas o POST/DELETE/PATCH importantes
    info = _RUTAS_DESCRIPCIONES.get(ruta)
    if not info:
        return  # Ruta desconocida — ignorar

    # Ignorar GETs en rutas de solo consulta salvo las de descarga
    if metodo == 'GET' and ruta in _RUTAS_IGNORAR:
        return

    accion, icono, categoria = info

    try:
        ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if ip and ',' in ip:
            ip = ip.split(',')[0].strip()

        supabase.table('bitacora').insert({
            'usuario_id':    session.get('usuario_id'),
            'usuario_nombre': session.get('nombre', ''),
            'usuario_rol':   session.get('rol', ''),
            'accion':        accion,
            'icono':         icono,
            'categoria':     categoria,
            'ruta':          ruta,
            'metodo':        metodo,
            'codigo_http':   codigo_http,
            'ip':            ip,
            'detalle':       detalle,
            'fecha_hora':    datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception as e:
        print(f"[BITACORA] Error registrando acción: {e}")


def bitacora_view():
    """Vista de la bitácora — solo admin."""

    # Filtros desde query params
    filtro_usuario = request.args.get('usuario', '').strip()
    filtro_cat     = request.args.get('categoria', '').strip()
    filtro_fecha   = request.args.get('fecha', '').strip()
    pagina         = max(1, int(request.args.get('pagina', 1)))
    por_pagina     = 50

    try:
        query = supabase.table('bitacora').select('*').order('fecha_hora', desc=True)

        if filtro_usuario:
            query = query.ilike('usuario_nombre', f'%{filtro_usuario}%')
        if filtro_cat:
            query = query.eq('categoria', filtro_cat)
        if filtro_fecha:
            query = query.gte('fecha_hora', f'{filtro_fecha}T00:00:00').lte('fecha_hora', f'{filtro_fecha}T23:59:59')

        # Paginación manual
        offset = (pagina - 1) * por_pagina
        result = query.range(offset, offset + por_pagina - 1).execute()
        registros = result.data or []

        # Conteo total para paginación
        count_q = supabase.table('bitacora').select('id', count='exact')
        if filtro_usuario:
            count_q = count_q.ilike('usuario_nombre', f'%{filtro_usuario}%')
        if filtro_cat:
            count_q = count_q.eq('categoria', filtro_cat)
        if filtro_fecha:
            count_q = count_q.gte('fecha_hora', f'{filtro_fecha}T00:00:00').lte('fecha_hora', f'{filtro_fecha}T23:59:59')
        total = count_q.execute().count or 0

    except Exception as e:
        print(f"[BITACORA] Error cargando registros: {e}")
        registros = []
        total = 0

    categorias = list(_CATEGORIA_COLOR.keys())
    total_paginas = max(1, -(-total // por_pagina))  # ceil division

    # Enriquecer con colores
    for r in registros:
        r['color'] = _CATEGORIA_COLOR.get(r.get('categoria', ''), '#64748b')

    return render_template(
        'admin/bitacora.html',
        registros       = registros,
        total           = total,
        pagina          = pagina,
        total_paginas   = total_paginas,
        por_pagina      = por_pagina,
        filtro_usuario  = filtro_usuario,
        filtro_cat      = filtro_cat,
        filtro_fecha    = filtro_fecha,
        categorias      = categorias,
        colores_cat     = _CATEGORIA_COLOR,
    )

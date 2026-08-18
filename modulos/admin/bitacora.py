"""
bitacora.py — Módulo de Bitácora de Actividad del Sistema
PRISMA — Sistema de Gestión Escolar | Unidad Educativa Carmen Ruíz

Registra y visualiza todas las acciones importantes realizadas por los usuarios.
Incluye auditoría detallada con valor anterior/nuevo para cambios sensibles.

Accesible para: admin, director.
"""

from flask import session, request, render_template
from db import supabase
from datetime import datetime, timezone


# ── Acciones que se muestran con nombre amigable ──────────────────────────────
_RUTAS_DESCRIPCIONES = {
    # Autenticación
    '/login':                   ('Inicio de Sesión',           'fa-right-to-bracket',   'login'),
    '/logout':                  ('Cierre de Sesión',            'fa-right-from-bracket',  'logout'),
    # Estudiantes
    '/registro_estu':           ('Registro de Estudiante',      'fa-user-plus',           'estudiante'),
    '/cargar_estudiantes_masivo':('Carga Masiva de Estudiantes','fa-file-excel',          'estudiante'),
    '/buscar_estu':             ('Búsqueda de Estudiante',      'fa-magnifying-glass',    'consulta'),
    '/editar_estu':             ('Edición de Estudiante',       'fa-user-pen',            'estudiante'),
    # Matrícula
    '/matricula':               ('Proceso de Matrícula',        'fa-file-signature',      'matricula'),
    '/matricula_automatica':    ('Matrícula Automática',        'fa-wand-magic-sparkles',  'matricula'),
    # Personal
    '/personal':                ('Gestión de Personal',         'fa-id-badge',            'personal'),
    # Usuarios
    '/usuarios':                ('Gestión de Usuarios',         'fa-users-gear',          'usuario'),
    # Notas
    '/registro_notas':          ('Registro de Notas',           'fa-star-half-stroke',    'notas'),
    '/carga_masiva_notas':      ('Carga Masiva de Notas',       'fa-file-excel',          'notas'),
    '/boletines':               ('Generación de Boletines',     'fa-newspaper',           'boletin'),
    '/notas_certificadas':      ('Notas Certificadas',          'fa-certificate',         'certificado'),
    '/descargar_nota_xls':      ('Descarga Formato MPPE',       'fa-download',            'certificado'),
    # Académico
    '/materias':                ('Gestión de Materias',         'fa-book-open',           'academico'),
    '/asignacion_docente':      ('Asignación Docente',          'fa-chalkboard-user',     'academico'),
    '/secciones':               ('Gestión de Secciones',        'fa-layer-group',         'academico'),
    '/anio_escolar':            ('Año Escolar',                 'fa-calendar-alt',        'academico'),
    '/configuracion_ano':       ('Configuración Año Escolar',   'fa-calendar-days',       'academico'),
    '/momentos':                ('Momentos Evaluativos',        'fa-calendar-check',      'academico'),
    '/ejecutar_promocion':      ('Promoción Automática',        'fa-graduation-cap',      'sistema'),
    # Documentos
    '/constancias':             ('Constancias',                 'fa-file-circle-check',   'documento'),
    '/representantes':          ('Gestión de Representantes',   'fa-people-roof',         'estudiante'),
    # Sistema
    '/activos':                 ('Control de Activos',          'fa-boxes-stacked',       'sistema'),
    '/reportes':                ('Reportes',                    'fa-chart-bar',           'reporte'),
    '/menu':                    ('Acceso al Dashboard',         'fa-house',               'sistema'),
    '/descargar_plantilla_estudiantes': ('Descarga Plantilla Estudiantes', 'fa-download', 'estudiante'),
    # Acceso denegado
    '__acceso_denegado__':      ('Acceso Denegado (403)',       'fa-ban',                 'seguridad'),
}

# Rutas que se ignoran en el registro (GET puros de solo consulta)
_RUTAS_IGNORAR_GET = {'/menu', '/buscar_estu', '/directorio_estudiantil'}

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
    'seguridad':  '#dc2626',
}


# ── Función principal de registro ─────────────────────────────────────────────

def registrar_accion(ruta: str, metodo: str, codigo_http: int, detalle: str = '') -> int | None:
    """
    Inserta un registro en la tabla `bitacora` de Supabase.
    Se llama desde el hook after_request de Flask.

    Returns:
        ID del registro insertado (para usar con registrar_cambio_detalle), o None.
    """
    if 'usuario_id' not in session:
        return None

    # Solo registrar rutas conocidas
    info = _RUTAS_DESCRIPCIONES.get(ruta)
    if not info:
        return None

    # Ignorar GETs en rutas de solo consulta
    if metodo == 'GET' and ruta in _RUTAS_IGNORAR_GET:
        return None

    accion, icono, categoria = info

    try:
        ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if ip and ',' in ip:
            ip = ip.split(',')[0].strip()

        resultado = supabase.table('bitacora').insert({
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

        if resultado.data:
            return resultado.data[0].get('id')
        return None

    except Exception as e:
        print(f"[BITACORA] Error registrando acción: {e}")
        return None


def registrar_acceso_denegado(rol_intento: str) -> None:
    """
    Registra en bitácora cuando un usuario intenta acceder a una ruta
    para la que no tiene permisos (HTTP 403).

    Args:
        rol_intento: El rol del usuario que intentó el acceso.
    """
    if 'usuario_id' not in session:
        return

    try:
        ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if ip and ',' in ip:
            ip = ip.split(',')[0].strip()

        supabase.table('bitacora').insert({
            'usuario_id':     session.get('usuario_id'),
            'usuario_nombre': session.get('nombre', ''),
            'usuario_rol':    rol_intento,
            'accion':         f"Acceso Denegado — ruta: {request.path}",
            'icono':          'fa-ban',
            'categoria':      'seguridad',
            'ruta':           request.path,
            'metodo':         request.method,
            'codigo_http':    403,
            'ip':             ip,
            'detalle':        f"Rol '{rol_intento}' intentó acceder a '{request.path}'",
            'fecha_hora':     datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception as e:
        print(f"[BITACORA] Error registrando acceso denegado: {e}")


def registrar_cambio_detalle(
    entidad: str,
    entidad_id: str,
    campo: str,
    valor_anterior,
    valor_nuevo,
    bitacora_id: int = None,
    detalle_extra: str = ''
) -> None:
    """
    Registra el detalle de un cambio en un campo específico (valor anterior → valor nuevo).
    Se guarda en la tabla `auditoria_detalle`.

    Útil para rastrear cambios en notas, datos de estudiantes, estados de matrícula, etc.

    Args:
        entidad:        Nombre de la tabla/entidad afectada (ej: 'evaluacion', 'estudiante')
        entidad_id:     Identificador del registro afectado (cedula, id, etc.)
        campo:          Nombre del campo modificado (ej: 'nota', 'estado_matricula')
        valor_anterior: Valor antes del cambio
        valor_nuevo:    Valor después del cambio
        bitacora_id:    ID de la entrada en bitácora (para vincular, opcional)
        detalle_extra:  Texto libre adicional (motivo, observación, etc.)

    Ejemplo:
        registrar_cambio_detalle(
            entidad='evaluacion',
            entidad_id='V-12345678',
            campo='nota',
            valor_anterior=14.0,
            valor_nuevo=16.0,
            detalle_extra='Corrección solicitada por docente'
        )
    """
    if 'usuario_id' not in session:
        return

    try:
        supabase.table('auditoria_detalle').insert({
            'bitacora_id':     bitacora_id,
            'entidad':         entidad,
            'entidad_id':      str(entidad_id),
            'campo':           campo,
            'valor_anterior':  str(valor_anterior) if valor_anterior is not None else None,
            'valor_nuevo':     str(valor_nuevo) if valor_nuevo is not None else None,
            'usuario_id':      session.get('usuario_id'),
            'usuario_nombre':  session.get('nombre', ''),
            'usuario_rol':     session.get('rol', ''),
            'detalle':         detalle_extra,
            'created_at':      datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception as e:
        print(f"[BITACORA] Error registrando detalle de cambio: {e}")


# ── Vista de la bitácora ──────────────────────────────────────────────────────

def bitacora_view():
    """Vista de la bitácora — para admin y director."""

    # Filtros desde query params
    filtro_usuario = request.args.get('usuario', '').strip()
    filtro_cat     = request.args.get('categoria', '').strip()
    filtro_fecha   = request.args.get('fecha', '').strip()
    pagina         = max(1, int(request.args.get('pagina', 1)))
    por_pagina     = 50

    rol_actual = session.get('rol', '')

    try:
        query = supabase.table('bitacora').select('*').order('fecha_hora', desc=True)

        # El director no ve acciones del administrador
        if rol_actual != 'admin':
            query = query.neq('usuario_rol', 'admin')

        if filtro_usuario:
            query = query.ilike('usuario_nombre', f'%{filtro_usuario}%')
        if filtro_cat:
            query = query.eq('categoria', filtro_cat)
        if filtro_fecha:
            query = query.gte('fecha_hora', f'{filtro_fecha}T00:00:00') \
                         .lte('fecha_hora', f'{filtro_fecha}T23:59:59')

        # Paginación
        offset = (pagina - 1) * por_pagina
        result = query.range(offset, offset + por_pagina - 1).execute()
        registros = result.data or []

        # Conteo total
        count_q = supabase.table('bitacora').select('id', count='exact')
        if rol_actual != 'admin':
            count_q = count_q.neq('usuario_rol', 'admin')
        if filtro_usuario:
            count_q = count_q.ilike('usuario_nombre', f'%{filtro_usuario}%')
        if filtro_cat:
            count_q = count_q.eq('categoria', filtro_cat)
        if filtro_fecha:
            count_q = count_q.gte('fecha_hora', f'{filtro_fecha}T00:00:00') \
                             .lte('fecha_hora', f'{filtro_fecha}T23:59:59')
        total = count_q.execute().count or 0

    except Exception as e:
        print(f"[BITACORA] Error cargando registros: {e}")
        registros = []
        total = 0

    categorias = list(_CATEGORIA_COLOR.keys())
    total_paginas = max(1, -(-total // por_pagina))  # ceil division

    # Enriquecer con colores y formato de tiempo relativo
    ahora = datetime.now(timezone.utc)
    for r in registros:
        r['color'] = _CATEGORIA_COLOR.get(r.get('categoria', ''), '#64748b')
        fh = r.get('fecha_hora', '')
        try:
            dt = datetime.fromisoformat(fh.replace('Z', '+00:00'))
            diff = ahora - dt
            mins = int(diff.total_seconds() / 60)
            if mins < 1:
                r['hace'] = 'ahora mismo'
            elif mins < 60:
                r['hace'] = f'{mins} min atrás'
            elif mins < 1440:
                r['hace'] = f'{mins // 60}h atrás'
            else:
                r['hace'] = f'{mins // 1440}d atrás'
        except Exception:
            r['hace'] = '—'

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

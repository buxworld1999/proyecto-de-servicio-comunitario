"""
asignacion_docente_view.py — Gestión de Asignación Docente-Materia-Sección
PRISMA — Sistema de Gestión Escolar | Unidad Educativa Carmen Ruíz

Tabla: asignacion_docente(id, cedula_docente FK→personal, codigo_seccion FK→seccion,
       codigo_materia FK→materia, codigo_ano_escolar FK→ano_escolar,
       horas_asignadas, turno, id_imagen)
"""

from flask import render_template, request, redirect, url_for, flash, session
from db import supabase


def _get_ano_activo():
    """Retorna el código del año escolar activo."""
    try:
        resp = supabase.table("ano_escolar").select("codigo") \
            .eq("activo", True).limit(1).execute()
        if resp.data:
            return resp.data[0]['codigo']
    except Exception:
        pass
    return None


def asignacion_docente_view():
    """
    Controlador de asignaciones docente-materia-sección.
    GET  → lista asignaciones con filtros.
    POST → crear o eliminar asignación.
    """
    # ── Datos de selects ──────────────────────────────────────────────
    try:
        resp_anos = supabase.table("ano_escolar").select("codigo, descripcion, activo") \
            .order("codigo", desc=True).execute()
        anos = resp_anos.data or []
    except Exception as e:
        flash(f"Error cargando años: {str(e)}", "danger")
        anos = []

    try:
        # Obtener las cédulas de los usuarios registrados con el rol 'docente'
        resp_usuarios = supabase.table("usuario").select("cedula_personal").eq("rol", "docente").eq("estado", "A").execute()
        cedulas_validas = [u['cedula_personal'] for u in (resp_usuarios.data or []) if u.get('cedula_personal')]

        if cedulas_validas:
            resp_doc = supabase.table("personal").select("cedula, nombres, apellidos, cargo") \
                .eq("estado", "A").in_("cedula", cedulas_validas).order("apellidos").execute()
            docentes = resp_doc.data or []
        else:
            docentes = []
    except Exception as e:
        flash(f"Error cargando docentes: {str(e)}", "danger")
        docentes = []

    try:
        resp_mat = supabase.table("materia").select("codigo, nombre, codigo_grado") \
            .eq("estado", "A").order("nombre").execute()
        materias = resp_mat.data or []
    except Exception as e:
        flash(f"Error cargando materias: {str(e)}", "danger")
        materias = []

    try:
        resp_sec = supabase.table("seccion").select("codigo, letra, codigo_grado, codigo_ano_escolar") \
            .order("codigo").execute()
        secciones_todas = resp_sec.data or []
    except Exception as e:
        flash(f"Error cargando secciones: {str(e)}", "danger")
        secciones_todas = []

    # ── Filtros ───────────────────────────────────────────────────────
    ano_filtro  = request.args.get('ano') or _get_ano_activo() or (anos[0]['codigo'] if anos else '')
    doc_filtro  = request.args.get('docente', '')
    sec_filtro  = request.args.get('seccion', '')

    # Secciones del año seleccionado
    secciones = [s for s in secciones_todas if s.get('codigo_ano_escolar') == ano_filtro]

    # ── Cargar asignaciones ───────────────────────────────────────────
    asignaciones = []
    if ano_filtro:
        try:
            query = supabase.table("asignacion_docente").select(
                "id, cedula_docente, codigo_seccion, codigo_materia, "
                "codigo_ano_escolar, horas_asignadas, turno, "
                "personal(nombres, apellidos), "
                "materia(nombre, codigo_grado), "
                "seccion(letra, codigo_grado)"
            ).eq("codigo_ano_escolar", ano_filtro)

            if doc_filtro:
                query = query.eq("cedula_docente", doc_filtro)
            if sec_filtro:
                query = query.eq("codigo_seccion", sec_filtro)

            resp_asig = query.order("codigo_seccion").execute()
            asignaciones = resp_asig.data or []
        except Exception as e:
            flash(f"Error cargando asignaciones: {str(e)}", "danger")

    # ── POST ─────────────────────────────────────────────────────────
    if request.method == 'POST':
        accion = request.form.get('accion', '')

        if accion == 'crear':
            cedula_doc = request.form.get('cedula_docente', '').strip()
            cod_sec    = request.form.get('codigo_seccion', '').strip()
            cod_mat    = request.form.get('codigo_materia', '').strip()
            cod_ano    = request.form.get('codigo_ano_escolar', ano_filtro).strip()

            if not all([cedula_doc, cod_sec, cod_mat, cod_ano]):
                flash("Todos los campos son obligatorios.", "warning")
            else:
                try:
                    horas = int(request.form.get('horas_asignadas', 4))
                except (TypeError, ValueError):
                    horas = 4

                dato = {
                    "cedula_docente":     cedula_doc,
                    "codigo_seccion":     cod_sec,
                    "codigo_materia":     cod_mat,
                    "codigo_ano_escolar": cod_ano,
                    "horas_asignadas":    horas,
                    "turno":              request.form.get('turno', 'M'),
                }
                try:
                    supabase.table("asignacion_docente").insert(dato).execute()
                    flash("Asignación creada exitosamente.", "success")
                except Exception as e:
                    flash(f"Error al crear asignación: {str(e)}", "danger")

        elif accion == 'eliminar':
            asig_id = request.form.get('asig_id')
            try:
                supabase.table("asignacion_docente").delete().eq("id", int(asig_id)).execute()
                flash("Asignación eliminada.", "success")
            except Exception as e:
                flash(f"Error al eliminar: {str(e)}", "danger")

        return redirect(url_for('asignacion_docente', ano=ano_filtro, docente=doc_filtro, seccion=sec_filtro))

    # ── Resumen ───────────────────────────────────────────────────────
    total_docentes_asignados = len({a.get('cedula_docente') for a in asignaciones})
    total_asignaciones = len(asignaciones)

    return render_template(
        'academico/asignacion_docente.html',
        anos                    = anos,
        docentes                = docentes,
        materias                = materias,
        secciones               = secciones,
        asignaciones            = asignaciones,
        ano_filtro              = ano_filtro,
        doc_filtro              = doc_filtro,
        sec_filtro              = sec_filtro,
        total_docentes_asignados = total_docentes_asignados,
        total_asignaciones      = total_asignaciones,
    )

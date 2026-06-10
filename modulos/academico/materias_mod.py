"""
materias_mod.py — Gestión de Materias / Asignaturas
PRISMA — Sistema de Gestión Escolar | Unidad Educativa Carmen Ruíz

Tabla principal: materia(codigo PK, nombre, abreviatura, area_formacion,
    codigo_grado FK→grado, horas_semanales, obligatoria, tipo_evaluacion,
    se_repara, nota_minima_aprobacion, estado)
"""

from flask import render_template, request, redirect, url_for, flash
from db import supabase


def _cargar_grados():
    try:
        resp = supabase.table("grado").select("codigo, nombre") \
            .order("numero_ano").execute()
        return resp.data or []
    except Exception as e:
        flash(f"Error cargando grados: {str(e)}", "danger")
        return []


def materias_view():
    """
    Controlador CRUD de materias.
    GET  → lista materias filtradas por grado.
    POST → crear, editar o cambiar estado de una materia.
    """
    grados = _cargar_grados()

    # Filtro por grado
    grado_sel = request.args.get('grado', 'todos')

    # ── Cargar materias ──────────────────────────────────────────────
    try:
        query = supabase.table("materia").select(
            "codigo, nombre, abreviatura, area_formacion, codigo_grado, "
            "horas_semanales, obligatoria, tipo_evaluacion, se_repara, "
            "nota_minima_aprobacion, estado"
        )
        if grado_sel != 'todos':
            query = query.eq("codigo_grado", grado_sel)
        resp = query.order("codigo_grado").order("nombre").execute()
        materias = resp.data or []
    except Exception as e:
        flash(f"Error cargando materias: {str(e)}", "danger")
        materias = []

    # Agrupar por grado para la vista
    grados_dict = {g['codigo']: g['nombre'] for g in grados}

    # ── POST ─────────────────────────────────────────────────────────
    if request.method == 'POST':
        accion = request.form.get('accion', '')

        if accion == 'crear':
            _crear_materia()

        elif accion == 'editar':
            _editar_materia()

        elif accion == 'cambiar_estado':
            codigo     = request.form.get('codigo')
            est_actual = request.form.get('estado_actual', 'A')
            nuevo      = 'I' if est_actual == 'A' else 'A'
            try:
                supabase.table("materia").update({"estado": nuevo}).eq("codigo", codigo).execute()
                flash(f"Materia '{codigo}' {'activada' if nuevo == 'A' else 'desactivada'}.", "success")
            except Exception as e:
                flash(f"Error: {str(e)}", "danger")

        return redirect(url_for('materias', grado=grado_sel))

    # Estadísticas
    total_activas   = sum(1 for m in materias if m.get('estado') == 'A')
    total_inactivas = len(materias) - total_activas

    return render_template(
        'materias.html',
        materias        = materias,
        grados          = grados,
        grados_dict     = grados_dict,
        grado_sel       = grado_sel,
        total_activas   = total_activas,
        total_inactivas = total_inactivas,
    )


def _crear_materia():
    codigo = request.form.get('codigo', '').strip().upper()
    nombre = request.form.get('nombre', '').strip()

    if not codigo or not nombre:
        flash("Código y nombre son obligatorios.", "warning")
        return

    try:
        horas = int(request.form.get('horas_semanales', 4))
    except (TypeError, ValueError):
        horas = 4

    try:
        nota_min = float(request.form.get('nota_minima_aprobacion', 10.0))
    except (TypeError, ValueError):
        nota_min = 10.0

    dato = {
        "codigo":                  codigo,
        "nombre":                  nombre,
        "abreviatura":             request.form.get('abreviatura') or None,
        "area_formacion":          request.form.get('area_formacion') or None,
        "codigo_grado":            request.form.get('codigo_grado') or None,
        "horas_semanales":         horas,
        "obligatoria":             request.form.get('obligatoria') == '1',
        "tipo_evaluacion":         request.form.get('tipo_evaluacion', 'C'),
        "se_repara":               request.form.get('se_repara') == '1',
        "nota_minima_aprobacion":  nota_min,
        "estado":                  'A',
    }
    try:
        supabase.table("materia").insert(dato).execute()
        flash(f"Materia '{nombre}' creada exitosamente.", "success")
    except Exception as e:
        flash(f"Error al crear materia: {str(e)}", "danger")


def _editar_materia():
    codigo = request.form.get('codigo', '').strip()
    if not codigo:
        flash("Código requerido para editar.", "warning")
        return

    try:
        horas = int(request.form.get('horas_semanales', 4))
    except (TypeError, ValueError):
        horas = 4

    try:
        nota_min = float(request.form.get('nota_minima_aprobacion', 10.0))
    except (TypeError, ValueError):
        nota_min = 10.0

    dato = {
        "nombre":                  request.form.get('nombre', '').strip(),
        "abreviatura":             request.form.get('abreviatura') or None,
        "area_formacion":          request.form.get('area_formacion') or None,
        "codigo_grado":            request.form.get('codigo_grado') or None,
        "horas_semanales":         horas,
        "obligatoria":             request.form.get('obligatoria') == '1',
        "tipo_evaluacion":         request.form.get('tipo_evaluacion', 'C'),
        "se_repara":               request.form.get('se_repara') == '1',
        "nota_minima_aprobacion":  nota_min,
    }
    try:
        supabase.table("materia").update(dato).eq("codigo", codigo).execute()
        flash(f"Materia '{codigo}' actualizada exitosamente.", "success")
    except Exception as e:
        flash(f"Error al actualizar materia: {str(e)}", "danger")

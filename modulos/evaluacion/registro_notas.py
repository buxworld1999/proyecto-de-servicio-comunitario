"""
registro_notas.py — Módulo de Registro de Calificaciones
PRISMA — Sistema de Gestión Escolar | Unidad Educativa Carmen Ruíz

Flujo:
  1. Docente/Admin selecciona: año_escolar + sección + materia + momento
  2. El sistema carga la lista de estudiantes matriculados en esa sección/año
  3. Se muestran las notas existentes (si hay) en la tabla evaluacion
  4. Se permite ingresar/actualizar notas con validaciones
  5. Guarda en tabla: evaluacion

Tabla: evaluacion(id, cedula_estudiante, codigo_materia, codigo_ano_escolar,
       numero_momento, nota, resultado, fecha_evaluacion, observaciones,
       es_revision, cedula_docente_evaluador, fecha_modificacion, motivo_modificacion)
"""

from datetime import date
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from db import supabase


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _get_ano_activo():
    try:
        resp = supabase.table("ano_escolar").select("codigo") \
            .eq("activo", True).limit(1).execute()
        return resp.data[0]['codigo'] if resp.data else None
    except Exception:
        return None


def _nota_resultado(nota: float, nota_min: float = 10.0) -> str:
    """Determina resultado A/R según la nota."""
    return 'A' if nota >= nota_min else 'R'


def _get_cedula_personal():
    """Obtiene la cédula del personal desde la sesión o BD."""
    cedula = session.get('cedula_personal')
    if cedula:
        return cedula
    # Fallback: buscar por usuario_id
    try:
        resp = supabase.table("usuario").select("cedula_personal") \
            .eq("id", session.get('usuario_id')).limit(1).execute()
        if resp.data:
            return resp.data[0].get('cedula_personal')
    except Exception:
        pass
    return None


# ─── Vista Principal ──────────────────────────────────────────────────────────

def registro_notas_view():
    """
    Controlador principal de registro de notas.
    GET  → muestra formulario de selección + planilla de notas.
    POST → guarda/actualiza las calificaciones ingresadas.
    """
    rol = session.get('rol', '')
    cedula_personal = _get_cedula_personal()

    # ── 1. Cargar listas para selects ────────────────────────────────
    try:
        resp_anos = supabase.table("ano_escolar").select("codigo, descripcion, activo") \
            .order("codigo", desc=True).execute()
        anos = resp_anos.data or []
    except Exception as e:
        flash(f"Error cargando años: {str(e)}", "danger")
        anos = []

    # Si es docente, limitar a sus asignaciones
    asignaciones_docente = []
    if rol == 'docente' and cedula_personal:
        try:
            resp_asig = supabase.table("asignacion_docente").select(
                "id, codigo_seccion, codigo_materia, codigo_ano_escolar, "
                "materia(nombre), seccion(letra, codigo_grado)"
            ).eq("cedula_docente", cedula_personal).execute()
            asignaciones_docente = resp_asig.data or []
        except Exception as e:
            flash(f"Error cargando asignaciones: {str(e)}", "danger")

    try:
        resp_sec = supabase.table("seccion").select("codigo, letra, codigo_grado, codigo_ano_escolar") \
            .order("codigo").execute()
        secciones_todas = resp_sec.data or []
    except Exception as e:
        secciones_todas = []

    try:
        resp_mat = supabase.table("materia").select("codigo, nombre, nota_minima_aprobacion") \
            .eq("estado", "A").order("nombre").execute()
        materias = resp_mat.data or []
    except Exception as e:
        materias = []

    try:
        resp_mom = supabase.table("momento_evaluativo").select("numero, nombre, estado") \
            .order("numero").execute()
        momentos = resp_mom.data or []
    except Exception as e:
        momentos = []

    if not momentos:
        momentos = [
            {"numero": 1, "nombre": "Primer Momento", "estado": "A"},
            {"numero": 2, "nombre": "Segundo Momento", "estado": "A"},
            {"numero": 3, "nombre": "Tercer Momento",  "estado": "A"},
        ]

    # ── 2. Filtros seleccionados ──────────────────────────────────────
    ano_sel     = request.args.get('ano',     _get_ano_activo() or '')
    seccion_sel = request.args.get('seccion', '')
    materia_sel = request.args.get('materia', '')
    momento_sel = request.args.get('momento', '')

    # Secciones filtradas por año
    secciones = [s for s in secciones_todas if s.get('codigo_ano_escolar') == ano_sel]

    # ── 3. Si hay selección completa → cargar planilla ────────────────
    estudiantes_planilla = []
    materia_info         = None
    momento_info         = None
    momento_cerrado      = False

    if all([ano_sel, seccion_sel, materia_sel, momento_sel]):
        try:
            num_momento = int(momento_sel)
        except ValueError:
            num_momento = None

        if num_momento:
            # Info del momento
            momento_info = next(
                (m for m in momentos if m['numero'] == num_momento), None
            )
            momento_cerrado = momento_info and momento_info.get('estado') == 'C'

            # Info de la materia (nota mínima)
            materia_info = next((m for m in materias if m['codigo'] == materia_sel), None)
            nota_min = float(materia_info.get('nota_minima_aprobacion') or 10.0) if materia_info else 10.0

            # ── Estudiantes matriculados en la sección/año ────────────
            try:
                resp_mat_est = supabase.table("matricula").select(
                    "id, cedula_estudiante, numero_lista, "
                    "estudiante(nombres, apellidos, genero)"
                ).eq("codigo_seccion", seccion_sel) \
                 .eq("codigo_ano_escolar", ano_sel) \
                 .eq("estado_matricula", 'A') \
                 .order("numero_lista").execute()
                matriculas = resp_mat_est.data or []
            except Exception as e:
                flash(f"Error cargando estudiantes: {str(e)}", "danger")
                matriculas = []

            # ── Notas existentes ──────────────────────────────────────
            cedulas = [m['cedula_estudiante'] for m in matriculas]
            notas_existentes = {}
            if cedulas:
                try:
                    resp_ev = supabase.table("evaluacion").select(
                        "cedula_estudiante, nota, resultado, observaciones, id"
                    ).eq("codigo_materia", materia_sel) \
                     .eq("codigo_ano_escolar", ano_sel) \
                     .eq("numero_momento", num_momento) \
                     .execute()
                    notas_existentes = {
                        e['cedula_estudiante']: e for e in (resp_ev.data or [])
                    }
                except Exception as e:
                    flash(f"Error cargando notas existentes: {str(e)}", "danger")

            # ── Construir planilla ────────────────────────────────────
            vistos = set()
            for m in matriculas:
                cedula     = m['cedula_estudiante']
                if cedula in vistos:
                    continue
                vistos.add(cedula)
                
                est        = m.get('estudiante') or {}
                ev_exist   = notas_existentes.get(cedula)
                nota_val   = ev_exist['nota'] if ev_exist else None

                estudiantes_planilla.append({
                    "cedula":           cedula,
                    "nombres":          est.get('nombres', ''),
                    "apellidos":        est.get('apellidos', ''),
                    "numero_lista":     m.get('numero_lista', ''),
                    "nota_existente":   nota_val,
                    "obs_existente":    ev_exist.get('observaciones', '') if ev_exist else '',
                    "eval_id":          ev_exist['id'] if ev_exist else None,
                    "resultado":        _nota_resultado(nota_val, nota_min) if nota_val is not None else None,
                })

    # ── 4. POST: guardar notas ────────────────────────────────────────
    if request.method == 'POST':
        accion = request.form.get('accion', '')

        if accion == 'guardar_notas':
            ano_form     = request.form.get('ano_escolar', '')
            seccion_form = request.form.get('codigo_seccion', '')
            materia_form = request.form.get('codigo_materia', '')
            momento_form = request.form.get('numero_momento', '')

            try:
                num_mom = int(momento_form)
            except (TypeError, ValueError):
                flash("Momento inválido.", "danger")
                return redirect(url_for('registro_notas'))

            # Verificar que el momento esté abierto
            mom_check = next((m for m in momentos if m['numero'] == num_mom), None)
            if mom_check and mom_check.get('estado') == 'C':
                flash("⚠ Este momento está CERRADO. No se pueden registrar notas.", "warning")
                return redirect(url_for('registro_notas',
                    ano=ano_form, seccion=seccion_form,
                    materia=materia_form, momento=momento_form))

            # Materia info para nota mínima
            mat_info  = next((m for m in materias if m['codigo'] == materia_form), None)
            nota_min  = float(mat_info.get('nota_minima_aprobacion') or 10.0) if mat_info else 10.0
            hoy       = date.today().isoformat()

            guardados = actualizados = errores = 0

            # Recorrer todas las cédulas enviadas
            cedulas_form = request.form.getlist('cedula[]')
            for cedula in cedulas_form:
                nota_str = request.form.get(f'nota_{cedula}', '').strip()
                obs_str  = request.form.get(f'obs_{cedula}',  '').strip() or None
                eval_id  = request.form.get(f'eval_id_{cedula}', '').strip()

                # Nota vacía = no registrar
                if not nota_str:
                    continue

                try:
                    nota_float = float(nota_str)
                    if not (0 <= nota_float <= 20):
                        flash(f"⚠ Nota fuera de rango (0-20) para cédula {cedula}.", "warning")
                        continue
                except ValueError:
                    flash(f"⚠ Nota inválida para cédula {cedula}.", "warning")
                    continue

                resultado = _nota_resultado(nota_float, nota_min)

                dato = {
                    "cedula_estudiante":       cedula,
                    "codigo_materia":          materia_form,
                    "codigo_ano_escolar":      ano_form,
                    "numero_momento":          num_mom,
                    "nota":                    nota_float,
                    "resultado":               resultado,
                    "fecha_evaluacion":        hoy,
                    "observaciones":           obs_str,
                    "cedula_docente_evaluador": cedula_personal,
                }

                try:
                    if eval_id:
                        # Actualizar registro existente
                        dato['fecha_modificacion'] = hoy
                        supabase.table("evaluacion").update(dato).eq("id", int(eval_id)).execute()
                        actualizados += 1
                    else:
                        # Insertar nuevo
                        supabase.table("evaluacion").insert(dato).execute()
                        guardados += 1
                except Exception as e:
                    errores += 1
                    flash(f"Error al guardar nota para {cedula}: {str(e)}", "danger")

            # Resumen
            partes = []
            if guardados:   partes.append(f"{guardados} notas guardadas")
            if actualizados: partes.append(f"{actualizados} actualizadas")
            if errores:      partes.append(f"{errores} con errores")

            categoria = "success" if not errores else "warning"
            if not errores:
                flash(f"Proceso completado: {', '.join(partes)}.", categoria)
            else:
                flash(f"Proceso completado con problemas: {', '.join(partes)}.", categoria)

            return redirect(url_for('registro_notas',
                ano=ano_form, seccion=seccion_form,
                materia=materia_form, momento=momento_form))

    return render_template(
        'registro_notas.html',
        anos                 = anos,
        secciones            = secciones,
        materias             = materias,
        momentos             = momentos,
        asignaciones_docente = asignaciones_docente,
        ano_sel              = ano_sel,
        seccion_sel          = seccion_sel,
        materia_sel          = materia_sel,
        momento_sel          = momento_sel,
        estudiantes_planilla = estudiantes_planilla,
        materia_info         = materia_info,
        momento_info         = momento_info,
        momento_cerrado      = momento_cerrado,
        rol                  = rol,
    )

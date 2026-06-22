"""
boletines_mod.py — Generación y Visualización de Boletines de Calificaciones
PRISMA — Sistema de Gestión Escolar | Unidad Educativa Carmen Ruíz

Tablas:
  - boletin(id, cedula_estudiante, codigo_ano_escolar, codigo_seccion,
            numero_momento, promedio_general, mencion, resultado_final,
            fecha_generacion, tipo_boletin, observaciones)
  - detalle_boletin(id, id_boletin, codigo_materia, nota_momento1,
                    nota_momento2, nota_momento3, nota_final,
                    resultado_materia, es_revision, observaciones)

Flujo:
  1. Usuario busca estudiante por cédula o lista por sección/año
  2. Sistema calcula notas desde tabla evaluacion
  3. Se genera/actualiza registro en boletin + detalle_boletin
  4. Vista imprimible en HTML con diseño institucional
"""

from datetime import date
from flask import render_template, request, redirect, url_for, flash, session
from db import supabase


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _get_ano_activo():
    try:
        resp = supabase.table("ano_escolar").select("codigo") \
            .eq("activo", True).limit(1).execute()
        return resp.data[0]['codigo'] if resp.data else None
    except Exception:
        return None


def _nota_resultado(nota, nota_min=10.0) -> str:
    if nota is None:
        return 'P'   # Pendiente
    return 'A' if float(nota) >= float(nota_min) else 'R'


def _calcular_nota_final(n1, n2, n3, p1=33.33, p2=33.33, p3=33.34):
    """
    Calcula la nota definitiva ponderada.
    Si algún momento no tiene nota, usa solo los disponibles en proporción.
    """
    pares = [(n, p) for n, p in [(n1, p1), (n2, p2), (n3, p3)] if n is not None]
    if not pares:
        return None
    # Si hay los 3, usa pesos; si faltan, promedio simple de los disponibles
    if len(pares) == 3:
        total_peso = p1 + p2 + p3
        nota = sum(n * p for n, p in pares) / total_peso
    else:
        nota = sum(n for n, _ in pares) / len(pares)
    return round(nota, 2)


# ─── Vista principal (listado) ────────────────────────────────────────────────

def boletines_view():
    """
    Controlador principal del módulo de boletines.
    Muestra buscador por cédula y lista de boletines existentes.
    """
    # ── Datos para filtros ────────────────────────────────────────────
    try:
        resp_anos = supabase.table("ano_escolar").select("codigo, descripcion, activo") \
            .order("codigo", desc=True).execute()
        anos = resp_anos.data or []
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        anos = []

    try:
        resp_sec = supabase.table("seccion").select("codigo, letra, codigo_grado, codigo_ano_escolar") \
            .order("codigo").execute()
        secciones_todas = resp_sec.data or []
    except Exception:
        secciones_todas = []

    ano_sel = request.args.get('ano', _get_ano_activo() or '')
    sec_sel = request.args.get('seccion', '')
    secciones = [s for s in secciones_todas if s.get('codigo_ano_escolar') == ano_sel]

    # ── Búsqueda por cédula ───────────────────────────────────────────
    estudiante_buscado = None
    matricula_buscada  = None
    cedula_buscar = request.args.get('cedula', '').strip()

    if cedula_buscar:
        try:
            resp_est = supabase.table("estudiante").select("cedula, nombres, apellidos") \
                .eq("cedula", cedula_buscar).limit(1).execute()
            if resp_est.data:
                estudiante_buscado = resp_est.data[0]
                resp_mat = supabase.table("matricula").select("id, codigo_seccion, codigo_ano_escolar") \
                    .eq("cedula_estudiante", cedula_buscar) \
                    .eq("codigo_ano_escolar", ano_sel) \
                    .limit(1).execute()
                if resp_mat.data:
                    matricula_buscada = resp_mat.data[0]
            else:
                flash(f"No se encontró estudiante con cédula '{cedula_buscar}'.", "warning")
        except Exception as e:
            flash(f"Error en búsqueda: {str(e)}", "danger")

    # ── Boletines existentes ──────────────────────────────────────────
    boletines = []
    try:
        query = supabase.table("boletin").select(
            "id, cedula_estudiante, codigo_seccion, numero_momento, "
            "promedio_general, resultado_final, fecha_generacion, tipo_boletin, "
            "estudiante(nombres, apellidos)"
        ).eq("codigo_ano_escolar", ano_sel)
        if sec_sel:
            query = query.eq("codigo_seccion", sec_sel)
        if cedula_buscar and estudiante_buscado:
            query = query.eq("cedula_estudiante", cedula_buscar)
        resp_bol = query.order("fecha_generacion", desc=True).execute()
        boletines = resp_bol.data or []
    except Exception as e:
        flash(f"Error cargando boletines: {str(e)}", "danger")

    # ── POST: Generar boletín ─────────────────────────────────────────
    if request.method == 'POST':
        accion = request.form.get('accion', '')

        if accion == 'generar':
            cedula     = request.form.get('cedula_estudiante', '').strip()
            ano_form   = request.form.get('codigo_ano_escolar', '')
            seccion    = request.form.get('codigo_seccion', '')
            tipo       = request.form.get('tipo_boletin', 'final')  # 'parcial' o 'final'
            num_mom    = request.form.get('numero_momento')
            obs        = request.form.get('observaciones', '') or None

            boletin_id = _generar_boletin(cedula, ano_form, seccion, tipo, num_mom, obs)
            if boletin_id:
                return redirect(url_for('boletin_ver', boletin_id=boletin_id))
        
        return redirect(url_for('boletines', ano=ano_sel, seccion=sec_sel, cedula=cedula_buscar))

    return render_template(
        'evaluacion/boletines.html',
        anos               = anos,
        secciones          = secciones,
        boletines          = boletines,
        ano_sel            = ano_sel,
        sec_sel            = sec_sel,
        cedula_buscar      = cedula_buscar,
        estudiante_buscado = estudiante_buscado,
        matricula_buscada  = matricula_buscada,
    )


# ─── Generador de Boletín ─────────────────────────────────────────────────────

def _generar_boletin(cedula, ano, seccion, tipo='final', num_mom=None, obs=None):
    """
    Genera o actualiza un boletín completo para un estudiante.
    Retorna el id del boletín generado, o None si hay error.
    """
    hoy = date.today().isoformat()
    num_mom_int = int(num_mom) if num_mom and str(num_mom).isdigit() else 3

    # ── 1. Eliminar boletín(es) existentes para evitar duplicados ──────
    # Se buscan todos los boletines previos del mismo estudiante/año/sección/tipo,
    # se borran sus detalles primero (por la FK), y luego el boletín padre.
    try:
        resp_prev = supabase.table("boletin").select("id") \
            .eq("cedula_estudiante", cedula) \
            .eq("codigo_ano_escolar", ano) \
            .eq("codigo_seccion", seccion) \
            .eq("tipo_boletin", tipo) \
            .execute()
        for bol_prev in (resp_prev.data or []):
            prev_id = bol_prev['id']
            try:
                supabase.table("detalle_boletin").delete().eq("id_boletin", prev_id).execute()
            except Exception:
                pass
            supabase.table("boletin").delete().eq("id", prev_id).execute()
    except Exception:
        pass

    # ── 2. Obtener porcentajes de cada momento ────────────────────────
    porcentajes = {1: 33.33, 2: 33.33, 3: 33.34}
    try:
        resp_mom = supabase.table("momento_evaluativo").select("numero, porcentaje") \
            .execute()
        for m in (resp_mom.data or []):
            if m.get('porcentaje'):
                porcentajes[m['numero']] = float(m['porcentaje'])
    except Exception:
        pass

    # ── 3. Materias activas del grado de la sección ───────────────────
    seccion_info = None
    try:
        resp_sec = supabase.table("seccion").select("codigo_grado") \
            .eq("codigo", seccion).limit(1).execute()
        if resp_sec.data:
            seccion_info = resp_sec.data[0]
    except Exception:
        pass

    try:
        resp_asig = supabase.table("asignacion_docente").select("codigo_materia") \
            .eq("codigo_seccion", seccion).eq("codigo_ano_escolar", ano).execute()
        materias_asignadas = [a['codigo_materia'] for a in (resp_asig.data or [])]

        resp_ev = supabase.table("evaluacion").select("codigo_materia") \
            .eq("cedula_estudiante", cedula).eq("codigo_ano_escolar", ano).execute()
        materias_evaluadas = [e['codigo_materia'] for e in (resp_ev.data or [])]

        codigos_materias = list(set(materias_asignadas + materias_evaluadas))

        if codigos_materias:
            q_mat = supabase.table("materia").select("codigo, nombre, nota_minima_aprobacion") \
                .in_("codigo", codigos_materias).eq("estado", "A").order("nombre").execute()
            materias = q_mat.data or []
        else:
            materias = []
            
    except Exception as e:
        flash(f"Error cargando materias: {str(e)}", "danger")
        return None

    if not materias:
        flash("No hay materias configuradas para este estudiante/grado.", "warning")
        return None

    # ── 4. Notas del estudiante ───────────────────────────────────────
    try:
        resp_ev = supabase.table("evaluacion").select(
            "cedula_estudiante, codigo_materia, numero_momento, nota, resultado"
        ).eq("cedula_estudiante", cedula).eq("codigo_ano_escolar", ano).execute()
        evaluaciones = resp_ev.data or []
    except Exception as e:
        flash(f"Error cargando notas: {str(e)}", "danger")
        return None

    # Indexar: {codigo_materia: {1: nota, 2: nota, 3: nota}}
    notas_idx = {}
    for ev in evaluaciones:
        cm  = ev['codigo_materia']
        mom = ev['numero_momento']
        if cm not in notas_idx:
            notas_idx[cm] = {}
        notas_idx[cm][mom] = ev['nota']

    # ── 5. Calcular definitivas y promedio general ────────────────────
    detalles = []
    sum_definitivas = 0.0
    count_definitivas = 0
    materias_reprobadas = 0

    for mat in materias:
        cm = mat['codigo']
        nota_min = float(mat.get('nota_minima_aprobacion') or 10.0)
        n_notas = notas_idx.get(cm, {})

        n1 = n_notas.get(1)
        n2 = n_notas.get(2)
        n3 = n_notas.get(3)

        nota_final = _calcular_nota_final(
            n1, n2, n3,
            porcentajes[1], porcentajes[2], porcentajes[3]
        )

        resultado = _nota_resultado(nota_final, nota_min)
        if nota_final is not None:
            sum_definitivas  += nota_final
            count_definitivas += 1
            if resultado == 'R':
                materias_reprobadas += 1

        detalles.append({
            "codigo_materia":   cm,
            "nota_momento1":    n1,
            "nota_momento2":    n2,
            "nota_momento3":    n3,
            "nota_final":       nota_final,
            "resultado_materia": resultado,
            "es_revision":      False,
            "observaciones":    None,
        })

    promedio_general = round(sum_definitivas / count_definitivas, 2) if count_definitivas else 0.0
    resultado_final  = 'A' if materias_reprobadas == 0 and count_definitivas > 0 else 'R'

    # ── 6. Guardar boletin ────────────────────────────────────────────
    dato_boletin = {
        "cedula_estudiante":  cedula,
        "codigo_ano_escolar": ano,
        "codigo_seccion":     seccion,
        "numero_momento":     num_mom_int,
        "promedio_general":   promedio_general,
        "mencion":            None,
        "resultado_final":    resultado_final,
        "fecha_generacion":   hoy,
        "tipo_boletin":       tipo,
        "observaciones":      obs,
    }

    try:
        resp_bol = supabase.table("boletin").insert(dato_boletin).execute()
        boletin_id = resp_bol.data[0]['id']
    except Exception as e:
        flash(f"Error al guardar boletín: {str(e)}", "danger")
        return None

    # ── 7. Guardar detalle_boletin ────────────────────────────────────
    errores_det = 0
    for det in detalles:
        det['id_boletin'] = boletin_id
        try:
            supabase.table("detalle_boletin").insert(det).execute()
        except Exception:
            errores_det += 1

    if errores_det:
        flash(f"⚠ Boletín generado con {errores_det} materia(s) sin detalle. Promedio: {promedio_general}.", "warning")
    else:
        estado_txt = 'Aprobado' if resultado_final == 'A' else 'Reprobado'
        flash(f"✅ Boletín generado: {len(detalles)} materias | Promedio: {promedio_general} | {estado_txt}.", "success")
    return boletin_id


# ─── Vista de un boletín individual (imprimible) ─────────────────────────────

def boletin_ver_view(boletin_id):
    """
    Muestra el boletín individual en formato imprimible.
    """
    # ── Cargar boletín ────────────────────────────────────────────────
    try:
        resp_bol = supabase.table("boletin").select("*") \
            .eq("id", boletin_id).limit(1).execute()
        boletin = resp_bol.data[0] if resp_bol.data else None
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('boletines'))

    if not boletin:
        flash("Boletín no encontrado.", "danger")
        return redirect(url_for('boletines'))

    # ── Estudiante ────────────────────────────────────────────────────
    try:
        resp_est = supabase.table("estudiante").select("*") \
            .eq("cedula", boletin['cedula_estudiante']).limit(1).execute()
        estudiante = resp_est.data[0] if resp_est.data else {}
    except Exception:
        estudiante = {}

    # ── Sección y Grado ───────────────────────────────────────────────
    try:
        resp_sec = supabase.table("seccion").select(
            "letra, codigo_grado, turno, grado(nombre)"
        ).eq("codigo", boletin['codigo_seccion']).limit(1).execute()
        seccion_info = resp_sec.data[0] if resp_sec.data else {}
    except Exception:
        seccion_info = {}

    # ── Año escolar ───────────────────────────────────────────────────
    try:
        resp_ano = supabase.table("ano_escolar").select("codigo, descripcion") \
            .eq("codigo", boletin['codigo_ano_escolar']).limit(1).execute()
        ano_info = resp_ano.data[0] if resp_ano.data else {}
    except Exception:
        ano_info = {}

    # ── Institución ───────────────────────────────────────────────────
    try:
        resp_inst = supabase.table("institucion").select("*").limit(1).execute()
        institucion = resp_inst.data[0] if resp_inst.data else {}
    except Exception:
        institucion = {}

    # ── Detalles del boletín (materias y notas) ───────────────────────
    try:
        resp_det = supabase.table("detalle_boletin").select(
            "*, materia(nombre, abreviatura)"
        ).eq("id_boletin", boletin_id).execute()
        detalles = resp_det.data or []
    except Exception as e:
        flash(f"Error cargando detalles: {str(e)}", "danger")
        detalles = []

    # Ordenar detalles por nombre de materia
    detalles.sort(key=lambda d: (d.get('materia') or {}).get('nombre', ''))

    # Estadísticas del boletín
    total_materias   = len(detalles)
    aprobadas        = sum(1 for d in detalles if d.get('resultado_materia') == 'A')
    reprobadas       = total_materias - aprobadas

    # ── Momentos (para el encabezado de columnas) ─────────────────────
    try:
        resp_mom = supabase.table("momento_evaluativo").select("numero, nombre") \
            .order("numero").execute()
        momentos = resp_mom.data or []
    except Exception:
        momentos = [
            {"numero": 1, "nombre": "1er Momento"},
            {"numero": 2, "nombre": "2do Momento"},
            {"numero": 3, "nombre": "3er Momento"},
        ]

    return render_template(
        'evaluacion/boletin_ver.html',
        boletin       = boletin,
        estudiante    = estudiante,
        seccion_info  = seccion_info,
        ano_info      = ano_info,
        institucion   = institucion,
        detalles      = detalles,
        momentos      = momentos,
        total_materias = total_materias,
        aprobadas     = aprobadas,
        reprobadas    = reprobadas,
    )

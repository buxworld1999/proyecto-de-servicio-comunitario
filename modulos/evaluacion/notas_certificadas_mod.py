"""
notas_certificadas_mod.py — Certificación de Calificaciones Oficial (Formato MPPE)
PRISMA — Sistema de Gestión Escolar | Unidad Educativa Carmen Ruíz

Genera el documento oficial venezolano:
  - Certificación de Calificaciones EMG Código 31059
  - Certificación de Calificaciones EMG Mención Ciencia y Tecnología Código 31060

El documento replica fielmente el formato del Ministerio del Poder Popular para
la Educación, rellenando los datos del estudiante y sus calificaciones por año.

Tablas usadas:
  - estudiante, matricula, seccion, grado
  - evaluacion (notas por materia/año)
  - boletin, detalle_boletin (si se tiene boletín final)
  - institucion
"""

import hashlib
from datetime import date, datetime
from flask import render_template, request, redirect, url_for, flash, session, send_file
from db import supabase
from modulos.evaluacion.notas_xls_filler import llenar_xls_mppe


# ─── Constantes de conversión nota→letras ────────────────────────────────────

def nota_en_letras(nota: float) -> str:
    """
    Convierte una nota numérica (0-20) a su representación en letras
    según el sistema venezolano de educación media.
    """
    if nota is None:
        return ''
    n = round(float(nota))
    mapa = {
        20: 'VEINTE',
        19: 'DIECINUEVE',
        18: 'DIECIOCHO',
        17: 'DIECISIETE',
        16: 'DIECISÉIS',
        15: 'QUINCE',
        14: 'CATORCE',
        13: 'TRECE',
        12: 'DOCE',
        11: 'ONCE',
        10: 'DIEZ',
         9: 'NUEVE',
         8: 'OCHO',
         7: 'SIETE',
         6: 'SEIS',
         5: 'CINCO',
         4: 'CUATRO',
         3: 'TRES',
         2: 'DOS',
         1: 'UNO',
         0: 'CERO',
    }
    return mapa.get(n, str(n))


# ─── Mapeo de nombre de materia → área de formación del MPPE ─────────────────

# Este mapa relaciona nombres de materias tal como están en la BD
# con las "Áreas de Formación" exactas del formato MPPE.
# Se busca por coincidencia parcial (case-insensitive).
MAPA_AREA_31059 = {
    'castellano':          'Castellano',
    'lengua':              'Castellano',
    'inglés':              'Inglés y otras Lenguas Extranjeras',
    'ingles':              'Inglés y otras Lenguas Extranjeras',
    'idiomas':             'Inglés y otras Lenguas Extranjeras',
    'matemática':          'Matemáticas',
    'matematica':          'Matemáticas',
    'matemáticas':         'Matemáticas',
    'educación física':    'Educación Física',
    'educacion fisica':    'Educación Física',
    'arte':                'Arte y Patrimonio',
    'patrimonio':          'Arte y Patrimonio',
    'ciencias naturales':  'Ciencias Naturales',
    'ciencias de la tierra': 'Ciencias de la Tierra',
    'geografía':           'Geografía, Historia y Ciudadanía',
    'geografia':           'Geografía, Historia y Ciudadanía',
    'historia':            'Geografía, Historia y Ciudadanía',
    'ciudadanía':          'Geografía, Historia y Ciudadanía',
    'física':              'Física',
    'fisica':              'Física',
    'química':             'Química',
    'quimica':             'Química',
    'biología':            'Biología',
    'biologia':            'Biología',
    'soberanía':           'Formación para la Soberanía Nacional',
    'soberania':           'Formación para la Soberanía Nacional',
    'orientación':         'Orientación y Convivencia',
    'orientacion':         'Orientación y Convivencia',
}

MAPA_AREA_31060 = {
    'lengua':              'Lengua y Literatura',
    'castellano':          'Lengua y Literatura',
    'inglés':              'Idiomas',
    'ingles':              'Idiomas',
    'idiomas':             'Idiomas',
    'matemática':          'Matemática',
    'matematica':          'Matemática',
    'educación física':    'Educación Física',
    'educacion fisica':    'Educación Física',
    'biología':            'Biología, Ambiente y Tecnología',
    'biologia':            'Biología, Ambiente y Tecnología',
    'física':              'Física',
    'fisica':              'Física',
    'química':             'Química',
    'quimica':             'Química',
    'geografía':           'Geografía, Historia y Soberanía Nacional',
    'geografia':           'Geografía, Historia y Soberanía Nacional',
    'historia':            'Geografía, Historia y Soberanía Nacional',
    'soberanía':           'Geografía, Historia y Soberanía Nacional',
    'innovación':          'Innovación Tecnológica y Productiva',
    'orientación':         'Orientación Vocacional',
}


def _mapear_area(nombre_materia: str, tipo: str) -> str:
    """Convierte el nombre de materia de la BD al área de formación MPPE."""
    mapa = MAPA_AREA_31060 if tipo == '31060' else MAPA_AREA_31059
    n = nombre_materia.lower()
    for clave, area in mapa.items():
        if clave in n:
            return area
    # Fallback: devuelve el nombre tal cual (se mostrará en la tabla si no hay match)
    return nombre_materia


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _get_ano_activo():
    try:
        resp = supabase.table("ano_escolar").select("codigo") \
            .eq("activo", True).limit(1).execute()
        return resp.data[0]['codigo'] if resp.data else None
    except Exception:
        return None


def _generar_codigo_verificacion(cedula: str, ano: str) -> str:
    """Genera código de verificación único."""
    raw = f"{cedula}-{ano}-{datetime.now().timestamp()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12].upper()


# ─── Vista del historial / buscador ──────────────────────────────────────────

def notas_certificadas_view():
    """
    Permite buscar un estudiante y ver su historial académico.
    Muestra botones para emitir el certificado MPPE.
    """
    try:
        resp_anos = supabase.table("ano_escolar").select("codigo, descripcion") \
            .order("codigo", desc=True).execute()
        anos = resp_anos.data or []
    except Exception:
        anos = []

    ano_sel       = request.args.get('ano', _get_ano_activo() or '')
    cedula_buscar = request.args.get('cedula', '').strip()

    estudiante = None
    historial  = []
    matriculas = []

    if cedula_buscar:
        try:
            resp_est = supabase.table("estudiante").select("*") \
                .eq("cedula", cedula_buscar).limit(1).execute()
            if resp_est.data:
                estudiante = resp_est.data[0]
            else:
                flash(f"No se encontró estudiante con cédula '{cedula_buscar}'.", "warning")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")

        if estudiante:
            # Historial de matrículas
            try:
                resp_mat = supabase.table("matricula").select(
                    "id, codigo_ano_escolar, codigo_seccion, estado_matricula, "
                    "seccion(letra, codigo_grado, grado(nombre))"
                ).eq("cedula_estudiante", cedula_buscar) \
                 .order("codigo_ano_escolar", desc=True).execute()
                matriculas = resp_mat.data or []
            except Exception:
                pass

            # Boletines finales
            try:
                resp_bol = supabase.table("boletin").select("*") \
                    .eq("cedula_estudiante", cedula_buscar) \
                    .eq("tipo_boletin", "final") \
                    .order("codigo_ano_escolar", desc=True).execute()
                boletines_hist = resp_bol.data or []
            except Exception:
                boletines_hist = []

            for bol in boletines_hist:
                try:
                    resp_det = supabase.table("detalle_boletin").select("*, materia(nombre)") \
                        .eq("id_boletin", bol['id']).execute()
                    bol['detalles'] = resp_det.data or []
                except Exception:
                    bol['detalles'] = []
                historial.append(bol)

    return render_template(
        'evaluacion/notas_certificadas.html',
        anos          = anos,
        anos_lista    = anos,
        ano_sel       = ano_sel,
        cedula_buscar = cedula_buscar,
        estudiante    = estudiante,
        historial     = historial,
        matriculas    = matriculas,
    )


def _construir_notas_por_anio(cedula: str, tipo: str,
                              matriculas_hist: list,
                              evaluaciones: list,
                              detalles_boletin: list = None,
                              boletin_ano: str = None) -> dict:
    """
    Construye el diccionario {str(numero_ano): {area_mppe: nota}}
    a partir de los datos históricos del estudiante.
    Reutilizable en nota_certificada_ver_view y descargar_nota_xls_view.
    """
    from collections import defaultdict

    notas_por_anio = {}

    # ── Datos del boletín (tienen prioridad) ─────────────────────────
    if detalles_boletin and boletin_ano:
        boletin_mat = next(
            (m for m in matriculas_hist if m.get('codigo_ano_escolar') == boletin_ano), {}
        )
        sec_info  = boletin_mat.get('seccion') or {}
        grado_inf = sec_info.get('grado') or {}
        numero_ano_str = str(grado_inf.get('numero_ano', ''))

        if numero_ano_str:
            notas_por_anio[numero_ano_str] = {}
            for det in detalles_boletin:
                mat_info   = det.get('materia') or {}
                nombre_mat = mat_info.get('nombre', det.get('codigo_materia', ''))
                nota_final = det.get('nota_final')
                if nota_final is not None:
                    area_mppe = _mapear_area(nombre_mat, tipo)
                    notas_por_anio[numero_ano_str][area_mppe] = nota_final

    # ── Complementar con evaluaciones históricas directas ────────────
    ev_grouped = defaultdict(list)
    for ev in evaluaciones:
        key = (ev['codigo_ano_escolar'], ev['codigo_materia'])
        if ev.get('nota') is not None:
            ev_grouped[key].append(ev['nota'])

    for mat in matriculas_hist:
        ano_esc   = mat.get('codigo_ano_escolar', '')
        sec_info  = mat.get('seccion') or {}
        grado_inf = sec_info.get('grado') or {}
        num_ano   = grado_inf.get('numero_ano')

        if not num_ano:
            continue

        k = str(num_ano)
        if k not in notas_por_anio:
            notas_por_anio[k] = {}

        for (ae, cm), notas in ev_grouped.items():
            if ae != ano_esc:
                continue
            nota_prom = sum(notas) / len(notas)
            ev_mat = next((e for e in evaluaciones
                          if e['codigo_ano_escolar'] == ae
                          and e['codigo_materia'] == cm), None)
            if not ev_mat:
                continue
            mat_info_ev = ev_mat.get('materia') or {}
            nombre_mat  = mat_info_ev.get('nombre', cm)
            area_mppe   = _mapear_area(nombre_mat, tipo)

            if area_mppe not in notas_por_anio[k]:
                notas_por_anio[k][area_mppe] = round(nota_prom, 0)

    return notas_por_anio


# ─── Vista del Certificado Oficial (Formato MPPE) ────────────────────────────

def nota_certificada_ver_view():
    """
    Genera el documento oficial de Certificación de Calificaciones
    basado en el formato MPPE (Código 31059 o 31060).

    Parámetros GET:
      cedula     - Cédula del estudiante
      ano        - Año escolar (para filtrar datos actuales)
      boletin_id - ID de un boletín específico (opcional)
      tipo       - '31059' (EMG) o '31060' (EMGCT con mención C y T)
    """
    cedula     = request.args.get('cedula', '').strip()
    ano        = request.args.get('ano', '').strip()
    boletin_id = request.args.get('boletin_id', '').strip()
    tipo       = request.args.get('tipo', '31059')  # '31059' o '31060'

    if not cedula:
        flash("Cédula del estudiante requerida.", "warning")
        return redirect(url_for('notas_certificadas'))

    # ── 1. Estudiante ─────────────────────────────────────────────────
    try:
        resp_est = supabase.table("estudiante").select("*") \
            .eq("cedula", cedula).limit(1).execute()
        estudiante = resp_est.data[0] if resp_est.data else None
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('notas_certificadas'))

    if not estudiante:
        flash("Estudiante no encontrado.", "danger")
        return redirect(url_for('notas_certificadas'))

    # ── 2. Institución ────────────────────────────────────────────────
    try:
        resp_inst = supabase.table("institucion").select("*").limit(1).execute()
        institucion = resp_inst.data[0] if resp_inst.data else {}
    except Exception:
        institucion = {}

    # ── 3. Año escolar ────────────────────────────────────────────────
    try:
        resp_ano = supabase.table("ano_escolar").select("*") \
            .eq("codigo", ano).limit(1).execute()
        ano_info = resp_ano.data[0] if resp_ano.data else {"codigo": ano}
    except Exception:
        ano_info = {"codigo": ano}

    # ── 4. Matrículas históricas ──────────────────────────────────────
    try:
        resp_mats = supabase.table("matricula").select(
            "codigo_ano_escolar, codigo_seccion, "
            "seccion(letra, codigo_grado, grado(nombre, numero_ano))"
        ).eq("cedula_estudiante", cedula) \
         .order("codigo_ano_escolar").execute()
        matriculas_hist = resp_mats.data or []
    except Exception:
        matriculas_hist = []

    matricula_info = next(
        (m for m in matriculas_hist if m.get('codigo_ano_escolar') == ano),
        matriculas_hist[0] if matriculas_hist else {}
    )

    # ── 5. Evaluaciones históricas ────────────────────────────────────
    try:
        resp_ev = supabase.table("evaluacion").select(
            "codigo_materia, codigo_ano_escolar, numero_momento, nota, "
            "materia(nombre, codigo_grado, grado(numero_ano))"
        ).eq("cedula_estudiante", cedula).execute()
        evaluaciones = resp_ev.data or []
    except Exception:
        evaluaciones = []

    # ── 6. Detalles de boletín (si existe) ───────────────────────────
    detalles_boletin = []
    if boletin_id:
        try:
            resp_det = supabase.table("detalle_boletin").select(
                "*, materia(nombre, codigo_grado, grado(numero_ano))"
            ).eq("id_boletin", int(boletin_id)).execute()
            detalles_boletin = resp_det.data or []
        except Exception:
            pass

    # ── 7. Construir notas_por_anio ───────────────────────────────────
    notas_por_anio = _construir_notas_por_anio(
        cedula, tipo, matriculas_hist, evaluaciones,
        detalles_boletin=detalles_boletin,
        boletin_ano=ano
    )

    # ── 8. Observaciones ──────────────────────────────────────────────
    observaciones = ''
    if boletin_id:
        try:
            resp_bol = supabase.table("boletin").select("observaciones") \
                .eq("id", int(boletin_id)).limit(1).execute()
            if resp_bol.data:
                observaciones = resp_bol.data[0].get('observaciones') or ''
        except Exception:
            pass

    # ── 9. Metadatos del documento ────────────────────────────────────
    codigo_verificacion = _generar_codigo_verificacion(cedula, ano)
    fecha_emision       = date.today().strftime('%d de %B de %Y').capitalize()
    emisor_nombre       = session.get('nombre', 'Secretaría')

    return render_template(
        'evaluacion/nota_certificada_ver.html',
        estudiante          = estudiante,
        ano_info            = ano_info,
        institucion         = institucion,
        matricula_info      = matricula_info,
        notas_por_anio      = notas_por_anio,
        observaciones       = observaciones,
        codigo_verificacion = codigo_verificacion,
        fecha_emision       = fecha_emision,
        emisor_nombre       = emisor_nombre,
        tipo                = tipo,
        nota_en_letras      = nota_en_letras,   # Función disponible en Jinja2
    )


def descargar_nota_xls_view():
    """
    Genera y descarga el archivo .xls rellenado con los datos del estudiante
    y sus notas históricas reales usando llenar_xls_mppe.
    """
    cedula     = request.args.get('cedula', '').strip()
    ano        = request.args.get('ano', '').strip()
    tipo       = request.args.get('tipo', '31059')

    if not cedula:
        flash("Cédula del estudiante requerida para descargar el formato.", "warning")
        return redirect(url_for('notas_certificadas'))

    # ── 1. Estudiante ─────────────────────────────────────────────────
    try:
        resp_est = supabase.table("estudiante").select("*") \
            .eq("cedula", cedula).limit(1).execute()
        estudiante = resp_est.data[0] if resp_est.data else None
    except Exception:
        estudiante = None

    if not estudiante:
        flash("Estudiante no encontrado.", "danger")
        return redirect(url_for('notas_certificadas'))

    # ── 2. Institución ────────────────────────────────────────────────
    try:
        resp_inst = supabase.table("institucion").select("*").limit(1).execute()
        institucion = resp_inst.data[0] if resp_inst.data else {}
    except Exception:
        institucion = {}

    # ── 3. Matrículas históricas ──────────────────────────────────────
    try:
        resp_mats = supabase.table("matricula").select(
            "codigo_ano_escolar, codigo_seccion, "
            "seccion(letra, codigo_grado, grado(nombre, numero_ano))"
        ).eq("cedula_estudiante", cedula) \
         .order("codigo_ano_escolar").execute()
        matriculas_hist = resp_mats.data or []
    except Exception:
        matriculas_hist = []

    # ── 4. Evaluaciones históricas ────────────────────────────────────
    try:
        resp_ev = supabase.table("evaluacion").select(
            "codigo_materia, codigo_ano_escolar, numero_momento, nota, "
            "materia(nombre, codigo_grado, grado(numero_ano))"
        ).eq("cedula_estudiante", cedula).execute()
        evaluaciones = resp_ev.data or []
    except Exception:
        evaluaciones = []

    # ── 5. Construir notas_por_anio reales ────────────────────────────
    notas_por_anio = _construir_notas_por_anio(
        cedula, tipo, matriculas_hist, evaluaciones
    )

    # ── 6. Generar XLS buffer ─────────────────────────────────────────
    try:
        buf, nombre_archivo = llenar_xls_mppe(
            tipo, estudiante, institucion, notas_por_anio
        )
        nombre_descarga = f"Notas_Certificadas_{tipo}_{cedula}.xls"
        return send_file(
            buf,
            as_attachment=True,
            download_name=nombre_descarga,
            mimetype='application/vnd.ms-excel'
        )
    except Exception as e:
        flash(f"Error generando el formato XLS: {e}", "danger")
        return redirect(url_for('notas_certificadas'))

"""
carga_masiva_notas.py — Carga Masiva de Notas por Excel
PRISMA — Sistema de Gestión Escolar | Unidad Educativa Carmen Ruíz

Flujo:
  1. Admin/Docente sube un .xlsx con columnas: Cédula, Apellidos, Nombres, Nota
  2. Selecciona: Año Escolar, Sección, Materia, Momento Evaluativo
  3. El motor parsea el Excel y mapea los datos
  4. Por cada fila, busca al estudiante matriculado en esa sección/año por cédula
  5. Hace upsert en la tabla 'evaluacion' de Supabase
  6. Retorna resumen: insertadas, actualizadas, no encontradas, errores
"""

from datetime import date
from flask import render_template, request, redirect, url_for, flash, session
import re
from db import supabase
from modulos.evaluacion.notas_excel_parser import NotasExcelParser
from modulos.evaluacion.sabana_excel_parser import SabanaExcelParser


def _get_ano_activo():
    try:
        resp = supabase.table("ano_escolar").select("codigo") \
            .eq("activo", True).limit(1).execute()
        return resp.data[0]['codigo'] if resp.data else None
    except Exception:
        return None


def _get_cedula_personal():
    cedula = session.get('cedula_personal')
    if cedula:
        return cedula
    try:
        resp = supabase.table("usuario").select("cedula_personal") \
            .eq("id", session.get('usuario_id')).limit(1).execute()
        if resp.data:
            return resp.data[0].get('cedula_personal')
    except Exception:
        pass
    return None


def _nota_resultado(nota: float, nota_min: float = 10.0) -> str:
    return 'A' if nota >= nota_min else 'R'


def carga_masiva_notas_view():
    """
    Vista principal de Carga Masiva de Notas por Excel.
    GET  → formulario de selección y drop zone de archivo
    POST → parsea Excel, valida y hace upsert en tabla 'evaluacion'
    """

    # ── Cargar selectores ─────────────────────────────────────────────
    try:
        resp_anos = supabase.table("ano_escolar").select("codigo, descripcion, activo") \
            .order("codigo", desc=True).execute()
        anos = resp_anos.data or []
    except Exception:
        anos = []

    try:
        resp_sec = supabase.table("seccion").select("codigo, letra, codigo_grado, codigo_ano_escolar") \
            .order("codigo").execute()
        secciones_todas = resp_sec.data or []
    except Exception:
        secciones_todas = []

    try:
        resp_mat = supabase.table("materia").select("codigo, nombre, nota_minima_aprobacion, codigo_grado") \
            .eq("estado", "A").order("nombre").execute()
        materias = resp_mat.data or []
    except Exception:
        materias = []

    try:
        resp_mom = supabase.table("momento_evaluativo").select("numero, nombre, estado") \
            .order("numero").execute()
        momentos = resp_mom.data or []
    except Exception:
        momentos = []

    if not momentos:
        momentos = [
            {"numero": 1, "nombre": "Primer Momento",  "estado": "A"},
            {"numero": 2, "nombre": "Segundo Momento", "estado": "A"},
            {"numero": 3, "nombre": "Tercer Momento",  "estado": "A"},
        ]

    ano_sel = request.args.get('ano', _get_ano_activo() or '')
    secciones = [s for s in secciones_todas if s.get('codigo_ano_escolar') == ano_sel]

    # ── GET: mostrar formulario ───────────────────────────────────────
    if request.method != 'POST':
        return render_template(
            'carga_masiva_notas.html',
            anos=anos, secciones=secciones, materias=materias, momentos=momentos,
            ano_sel=ano_sel, secciones_todas=secciones_todas,
        )

    # ── POST: procesar archivo ────────────────────────────────────────
    archivo = request.files.get('archivo_excel')
    tipo_carga   = request.form.get('tipo_carga', 'simple').strip()
    ano_form     = request.form.get('ano_escolar', '').strip()
    seccion_form = request.form.get('codigo_seccion', '').strip()
    materia_form = request.form.get('codigo_materia', '').strip() if tipo_carga == 'simple' else 'MULTIPLE'
    momento_form = request.form.get('numero_momento', '').strip()

    # Validaciones básicas
    if not archivo or archivo.filename == '':
        flash("Debes subir un archivo Excel.", "warning")
        return redirect(url_for('carga_masiva_notas', ano=ano_form))

    if not archivo.filename.lower().endswith(('.xlsx', '.xls')):
        flash("Solo se aceptan archivos .xlsx o .xls", "danger")
        return redirect(url_for('carga_masiva_notas', ano=ano_form))

    if not all([ano_form, seccion_form, momento_form]) or (tipo_carga == 'simple' and not materia_form):
        flash("Debes seleccionar Año Escolar, Sección, Materia y Momento.", "warning")
        return redirect(url_for('carga_masiva_notas', ano=ano_form))

    try:
        num_momento = int(momento_form)
    except ValueError:
        flash("Momento inválido.", "danger")
        return redirect(url_for('carga_masiva_notas', ano=ano_form))

    # Verificar que el momento esté abierto
    mom_check = next((m for m in momentos if m['numero'] == num_momento), None)
    if mom_check and mom_check.get('estado') == 'C':
        flash("Este momento evaluativo está CERRADO. No se pueden cargar notas.", "warning")
        return redirect(url_for('carga_masiva_notas', ano=ano_form))

    # Nota mínima de aprobación de la materia
    mat_info = next((m for m in materias if m['codigo'] == materia_form), None)
    nota_min = float(mat_info.get('nota_minima_aprobacion') or 10.0) if mat_info else 10.0

    # ── 1. Parsear Excel ──────────────────────────────────────────────
    try:
        if tipo_carga == 'sabana':
            resultado_dict = SabanaExcelParser.parse(archivo)
            if "error" in resultado_dict:
                flash(f"Error en Sábana MPPE: {resultado_dict['error']}", "danger")
                return redirect(url_for('carga_masiva_notas', ano=ano_form))
            registros = resultado_dict.get('estudiantes', [])
            diagnostico = resultado_dict.get('diagnostico', {})
        else:
            parser = NotasExcelParser(archivo)
            resultado = parser.parse()
            registros = resultado.registros
            diagnostico = resultado.diagnostico
    except Exception as e:
        flash(f"Error crítico al leer el archivo: {str(e)}", "danger")
        return redirect(url_for('carga_masiva_notas', ano=ano_form))

    if not registros:
        flash("El motor no encontró registros de notas en el archivo.", "danger")
        return render_template(
            'carga_masiva_notas.html',
            anos=anos, secciones=secciones, materias=materias, momentos=momentos,
            ano_sel=ano_form, secciones_todas=secciones_todas,
            procesado=True,
            diagnostico=diagnostico,
            insertadas=[], actualizadas=[], no_encontradas=[], errores=[],
        )

    # ── 2. Cargar lista de matriculados en esa sección/año ────────────
    try:
        resp_mat_est = supabase.table("matricula").select(
            "cedula_estudiante, numero_lista, estudiante(nombres, apellidos)"
        ).eq("codigo_seccion", seccion_form) \
         .eq("codigo_ano_escolar", ano_form) \
         .eq("estado_matricula", 'A').execute()
        matriculados = {
            m['cedula_estudiante']: m for m in (resp_mat_est.data or [])
        }
    except Exception as e:
        flash(f"Error cargando lista de matriculados: {str(e)}", "danger")
        return redirect(url_for('carga_masiva_notas', ano=ano_form))

    # ── 3. Cargar evaluaciones existentes ─────────────────────────────
    # Si es carga simple, cargamos solo de esa materia. Si es sábana, cargamos todas las materias del momento.
    try:
        query_ev = supabase.table("evaluacion").select(
            "id, cedula_estudiante, codigo_materia"
        ).eq("codigo_ano_escolar", ano_form).eq("numero_momento", num_momento)
        
        if tipo_carga == 'simple':
            query_ev = query_ev.eq("codigo_materia", materia_form)
            
        resp_ev = query_ev.execute()
        
        eval_existentes = {} # {(cedula, codigo_materia): id}
        for e in (resp_ev.data or []):
            eval_existentes[(e['cedula_estudiante'], e['codigo_materia'])] = e['id']
    except Exception as e:
        eval_existentes = {}

    # ── 4. Procesar cada registro del Excel ───────────────────────────
    cedula_personal = _get_cedula_personal()
    hoy = date.today().isoformat()

    insertadas    = []
    actualizadas  = []
    no_encontradas = []
    errores       = []

    for reg in registros:
        cedula = reg.get('cedula', '')
        
        # Obtener lista de notas a procesar (si es simple es 1, si es sábana pueden ser 10)
        notas_a_procesar = [] # list of (codigo_materia, nota_valor)
        if tipo_carga == 'sabana':
            for cod_mat, val in reg.get('notas', {}).items():
                notas_a_procesar.append((cod_mat, val))
        else:
            notas_a_procesar.append((materia_form, reg.get('nota')))

        if not cedula:
            no_encontradas.append({
                'fila':      reg.get('fila_excel'),
                'nombre':    reg.get('nombre_completo') or f"{reg.get('apellidos','')} {reg.get('nombres','')}",
                'motivo':    'Sin cédula detectada en el Excel',
            })
            continue

        if not notas_a_procesar or all(nota is None for _, nota in notas_a_procesar):
            errores.append({
                'fila':   reg.get('fila_excel'),
                'cedula': cedula,
                'nombre': reg.get('nombre_completo', ''),
                'motivo': reg.get('advertencias', ['Sin nota'])[0] if reg.get('advertencias') else 'Sin nota',
            })
            continue

        # Verificar que el estudiante esté matriculado en esa sección
        if cedula not in matriculados:
            no_encontradas.append({
                'fila':   reg.get('fila_excel'),
                'nombre': reg.get('nombre_completo') or f"{reg.get('apellidos','')} {reg.get('nombres','')}",
                'cedula': cedula,
                'motivo': 'No está matriculado en la sección seleccionada',
            })
            continue

        mat_estu = matriculados[cedula]
        est_info = mat_estu.get('estudiante') or {}
        nombre_completo = f"{est_info.get('apellidos','').strip()} {est_info.get('nombres','').strip()}".strip()

        # Procesar cada materia para este estudiante
        for cod_materia, nota in notas_a_procesar:
            if nota is None:
                continue
                
            # Buscar nota mínima para la materia específica (si no se encuentra, 10.0 por defecto)
            mat_obj = next((m for m in materias if m['codigo'] == cod_materia), None)
            nota_min_local = float(mat_obj.get('nota_minima_aprobacion') or 10.0) if mat_obj else nota_min
            resultado_nota = _nota_resultado(nota, nota_min_local)

            dato = {
                "cedula_estudiante":        cedula,
                "codigo_materia":           cod_materia,
                "codigo_ano_escolar":       ano_form,
                "numero_momento":           num_momento,
                "nota":                     nota,
                "resultado":                resultado_nota,
                "fecha_evaluacion":         hoy,
                "cedula_docente_evaluador": cedula_personal,
            }

            try:
                ev_id = eval_existentes.get((cedula, cod_materia))
                if ev_id:
                    dato['fecha_modificacion'] = hoy
                    supabase.table("evaluacion").update(dato).eq("id", ev_id).execute()
                    actualizadas.append({
                        'cedula': cedula,
                        'nombre': nombre_completo,
                        'nota':   nota,
                        'resultado': resultado_nota,
                        'materia': cod_materia
                    })
                else:
                    supabase.table("evaluacion").insert(dato).execute()
                    insertadas.append({
                        'cedula': cedula,
                        'nombre': nombre_completo,
                        'nota':   nota,
                        'resultado': resultado_nota,
                        'materia': cod_materia
                    })
            except Exception as e:
                errores.append({
                    'fila':   reg.get('fila_excel'),
                    'cedula': cedula,
                    'nombre': nombre_completo,
                    'motivo': f"Error Supabase en {cod_materia}: {str(e)}",
                })

    # ── 5. Nombre de la materia y sección para el resumen ─────────────
    materia_nombre = "Múltiples (Sábana)" if tipo_carga == 'sabana' else (mat_info.get('nombre') if mat_info else materia_form)
    mom_info = mom_check if mom_check else {}
    momento_nombre = mom_info.get('nombre', f"Momento {num_momento}")

    return render_template(
        'carga_masiva_notas.html',
        anos=anos, secciones=secciones, materias=materias, momentos=momentos,
        ano_sel=ano_form, secciones_todas=secciones_todas,
        procesado=True,
        seccion_sel=seccion_form,
        materia_nombre=materia_nombre,
        momento_nombre=momento_nombre,
        insertadas=insertadas,
        actualizadas=actualizadas,
        no_encontradas=no_encontradas,
        errores=errores,
        total_insertadas=len(insertadas),
        total_actualizadas=len(actualizadas),
        total_no_encontradas=len(no_encontradas),
        total_errores=len(errores),
        diagnostico=diagnostico,
    )

"""
momentos_evaluativos.py — Gestión de Momentos Evaluativos (Lapsos)
PRISMA — Sistema de Gestión Escolar | Unidad Educativa Carmen Ruíz

Controla los tres momentos de evaluación del año escolar:
  - Primer Momento (Lapso 1)
  - Segundo Momento (Lapso 2)
  - Tercer Momento (Lapso 3)

Tabla: momento_evaluativo(numero PK, codigo_ano_escolar, nombre,
       fecha_inicio, fecha_fin, porcentaje, estado, observaciones)
"""

from flask import render_template, request, redirect, url_for, flash
from db import supabase


def momentos_view():
    """
    Controlador de momentos evaluativos.
    GET  → muestra los 3 momentos del año activo.
    POST → crea/actualiza momentos o cambia su estado (Abierto/Cerrado).
    """
    # ── 1. Cargar años escolares ──────────────────────────────────────
    try:
        resp_anos = supabase.table("ano_escolar") \
            .select("codigo, descripcion, activo") \
            .order("codigo", desc=True).execute()
        anos = resp_anos.data or []
    except Exception as e:
        flash(f"Error cargando años escolares: {str(e)}", "danger")
        anos = []

    # Año por defecto: el activo, o el primero de la lista
    ano_sel = (
        request.args.get('ano')
        or next((a['codigo'] for a in anos if a.get('activo')), '')
        or (anos[0]['codigo'] if anos else '')
    )

    # ── 2. Cargar momentos del año seleccionado ───────────────────────
    momentos_raw = []
    if ano_sel:
        try:
            resp_m = supabase.table("momento_evaluativo") \
                .select("*") \
                .eq("codigo_ano_escolar", ano_sel) \
                .order("numero").execute()
            momentos_raw = resp_m.data or []
        except Exception as e:
            flash(f"Error cargando momentos: {str(e)}", "danger")

    # Construir dict indexado por numero para fácil acceso en template
    momentos_dict = {m['numero']: m for m in momentos_raw}

    # ── 3. Manejar POST ───────────────────────────────────────────────
    if request.method == 'POST':
        accion    = request.form.get('accion', '')
        ano_form  = request.form.get('codigo_ano_escolar', ano_sel)

        # ── Acción: guardar configuración de los 3 momentos ──────────
        if accion == 'guardar':
            errores = 0
            for num in [1, 2, 3]:
                nombre  = (request.form.get(f'nombre_{num}') or f'Momento {num}').strip()
                fi      = request.form.get(f'fecha_inicio_{num}') or None
                ff      = request.form.get(f'fecha_fin_{num}') or None
                obs     = request.form.get(f'observaciones_{num}') or None
                try:
                    porc = float(request.form.get(f'porcentaje_{num}', '33.33'))
                except ValueError:
                    porc = 33.33

                dato = {
                    "numero":              num,
                    "codigo_ano_escolar":  ano_form,
                    "nombre":              nombre,
                    "fecha_inicio":        fi,
                    "fecha_fin":           ff,
                    "porcentaje":          porc,
                    "estado":              "A",     # Abierto por defecto al crear
                    "observaciones":       obs,
                }
                try:
                    # upsert: inserta si no existe, actualiza si ya existe (PK = numero)
                    supabase.table("momento_evaluativo").upsert(dato).execute()
                except Exception as e:
                    flash(f"Error al guardar Momento {num}: {str(e)}", "danger")
                    errores += 1

            if not errores:
                flash("Momentos evaluativos configurados exitosamente.", "success")

        # ── Acción: cambiar estado Abierto/Cerrado ────────────────────
        elif accion == 'cambiar_estado':
            try:
                num           = int(request.form.get('numero'))
                estado_actual = request.form.get('estado_actual', 'A')
                nuevo_estado  = 'C' if estado_actual == 'A' else 'A'
                supabase.table("momento_evaluativo") \
                    .update({"estado": nuevo_estado}) \
                    .eq("numero", num).execute()
                txt = "cerrado" if nuevo_estado == 'C' else "reabierto"
                flash(f"Momento {num} {txt} correctamente.", "success")
            except Exception as e:
                flash(f"Error al cambiar estado: {str(e)}", "danger")

        return redirect(url_for('momentos', ano=ano_form))

    # ── 4. Estadísticas rápidas ───────────────────────────────────────
    total_abiertos  = sum(1 for m in momentos_raw if m.get('estado') == 'A')
    total_cerrados  = sum(1 for m in momentos_raw if m.get('estado') == 'C')

    return render_template(
        'momentos.html',
        anos             = anos,
        momentos_dict    = momentos_dict,
        momentos_raw     = momentos_raw,
        ano_seleccionado = ano_sel,
        total_abiertos   = total_abiertos,
        total_cerrados   = total_cerrados,
    )

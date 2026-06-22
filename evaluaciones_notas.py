from flask import render_template, request, redirect, url_for, flash
from db import supabase
import re

def evaluaciones_view():
    """
    Controlador oficial potenciado para el módulo de Calificaciones (Solo Secundaria).
    Procesa altas, bajas, modificaciones (CRUD completo) con bypass de metadatos en observaciones.
    """
    # === 1. DETECTAR ELIMINACIÓN POR URL===
    action = request.args.get('action')
    id_nota = request.args.get('id')
    
    if action == 'eliminar' and id_nota:
        try:
            supabase.table("evaluacion").delete().eq("id", id_nota).execute()
            flash("Calificación eliminada exitosamente del sistema.", "success")
        except Exception as e:
            flash(f"No se pudo eliminar la calificación: {str(e)}", "error")
        return redirect(url_for('evaluaciones'))

    # === 2. PROCESAR INSCRIPCIÓN O EDICIÓN DE NOTAS (POST) ===
    if request.method == 'POST':
        id_nota_edit = request.form.get('id_nota') # Si existe, estamos Editando buuuuu
        cedula_estudiante = request.form.get('cedula_estudiante')
        codigo_ano_escolar = request.form.get('codigo_ano_escolar')
        numero_momento = request.form.get('numero_momento')
        fecha_evaluacion = request.form.get('fecha_evaluacion')
        observaciones_raw = request.form.get('observaciones') or ''
        cedula_docente_evaluador = request.form.get('cedula_docente_evaluador')
        ano_estudiante = request.form.get('ano_estudiante')
        tipo_nota = request.form.get('tipo_nota')

        try:
            momento_int = int(numero_momento) if numero_momento else 1
            materia_seleccionada = request.form.get('codigo_materia_secundaria')
            
            if materia_seleccionada == 'MANUAL':
                codigo_materia = request.form.get('codigo_materia_secundaria_manual')
            else:
                codigo_materia = materia_seleccionada

            nota_str = request.form.get('nota_numerica')
            nota_float = float(nota_str) if nota_str else 0.0
            
            resultado = 'A' if nota_float >= 10.0 else 'R'
            es_revision = True if tipo_nota == 'REVISION' else False

            meta_tag = f"[META:{tipo_nota}:{ano_estudiante}]"
            observaciones_con_meta = f"{observaciones_raw} {meta_tag}".strip()

            payload_nota = {
                "cedula_estudiante": cedula_estudiante if cedula_estudiante else None,
                "codigo_materia": codigo_materia if codigo_materia else None,
                "codigo_ano_escolar": codigo_ano_escolar if codigo_ano_escolar else None,
                "numero_momento": momento_int,
                "nota": nota_float,
                "resultado": resultado,
                "fecha_evaluacion": fecha_evaluacion if fecha_evaluacion else None,
                "cedula_docente_evaluador": cedula_docente_evaluador if cedula_docente_evaluador else None,
                "observaciones": observaciones_con_meta,
                "es_revision": es_revision,
                "tipo_nota": tipo_nota,
                "ano_estudiante": ano_estudiante
            }

            if id_nota_edit:
                # Flujo de Actualización (Update)
                try:
                    supabase.table("evaluacion").update(payload_nota).eq("id", id_nota_edit).execute()
                except Exception:
                    # Fallback de seguridad: borramos las columnas fantasmas pero conservamos el tag en observaciones
                    if "tipo_nota" in payload_nota: del payload_nota["tipo_nota"]
                    if "ano_estudiante" in payload_nota: del payload_nota["ano_estudiante"]
                    supabase.table("evaluacion").update(payload_nota).eq("id", id_nota_edit).execute()
                flash("Calificación corregida y actualizada con éxito.", "success")
            else:
                # Flujo de Inserción Nueva (Insert)
                try:
                    supabase.table("evaluacion").insert(payload_nota).execute()
                except Exception:
                    if "tipo_nota" in payload_nota: del payload_nota["tipo_nota"]
                    if "ano_estudiante" in payload_nota: del payload_nota["ano_estudiante"]
                    supabase.table("evaluacion").insert(payload_nota).execute()
                flash("Calificación guardada exitosamente en el sistema.", "success")

        except Exception as e:
            flash(f"Error al procesar la calificación: {str(e)}", "error")

        return redirect(url_for('evaluaciones'))

    # === 3. CARGA Y TRADUCCIÓN DEL HISTORIAL HISTÓRICO (GET) ===
    mapa_materias = {
        "MAT1": "Matemáticas", "CAST1": "Castellano", "ING1": "Inglés y otras Lenguas", "EDFI1": "Educación Física", "ARTE1": "Arte y Patrimonio", "CNAT1": "Ciencias Naturales", "GHC1": "Geografía, Historia y Ciudadanía", "OC1": "Orientación y Convivencia", "GCRP1": "Grupos de Creación...",
        "MAT2": "Matemáticas", "CAST2": "Castellano", "ING2": "Inglés y otras Lenguas", "EDFI2": "Educación Física", "ARTE2": "Arte y Patrimonio", "CNAT2": "Ciencias Naturales", "GHC2": "Geografía, Historia y Ciudadanía", "OC2": "Orientación y Convivencia", "GCRP2": "Grupos de Creación...",
        "MAT3": "Matemáticas", "CAST3": "Castellano", "ING3": "Inglés y otras Lenguas", "EDFI3": "Educación Física", "FIS3": "Física", "QUI3": "Química", "BIO3": "Biología", "GHC3": "Geografía, Historia y Ciudadanía", "OC3": "Orientación y Convivencia", "GCRP3": "Grupos de Creación...",
        "MAT4": "Matemáticas", "CAST4": "Castellano", "ING4": "Inglés y otras Lenguas", "EDFI4": "Educación Física", "FIS4": "Física", "QUI4": "Química", "BIO4": "Biología", "GHC4": "Geografía, Historia y Ciudadanía", "FSN4": "Soberanía Nacional", "OC4": "Orientación y Convivencia", "GCRP4": "Grupos de Creación...",
        "MAT5": "Matemáticas", "CAST5": "Castellano", "ING5": "Inglés y otras Lenguas", "EDFI5": "Educación Física", "FIS5": "Física", "QUI5": "Química", "BIO5": "Biología", "CT5": "Ciencias de la Tierra", "GHC5": "Geografía, Historia y Ciudadanía", "FSN5": "Soberanía Nacional", "OC5": "Orientación y Convivencia", "GCRP5": "Grupos de Creación..."
    }

    try:
        respuesta = supabase.table("evaluacion").select("*").execute()
        notas_registradas = respuesta.data
        
        if notas_registradas:
            # Ordenamos por cédula y luego por momento
            notas_registradas.sort(key=lambda x: (x.get('cedula_estudiante', ''), x.get('numero_momento', 1)))
            
            # LÓGICA RECONSTRUCTORA POST-FETCH
            for cal in notas_registradas:
                obs = cal.get('observaciones') or ''
                tipo_nota_deducido = None
                ano_estudiante_deducido = None
                
                # Intentar extraer los metadatos guardados clandestinamente dentro de observaciones
                match = re.search(r'\[META:(.*?):(.*?)\]', obs)
                if match:
                    tipo_nota_deducido = match.group(1)
                    ano_estudiante_deducido = match.group(2)
                    # Limpiar las observaciones para remover el tag feo de la vista pública
                    cal['observaciones'] = re.sub(r'\s*\[META:.*?\]', '', obs).strip()
                
                # Inyectar propiedades en el objeto final para que Jinja las lea sin enterarse de la limitación física
                if tipo_nota_deducido:
                    cal['tipo_nota'] = tipo_nota_deducido
                elif not cal.get('tipo_nota'):
                    cal['tipo_nota'] = 'REVISION' if cal.get('es_revision') else 'REGULAR'
                    
                if ano_estudiante_deducido:
                    cal['ano_estudiante'] = ano_estudiante_deducido
                elif not cal.get('ano_estudiante'):
                    digitos = re.findall(r'\d', cal.get('codigo_materia', ''))
                    cal['ano_estudiante'] = digitos[-1] if digitos else "1"
            
    except Exception as e:
        notas_registradas = []
        flash(f"Error al conectar con la base de datos: {str(e)}", "error")

    return render_template('evaluacion/evaluaciones_notas.html', calificaciones=notas_registradas, mapa_materias=mapa_materias)
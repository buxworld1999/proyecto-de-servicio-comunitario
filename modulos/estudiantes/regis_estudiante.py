from flask import render_template, request, redirect, url_for, flash, send_file
import io
import pandas as pd

# Importar supabase desde db.py — sin importaciones circulares
from db import supabase


def registro_estudiantes():
    """
    Ruta: Captura el formulario completo y registra un estudiante
    en la tabla 'estudiante' de Supabase controlando longitudes bpchar.
    """
    if request.method == 'POST':
        # Captura y normalización estricta a 1 carácter para evitar el error 22001
        v_genero = request.form.get('genero', 'M')
        genero_filtrado = v_genero.strip().upper()[0] if v_genero else 'M'
        
        v_estado = request.form.get('estado_estudiante', 'A')
        estado_filtrado = v_estado.strip().upper()[0] if v_estado else 'A'

        # Recopilación estructurada mapeando el esquema de la base de datos
        datos_estudiante = {
            # 1. Identificación y Personales Básicos
            "cedula": request.form.get('cedula'),
            "nacionalidad": request.form.get('nacionalidad'),
            "nombres": request.form.get('nombres'),
            "apellidos": request.form.get('apellidos'),
            "genero": genero_filtrado,
            
            # 2. Información de Nacimiento
            "fecha_nacimiento": request.form.get('fecha_nacimiento') or None,
            "lugar_nacimiento": request.form.get('lugar_nacimiento') or None,
            "estado_nacimiento": request.form.get('estado_nacimiento') or None,
            "municipio_nacimiento": request.form.get('municipio_nacimiento') or None,
            
            # 3. Contacto y Ubicación
            "direccion": request.form.get('direccion') or None,
            "telefono": request.form.get('telefono') or None,
            "correo": request.form.get('correo') or None,
            
            # 4. Datos Antropométricos y Salud (Convertidos a float o None)
            "estatura": float(request.form.get('estatura')) if request.form.get('estatura') else None,
            "peso": float(request.form.get('peso')) if request.form.get('peso') else None,
            "talla_camisa": request.form.get('talla_camisa') or None,
            "talla_pantalon": request.form.get('talla_pantalon') or None,
            "talla_zapatos": request.form.get('talla_zapatos') or None,
            "condiciones_medicas": request.form.get('conditions_medicas') or None,
            "medicamentos": request.form.get('medicamentos') or None,
            
            # 5. Historial Académico, Año, Sección y Estado
            "plantel_procedencia": request.form.get('plantel_procedencia') or None,
            "fecha_ingreso": request.form.get('fecha_ingreso') or None,
            "anio": request.form.get('anio'),
            "seccion": request.form.get('seccion'),
            "estado_estudiante": estado_filtrado,
            "fecha_retiro": request.form.get('fecha_retiro') or None,
            "motivo_retiro": request.form.get('motivo_retiro') or None
        }

        try:
            # Inserción en la tabla de Supabase
            response = supabase.table("estudiante").insert(datos_estudiante).execute()
            flash(f"Estudiante {datos_estudiante['nombres']} {datos_estudiante['apellidos']} guardado de forma exitosa.", "success")
        except Exception as e:
            flash(f"Error al registrar estudiante: {str(e)}", "danger")
            
        return redirect(url_for('registro_estudiantes'))

    return render_template('registro_estudiantes.html')

def descargar_plantilla_estudiantes_view():
    """Genera y descarga una plantilla Excel vacía para la carga masiva."""
    columnas = [
        "cedula", "nacionalidad", "nombres", "apellidos", "genero",
        "fecha_nacimiento", "lugar_nacimiento", "estado_nacimiento", "municipio_nacimiento",
        "direccion", "telefono", "correo", "anio", "seccion"
    ]
    df = pd.DataFrame(columns=columnas)
    
    # Agregar una fila de ejemplo (opcional)
    df.loc[0] = ["12345678", "V", "JUAN CARLOS", "PEREZ RAMIREZ", "M", "2010-05-14", "CARACAS", "DISTRITO CAPITAL", "LIBERTADOR", "CALLE 1", "0412-0000000", "juan@example.com", "1er Año", "A"]
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Estudiantes')
    
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name='Plantilla_Estudiantes.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

def cargar_estudiantes_masivo_view():
    """Procesa el archivo Excel subido y registra a los estudiantes masivamente."""
    if 'archivo_excel' not in request.files:
        flash("No se subió ningún archivo.", "danger")
        return redirect(url_for('registro_estudiantes'))
        
    archivo = request.files['archivo_excel']
    if archivo.filename == '':
        flash("No se seleccionó ningún archivo.", "danger")
        return redirect(url_for('registro_estudiantes'))
        
    try:
        df = pd.read_excel(archivo, engine='openpyxl')
        
        # Omitir la primera fila si parece ser el ejemplo de Juan Carlos (opcional)
        # o simplemente intentar procesar todo
        exitosos = 0
        errores = 0
        
        # Convertir NaN a None
        df = df.where(pd.notnull(df), None)
        
        # Traer estudiantes existentes para no duplicar por cédula
        res_existentes = supabase.table("estudiante").select("cedula").execute()
        cedulas_existentes = {str(e['cedula']) for e in (res_existentes.data or [])}
        
        nuevos_estudiantes = []
        for index, row in df.iterrows():
            cedula = str(row.get('cedula', '')).replace('.0', '').strip()
            if not cedula or cedula == 'None' or cedula == '12345678':
                continue # Omitir vacíos o el de ejemplo
                
            if cedula in cedulas_existentes:
                errores += 1
                continue
                
            nacionalidad = str(row.get('nacionalidad', 'V')).strip().upper()[0] if row.get('nacionalidad') else 'V'
            genero = str(row.get('genero', 'M')).strip().upper()[0] if row.get('genero') else 'M'
            
            # Formatear fechas
            fecha_nac = row.get('fecha_nacimiento')
            if pd.notna(fecha_nac) and hasattr(fecha_nac, 'strftime'):
                fecha_nac = fecha_nac.strftime('%Y-%m-%d')
            elif pd.isna(fecha_nac):
                fecha_nac = None
                
            # Limpiar teléfono
            telefono_val = row.get('telefono')
            telefono = None
            if telefono_val and pd.notna(telefono_val):
                telefono = str(telefono_val).strip()
                # Remover decimales si se leyó como float
                if telefono.endswith('.0'):
                    telefono = telefono[:-2]
                # Limpiar a solo dígitos
                digitos = ''.join(c for c in telefono if c.isdigit())
                # Si falta el cero inicial (pandas quita el 0 a los números)
                if len(digitos) == 10:
                    digitos = '0' + digitos
                # Guardar solo si son 11 dígitos exactos (formato venezolano estándar sin guiones)
                if len(digitos) == 11:
                    telefono = digitos
                else:
                    # Si no cumple, lo dejamos como None para evitar el constraint
                    telefono = None
                
            datos = {
                "cedula": cedula,
                "nacionalidad": nacionalidad,
                "nombres": str(row.get('nombres', '')).strip().upper() if row.get('nombres') else None,
                "apellidos": str(row.get('apellidos', '')).strip().upper() if row.get('apellidos') else None,
                "genero": genero,
                "fecha_nacimiento": fecha_nac,
                "lugar_nacimiento": str(row.get('lugar_nacimiento', '')).strip() if row.get('lugar_nacimiento') else None,
                "estado_nacimiento": str(row.get('estado_nacimiento', '')).strip() if row.get('estado_nacimiento') else None,
                "municipio_nacimiento": str(row.get('municipio_nacimiento', '')).strip() if row.get('municipio_nacimiento') else None,
                "direccion": str(row.get('direccion', '')).strip() if row.get('direccion') else None,
                "telefono": telefono,
                "correo": str(row.get('correo', '')).strip() if row.get('correo') else None,
                "anio": str(row.get('anio', '')).strip() if row.get('anio') else None,
                "seccion": str(row.get('seccion', '')).strip().upper() if row.get('seccion') else None,
                "estado_estudiante": "A"
            }
            nuevos_estudiantes.append(datos)
            cedulas_existentes.add(cedula)
            
        if nuevos_estudiantes:
            # Batch insert
            supabase.table("estudiante").insert(nuevos_estudiantes).execute()
            exitosos = len(nuevos_estudiantes)
            
        mensaje = f"Se cargaron {exitosos} estudiantes masivamente."
        if errores > 0:
            mensaje += f" Se omitieron {errores} registros duplicados o de ejemplo."
            
        flash(mensaje, "success" if exitosos > 0 else "warning")
        
    except Exception as e:
        flash(f"Error procesando el archivo: {str(e)}", "danger")
        
    return redirect(url_for('registro_estudiantes'))
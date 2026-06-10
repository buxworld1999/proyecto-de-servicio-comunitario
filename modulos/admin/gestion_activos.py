from flask import render_template, request, redirect, url_for, flash, session
from db import supabase

def activos_institucion():
    """
    Lógica para el Control de Activos de la U.E.E. Carmen Ruiz.
    Mapeado directamente con los inputs y variables del HTML provisto.
    """
    if request.method == 'POST':
        # Captura exacta de los campos basados en el atributo 'name' de tu HTML
        datos_activo = {
            "nombre": request.form.get('nombre').strip(),
            "propietario": request.form.get('propietario').strip(),
            "ubicacion": request.form.get('ubicacion').strip(),
            "cantidad": int(request.form.get('cantidad', 0)),
            "valor_unitario": float(request.form.get('valor', 0.0))  # El input HTML se llama 'valor'
        }

        try:
            # Inserción limpia en Supabase
            supabase.table("activo_institucion").insert(datos_activo).execute()
            flash(f"Activo '{datos_activo['nombre']}' registrado con éxito.")
        except Exception as e:
            flash(f"Error al registrar activo: {str(e)}")
            
        return redirect(url_for('activos'))

    # --- PROCESAMIENTO DEL MÉTODO GET (LISTAR Y SUMAR) ---
    activos_lista = []
    valor_total_inventario = 0.0

    try:
        # Consultamos todos los activos guardados
        response = supabase.table("activo_institucion").select("*").execute()
        activos_lista = response.data

        # Calculamos el valor total acumulado del inventario para la variable {{ total }}
        for item in activos_lista:
            # Aseguramos que los valores no vengan nulos de la base de datos
            cant = item.get('cantidad', 0)
            val_uni = item.get('valor_unitario', 0.0)
            valor_total_inventario += (cant * val_uni)

    except Exception as e:
        flash(f"Error al recuperar los activos: {str(e)}")

    # Retornamos las variables exactas que pide tu HTML: 'activos' y 'total'
    return render_template(
        'activos.html',
        activos=activos_lista,
        total=valor_total_inventario
    )
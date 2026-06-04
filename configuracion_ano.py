from flask import Blueprint, render_template, request, flash, redirect, url_for
from promocion_automatica import promover_ano

def configuracion_ano_view():
    if request.method == 'POST':
        try:
            # Ejecutamos el script y obtenemos el log
            resultado_log = promover_ano()
            # El log contiene saltos de linea. Flask flash no renderiza HTML por defecto,
            # pero podemos pasar el mensaje con saltos y manejarlo en el template o dejarlo simple.
            flash("Proceso de promoción ejecutado. Revisa los detalles en pantalla.", "success")
            return render_template('configuracion_ano.html', resultado_log=resultado_log)
        except Exception as e:
            flash(f"Error crítico durante el proceso: {str(e)}", "error")
            return redirect(url_for('configuracion_ano'))

    # GET
    return render_template('configuracion_ano.html', resultado_log=None)

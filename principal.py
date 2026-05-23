
from ssl import ALERT_DESCRIPTION_BAD_CERTIFICATE_STATUS_RESPONSE
from pydantic._internal._model_construction import set_default_hash_func
import os
from flask import Flask, render_template, request
from supabase import create_client, Client

# Configuración de Supabase
supabase_url = os.environ.get("SUPABASE_URL", "https://mbvzajmglkvooxqkezbo.supabase.co")
supabase_key = os.environ.get("SUPABASE_KEY", "sb_publishable_N5GiaDm9d98adS74tb9kEw_ykqAzLZV")
supabase: Client = create_client(supabase_url, supabase_key)

app = Flask(__name__)

@app.route('/', methods=['GET'])
def inicio():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    v_codigo_usuario = request.form.get('codigo_usuario')
    v_nombre_completo = request.form.get('nombre_completo')
    v_clave = request.form.get('clave')
    v_accion = request.form.get('accion')
    if v_accion == 'login':
        # Buscar usuario en Supabase por nombre completo
        response = supabase.table("usuario").select("nombre_completo, contrasena_hash").eq("nombre_completo", v_nombre_completo).eq("contrasena_hash", v_clave).execute()
        usuario = response.data
        if usuario:
            return render_template('menu.html', nombres=usuario)
        else:
            return render_template('index.html', error="Contraseña incorrecta o usuario no existe.")
    elif v_accion == 'crear':
        if not v_codigo_usuario or not v_clave or not v_nombre_completo:
            return render_template('index.html', error="Faltan datos para crear el usuario.")
            
        try:
            # Crear usuario en Supabase
            response = supabase.table("usuario").insert({
                "codigo_usuario": v_codigo_usuario,
                "contrasena_hash": v_clave,
                "nombre_completo": v_nombre_completo,
                "rol": "usuario",
                "estado": "A"
            }).execute()
            return render_template('index.html', error="Usuario creado exitosamente. Por favor inicie sesión.")
            
        except Exception as e:
            return render_template('index.html', error=f"Error al crear usuario: {str(e)}")
    else:
        return render_template('index.html', error="Acción no válida.")


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)




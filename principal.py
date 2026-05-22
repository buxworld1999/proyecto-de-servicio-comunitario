
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
    v_cedula = request.form.get('cedula')
    v_clave = request.form.get('clave')
    v_accion = request.form.get('accion')
    if v_accion == 'login':
        # Buscar usuario en Supabase
        response = supabase.table("empleados").select("nombre, clave").eq("cedula", v_cedula).eq("clave", v_clave).execute()
        empleados = response.data
        if empleados:
            return render_template('menu1.html', nombres=empleados)
        else:
            return render_template('index.html', error="Contraseña incorrecta o usuario no existe.")
    elif v_accion == 'crear':
        # Aquí deberías agregar la lógica para crear un usuario en Supabase
        return render_template('incemp.html')
    else:
        return render_template('index.html', error="Acción no válida.")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)




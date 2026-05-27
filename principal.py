
import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from supabase import create_client, Client

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Configuración de Supabase
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("Faltan credenciales de Supabase. Asegúrate de configurar SUPABASE_URL y SUPABASE_KEY en el entorno.")

supabase: Client = create_client(supabase_url, supabase_key)

app = Flask(__name__)
app.secret_key = 'clave_secreta_comunitaria_ueecr'  # Requerida para activar los mensajes de éxito (flash)

@app.route('/', methods=['GET'])
def inicio():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    v_codigo_usuario = request.form.get('codigo_usuario')
    v_cedula_personal = request.form.get('cedula_personal')
    v_clave = request.form.get('clave')
    v_accion = request.form.get('accion')
    
    if v_accion == 'login':
        try:
            # Buscar usuario en Supabase usando las columnas correctas de la tabla usuario
            response = supabase.table("usuario").select("codigo_usuario, clave_hash").eq("codigo_usuario", v_codigo_usuario).eq("clave_hash", v_clave).execute()
            usuario = response.data
            if usuario:
                return render_template('menu.html', nombres=usuario)
            else:
                return render_template('index.html', error="Contraseña incorrecta o usuario no existe.")
        except Exception as e:
            return render_template('index.html', error=f"Error del servidor (Supabase): {str(e)}")
    elif v_accion == 'crear':
        if not v_codigo_usuario or not v_clave or not v_cedula_personal:
            return render_template('index.html', error="Faltan datos para crear el usuario.")
            
        try:
            # Crear usuario en Supabase
            response = supabase.table("usuario").insert({
                "codigo_usuario": v_codigo_usuario,
                "clave_hash": v_clave,
                "cedula_personal": v_cedula_personal,  # Se asume que este campo guarda la cédula
                "rol": "usuario",
                "estado": "A"
            }).execute()
            return render_template('index.html', error="Usuario creado exitosamente. Por favor inicie sesión.")
            
        except Exception as e:
            return render_template('index.html', error=f"Error al crear usuario: {str(e)}")
    else:
        return render_template('index.html', error="Acción no válida.")



# ===================================================================
# DECORADORES Y RUTAS DE PRUEBA (1 AL 12)
# ===================================================================

@app.route('/registro_estu', methods=['GET', 'POST'])
def registro_estudiantes():
    """
    Ruta de la Prueba 1: Captura el formulario y registra un estudiante
    en la tabla 'estudiante' de Supabase controlando la longitud de los tipos char(1).
    """
    if request.method == 'POST':
        # Captura y normalización estricta a 1 carácter para evitar el error 22001
        v_genero = request.form.get('genero', 'M')
        genero_filtrado = v_genero.strip().upper()[0] if v_genero else 'M' # Asegura 'M' o 'F'
        
        v_estado = request.form.get('estado', 'A')
        estado_filtrado = v_estado.strip().upper()[0] if v_estado else 'A' # Asegura 'A' o 'I'

        # Recopilación estructurada mapeando tu esquema de producción
        datos_estudiante = {
            "cedula": request.form.get('cedula'),
            "nacionalidad": request.form.get('nacionalidad'),
            "nombres": request.form.get('nombres'),
            "apellidos": request.form.get('apellidos'),
            "fecha_nacimiento": request.form.get('fecha_nacimiento') or None,
            "genero": genero_filtrado,          # Forzado a longitud 1
            "telefono": request.form.get('telefono') or None,
            "correo": request.form.get('correo') or None,
            "direccion": request.form.get('direccion') or None,
            "estado": estado_filtrado,          # Forzado a longitud 1
            "foto": None
        }

        try:
            # Inserción de datos limpia
            response = supabase.table("estudiante").insert(datos_estudiante).execute()
            flash(f"Estudiante {datos_estudiante['nombres']} guardado de forma exitosa.")
        except Exception as e:
            # Captura de errores específicos detallados
            flash(f"Error al registrar estudiante: {str(e)}")
            
        return redirect(url_for('registro_estudiantes'))

    return render_template('registro_estudiantes.html')

@app.route('/prueba2')
def prueba2():
    return render_template('prueba2.html')

@app.route('/prueba3')
def prueba3():
    return render_template('prueba3.html')

@app.route('/prueba4')
def prueba4():
    return render_template('prueba4.html')

@app.route('/prueba5')
def prueba5():
    return render_template('prueba5.html')

@app.route('/prueba6')
def prueba6():
    return render_template('prueba6.html')

@app.route('/prueba7')
def prueba7():
    return render_template('prueba7.html')

@app.route('/prueba8')
def prueba8():
    return render_template('prueba8.html')

@app.route('/prueba9')
def prueba9():
    return render_template('prueba9.html')

@app.route('/prueba10')
def prueba10():
    return render_template('prueba10.html')

@app.route('/prueba11')
def prueba11():
    return render_template('prueba11.html')

@app.route('/prueba12')
def prueba12():
    return render_template('prueba12.html')


if __name__ == '__main__':
    # Configuración dinámica para correr de forma óptima tanto local como en Render
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=puerto, debug=True)
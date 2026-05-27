# Proyecto de Servicio Comunitario

Este es el repositorio del sistema web para el **Proyecto de Servicio Comunitario** de la U.E.E. Carmen Ruiz, desarrollado en **Python** utilizando el framework **Flask** para el backend y **Supabase** como base de datos en la nube.

## 🚀 Requisitos Previos

Antes de ejecutar el proyecto, asegúrate de tener instalado en tu sistema:
- Python 3.10 o superior.
- Una cuenta y proyecto en [Supabase](https://supabase.com/).

## ⚙️ Instalación y Configuración

Sigue estos pasos para levantar el entorno de desarrollo localmente:

### 1. Clonar el Repositorio
```bash
git clone https://github.com/buxworld1999/proyecto-de-servicio-comunitario.git
cd proyecto-de-servicio-comunitario
```

### 2. Crear un Entorno Virtual (Opcional pero recomendado)
```bash
python -m venv .venv
# Activar en Windows:
.venv\Scripts\activate
# Activar en Mac/Linux:
source .venv/bin/activate
```

### 3. Instalar las Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar las Variables de Entorno (Importante)
Por razones de seguridad, las credenciales de la base de datos no están en el código. Debes crear un archivo llamado `.env` en la raíz del proyecto.

Crea el archivo `.env` y añade tus llaves de Supabase (te recomendamos usar la llave secreta `service_role` para evitar problemas con las políticas RLS):

```env
SUPABASE_URL=tu_url_de_supabase_aqui
SUPABASE_KEY=tu_llave_service_role_aqui
```

## ▶️ Ejecutar la Aplicación

Una vez instaladas las dependencias y configurado tu archivo `.env`, puedes arrancar el servidor de pruebas ejecutando:

```bash
python principal.py
```

La aplicación estará corriendo y podrás acceder a ella abriendo tu navegador en:
`http://localhost:5000`

## 📦 Estructura del Proyecto

- `principal.py`: Archivo principal del servidor Flask donde se controlan las rutas lógicas (`/login`, `/registro_estudiantes`, etc.).
- `templates/`: Archivos HTML para la interfaz de usuario.
- `static/`: Archivos estáticos como CSS, imágenes y scripts.
- `requirements.txt`: Lista de librerías de Python necesarias para que funcione el programa.
- `.env`: Archivo oculto (no subido a GitHub) que contiene tus secretos y contraseñas.

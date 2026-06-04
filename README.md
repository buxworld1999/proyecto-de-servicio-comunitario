# Proyecto de Servicio Comunitario

Este es el repositorio del sistema web para el **Proyecto de Servicio Comunitario** de la U.E.E. Carmen Ruiz, desarrollado en **Python** utilizando el framework **Flask** para el backend y **Supabase** como base de datos en la nube.

## 📖 ¿Qué hace este programa?

Este sistema integral de gestión escolar ("PRISMA") está diseñado específicamente para digitalizar, organizar y agilizar los procesos administrativos y académicos de la Unidad Educativa Estadal Carmen Ruiz. Entre sus funciones principales destacan:
- **Gestión de Usuarios y Roles:** Control de acceso seguro (Login) con permisos específicos para Administradores, Directores, Coordinadores, Secretarias y Docentes.
- **Registro Estudiantil y Personal:** Módulos para inscribir y buscar fácilmente la información completa de estudiantes y trabajadores de la institución.
- **Emisión de Documentos:** Generación y administración de constancias de estudio, reportes y citaciones.
- **Control Académico:** Administración de procesos de matrícula, control de secciones, asignación docente y registro de evaluaciones (boletines).
- **Proyectos y Labor Social:** Gestión del servicio comunitario y la labor social de los estudiantes.

🌐 **Plataforma en línea:** Puedes acceder al sistema alojado en producción a través de [https://carmen-ruiz.onrender.com](https://carmen-ruiz.onrender.com)

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
`https://carmen-ruiz.onrender.com`

## 📦 Estructura del Proyecto

- `principal.py`: Archivo principal del servidor Flask donde se controlan las rutas lógicas (`/login`, `/registro_estudiantes`, etc.).
- `templates/`: Archivos HTML para la interfaz de usuario.
- `static/`: Archivos estáticos como CSS, imágenes y scripts.
- `requirements.txt`: Lista de librerías de Python necesarias para que funcione el programa.
- `.env`: Archivo oculto (no subido a GitHub) que contiene tus secretos y contraseñas.

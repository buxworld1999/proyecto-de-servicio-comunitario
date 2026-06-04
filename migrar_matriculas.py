import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def migrar():
    print("Iniciando migración de estudiantes a matricula...")
    
    # Obtener estudiantes que tienen anio y seccion guardados
    res = supabase.table("estudiante").select("cedula, anio, seccion").execute()
    estudiantes = res.data or []
    
    if not estudiantes:
        print("No hay estudiantes para migrar.")
        return
        
    mapa_anios = {
        "1er Año": "1",
        "2do Año": "2",
        "3er Año": "3",
        "4to Año": "4",
        "5to Año": "5"
    }
    
    for est in estudiantes:
        cedula = est.get("cedula")
        anio_texto = est.get("anio")
        letra_seccion = est.get("seccion")
        
        if not anio_texto or not letra_seccion:
            continue
            
        grado_codigo = mapa_anios.get(anio_texto)
        if not grado_codigo:
            continue
            
        codigo_seccion = f"{grado_codigo}{letra_seccion}"
        
        # Insertar en tabla matricula
        datos = {
            "cedula_estudiante": cedula,
            "codigo_ano_escolar": "2025-2026",
            "codigo_seccion": codigo_seccion,
            "estado_matricula": "A"
        }
        
        try:
            supabase.table("matricula").insert(datos).execute()
            print(f"✅ Migrado estudiante V-{cedula} a la sección {codigo_seccion}")
        except Exception as e:
            print(f"Error migrando a {cedula}: {str(e)}")
            
    print("Migración finalizada.")

if __name__ == "__main__":
    migrar()

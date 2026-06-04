import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def populate():
    print("Iniciando llenado de catálogos...")

    # 1. Año Escolar
    ano = {
        "codigo": "2025-2026",
        "descripcion": "Periodo Escolar 2025-2026",
        "ano_inicio": 2025,
        "ano_fin": 2026,
        "estado": "A",
        "activo": True
    }
    
    # Intentar insertar o ignorar si ya existe
    try:
        supabase.table("ano_escolar").insert(ano).execute()
        print("✅ Año escolar '2025-2026' creado.")
    except Exception as e:
        print(f"Nota: El año escolar '2025-2026' ya podría existir o hubo un error: {str(e)}")

    # 2. Grados (1er a 5to)
    grados = [
        {"codigo": "1", "nombre": "1er Año", "nivel_educativo": "Media General", "numero_ano": 1, "activo": True},
        {"codigo": "2", "nombre": "2do Año", "nivel_educativo": "Media General", "numero_ano": 2, "activo": True},
        {"codigo": "3", "nombre": "3er Año", "nivel_educativo": "Media General", "numero_ano": 3, "activo": True},
        {"codigo": "4", "nombre": "4to Año", "nivel_educativo": "Media General", "numero_ano": 4, "activo": True},
        {"codigo": "5", "nombre": "5to Año", "nivel_educativo": "Media General", "numero_ano": 5, "activo": True},
    ]

    for g in grados:
        try:
            supabase.table("grado").insert(g).execute()
        except:
            pass
    print("✅ Grados creados (o ya existían).")

    # 3. Secciones (A hasta la F para cada grado)
    letras = ["A", "B", "C", "D", "E", "F"]
    for g in grados:
        for letra in letras:
            codigo_seccion = f"{g['codigo']}{letra}"
            seccion = {
                "codigo": codigo_seccion,
                "letra": letra,
                "codigo_grado": g["codigo"],
                "codigo_ano_escolar": "2025-2026",
                "capacidad_maxima": 35,
                "turno": "M"
            }
            try:
                supabase.table("seccion").insert(seccion).execute()
            except:
                pass
    print("✅ Secciones creadas (1A-1F ... 5A-5F).")
    print("🎉 Proceso finalizado.")

if __name__ == "__main__":
    populate()

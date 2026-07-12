import sys
from db import supabase

def main():
    try:
        # Consultamos todos los registros de la tabla ano_escolar
        res = supabase.table("ano_escolar").select("*").execute()
        print("Registros en 'ano_escolar':")
        for r in res.data:
            print(f"- ID: {r.get('id')}, Nombre/Código: {r.get('codigo') or r.get('nombre')}, Activo: {r.get('activo')}")
    except Exception as e:
        print(f"Error al consultar Supabase: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()

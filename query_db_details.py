import sys
from db import supabase

def main():
    try:
        # Consultar la tabla ano_escolar completa
        res_anos = supabase.table("ano_escolar").select("*").execute()
        print("--- Años Escolares ---")
        for r in res_anos.data:
            print(r)

        # Consultar si hay matrículas para cada uno de los periodos
        print("\n--- Conteo de matrículas en la tabla 'matricula' ---")
        for r in res_anos.data:
            codigo = r.get("codigo")
            res_mat = supabase.table("matricula").select("id", count="exact").eq("codigo_ano_escolar", codigo).execute()
            count = res_mat.count if hasattr(res_mat, 'count') else len(res_mat.data)
            print(f"Año escolar: {codigo} | Matrículas asociadas: {count}")

    except Exception as e:
        print(f"Error al consultar Supabase: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()

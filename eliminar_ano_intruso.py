import sys
from db import supabase

def main():
    if len(sys.argv) < 2:
        print("Uso: python eliminar_ano_intruso.py <codigo_ano_escolar>", file=sys.stderr)
        sys.exit(1)
        
    codigo_ano = sys.argv[1].strip()
    print(f"Iniciando verificación para el año escolar: '{codigo_ano}'...")
    
    try:
        # 1. Obtener la información del año escolar
        res_ano = supabase.table("ano_escolar").select("*").eq("codigo", codigo_ano).execute()
        if not res_ano.data:
            print(f"Error: El año escolar '{codigo_ano}' no existe en la tabla 'ano_escolar'.", file=sys.stderr)
            sys.exit(1)
            
        ano_data = res_ano.data[0]
        activo = ano_data.get("activo")
        
        print(f"Año encontrado: {ano_data}")
        
        # 2. Verificar que la columna 'activo' sea False
        if activo is not False:
            print(f"Error de Seguridad: El año escolar '{codigo_ano}' está marcado como activo: {activo}. No se puede eliminar.", file=sys.stderr)
            sys.exit(1)
            
        # 3. Verificar que no tenga matrículas asociadas en la tabla 'matricula'
        res_mat = supabase.table("matricula").select("id").eq("codigo_ano_escolar", codigo_ano).execute()
        cant_matriculas = len(res_mat.data) if res_mat.data else 0
        
        if cant_matriculas > 0:
            print(f"Error de Seguridad: El año escolar '{codigo_ano}' tiene {cant_matriculas} matrícula(s) asociada(s). No se puede eliminar para evitar afectar estudiantes.", file=sys.stderr)
            sys.exit(1)
            
        # 4. Si pasa todas las validaciones, proceder con la eliminación segura
        print("Todas las condiciones de seguridad se cumplieron exitosamente.")
        print(f"Eliminando fila de 'ano_escolar' con código '{codigo_ano}'...")
        
        res_del = supabase.table("ano_escolar").delete().eq("codigo", codigo_ano).execute()
        
        if res_del.data:
            print(f"¡Éxito! La fila correspondiente al año escolar '{codigo_ano}' se ha eliminado correctamente.")
            print(f"Detalle eliminado: {res_del.data[0]}")
        else:
            print("No se recibió confirmación de fila eliminada.", file=sys.stderr)
            
    except Exception as e:
        print(f"Ocurrió un error inesperado durante el proceso: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

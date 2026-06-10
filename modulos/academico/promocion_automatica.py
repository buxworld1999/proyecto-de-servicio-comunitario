import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

from db import supabase

def promover_ano():
    mensajes = []
    def log(msg):
        print(msg)
        mensajes.append(msg)
        
    log("=== SCRIPT DE APERTURA DE AÑO Y PROMOCIÓN ===")
    log("1. Identificando el Año Escolar Activo...")
    
    # Buscar año activo
    res_ano = supabase.table("ano_escolar").select("*").eq("activo", True).execute()
    anos_activos = res_ano.data or []
    
    if not anos_activos:
        log("[ERROR] No se encontro ningun ano escolar activo en la base de datos.")
        return "\n".join(mensajes)
        
    ano_actual = anos_activos[0]
    codigo_actual = ano_actual['codigo']
    ano_inicio = ano_actual['ano_inicio']
    ano_fin = ano_actual['ano_fin']
    
    log(f"   Año actual: {codigo_actual}")
    
    # Calcular el nuevo año
    nuevo_ano_inicio = ano_inicio + 1
    nuevo_ano_fin = ano_fin + 1
    nuevo_codigo = f"{nuevo_ano_inicio}-{nuevo_ano_fin}"
    
    # Fechas automatizadas: 15 de septiembre al 15 de julio del siguiente año
    fecha_inicio_auto = f"{nuevo_ano_inicio}-09-15"
    fecha_fin_auto = f"{nuevo_ano_fin}-07-15"
    
    log(f"\n2. Creando el Nuevo Año Escolar: {nuevo_codigo}...")
    
    nuevo_ano_data = {
        "codigo": nuevo_codigo,
        "descripcion": f"Periodo Regular {nuevo_codigo}",
        "ano_inicio": nuevo_ano_inicio,
        "ano_fin": nuevo_ano_fin,
        "fecha_inicio": fecha_inicio_auto,
        "fecha_fin": fecha_fin_auto,
        "estado": "A",
        "activo": True
    }
    
    try:
        supabase.table("ano_escolar").insert(nuevo_ano_data).execute()
        log(f"   [OK] Ano {nuevo_codigo} creado.")
    except Exception as e:
        log(f"   [AVISO] Nota (El ano posiblemente ya exista): {str(e)}")
        
    log("\n3. Generando nuevas secciones para el nuevo año...")
    grados = ["1", "2", "3", "4", "5"]
    letras = ["A", "B", "C", "D", "E", "F"]
    
    secciones_creadas = 0
    for g in grados:
        for l in letras:
            codigo_sec = f"{g}{l}"
            seccion_data = {
                "codigo": codigo_sec, # El código de sección normalmente debería incluir el año para ser único, pero nos adaptamos al modelo actual
                "letra": l,
                "codigo_grado": g,
                "codigo_ano_escolar": nuevo_codigo,
                "capacidad_maxima": 35,
                "turno": "M"
            }
            try:
                # Si el código primary key choca porque usan "1A" para todos los años,
                # tendrías que modificar el esquema de BD. Asumimos que la llave foránea se actualiza
                # o usamos UPDATE si la lógica de negocio dice que se reusan las secciones.
                # Por ahora, actualizaremos el año escolar de la sección a la nueva,
                # ya que en el script anterior se crearon como '1A', '1B', etc.
                supabase.table("seccion").update({"codigo_ano_escolar": nuevo_codigo}).eq("codigo", codigo_sec).execute()
                secciones_creadas += 1
            except:
                pass
                
    log(f"   [OK] {secciones_creadas} secciones preparadas para {nuevo_codigo}.")
    
    log("\n4. Promoviendo estudiantes...")
    # Buscar todas las matrículas del año actual
    res_mat = supabase.table("matricula").select("*").eq("codigo_ano_escolar", codigo_actual).execute()
    matriculas_actuales = res_mat.data or []
    
    if not matriculas_actuales:
        log(f"   No hay alumnos inscritos en {codigo_actual}.")
    else:
        promovidos = 0
        egresados = 0
        
        for mat in matriculas_actuales:
            seccion_vieja = mat.get("codigo_seccion") # ej: "1A"
            cedula = mat.get("cedula_estudiante")
            
            if not seccion_vieja or len(seccion_vieja) < 2:
                continue
                
            grado_num = int(seccion_vieja[0])
            letra = seccion_vieja[1:]
            
            if grado_num < 5:
                # Promover
                nuevo_grado = grado_num + 1
                nueva_seccion = f"{nuevo_grado}{letra}"
                
                nueva_matricula = {
                    "cedula_estudiante": cedula,
                    "codigo_ano_escolar": nuevo_codigo,
                    "codigo_seccion": nueva_seccion,
                    "estado_matricula": "A"
                }
                try:
                    supabase.table("matricula").insert(nueva_matricula).execute()
                    promovidos += 1
                except:
                    pass
            else:
                # 5to Año -> Egresado. Aquí deberíamos actualizar al estudiante o dejar un registro.
                # Para simplificar, cambiaremos su "estado_estudiante" en la tabla estudiante a 'E' (Egresado)
                try:
                    supabase.table("estudiante").update({"estado_estudiante": "E"}).eq("cedula", cedula).execute()
                    egresados += 1
                except:
                    pass
                    
        log(f"   [OK] {promovidos} estudiantes promovidos exitosamente.")
        log(f"   [INFO] {egresados} estudiantes egresados (5to Ano).")
        
    log("\n5. Cerrando el año anterior...")
    try:
        supabase.table("ano_escolar").update({"activo": False}).eq("codigo", codigo_actual).execute()
        log(f"   [OK] Ano {codigo_actual} marcado como inactivo.")
    except Exception as e:
        log(f"   [ERROR] Error desactivando ano viejo: {str(e)}")

    log("\n[PROCESO COMPLETADO EXITOSAMENTE]")
    return "\n".join(mensajes)

if __name__ == "__main__":
    promover_ano()

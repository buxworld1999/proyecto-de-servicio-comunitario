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

    # ── GUARDA DE SEGURIDAD: evita ejecutar la promoción dos veces ──────────
    # Si el año siguiente YA existe en la base de datos, significa que este
    # proceso ya se corrió antes (ej: alguien presionó el botón 2 veces).
    # Volver a ejecutarlo duplicaría matrículas de todos los estudiantes.
    res_check = supabase.table("ano_escolar").select("codigo").eq("codigo", nuevo_codigo).execute()
    if res_check.data:
        log(f"[BLOQUEADO] El año {nuevo_codigo} ya existe en el sistema. "
            f"La Promoción Automática ya fue ejecutada anteriormente y NO se puede repetir "
            f"(esto evita duplicar matrículas). Si de verdad necesitas revertir/repetir el proceso, "
            f"debe hacerse manualmente en la base de datos.")
        return "\n".join(mensajes)
    
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
        "estado": "I",
        "activo": False   # se crea INACTIVO; se activa recién al final, cuando todo lo demás ya terminó bien
    }
    
    try:
        supabase.table("ano_escolar").insert(nuevo_ano_data).execute()
        log(f"   [OK] Año {nuevo_codigo} creado.")
    except Exception as e:
        log(f"   [ERROR] No se pudo crear el año {nuevo_codigo}: {str(e)}")
        log("[DETENIDO] No se continuará con la promoción porque el año nuevo no se creó.")
        return "\n".join(mensajes)
        
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
                supabase.table("seccion").update({"codigo_ano_escolar": nuevo_codigo}).eq("codigo", codigo_sec).execute()
                secciones_creadas += 1
            except Exception as e:
                log(f"   [AVISO] No se pudo actualizar la sección {codigo_sec}: {str(e)}")
                
    log(f"   [OK] {secciones_creadas} secciones preparadas para {nuevo_codigo}.")
    
    log("\n4. Promoviendo estudiantes...")
    # Buscar todas las matrículas ACTIVAS del año actual
    res_mat = supabase.table("matricula").select("*") \
        .eq("codigo_ano_escolar", codigo_actual) \
        .eq("estado_matricula", "A").execute()
    matriculas_actuales = res_mat.data or []
    
    if not matriculas_actuales:
        log(f"   No hay alumnos inscritos en {codigo_actual}.")
    else:
        promovidos = 0
        egresados = 0
        omitidos = 0

        for mat in matriculas_actuales:
            seccion_vieja = mat.get("codigo_seccion") # ej: "1A"
            cedula = mat.get("cedula_estudiante")
            id_matricula_vieja = mat.get("id")

            if not seccion_vieja or len(seccion_vieja) < 2:
                continue

            grado_num = int(seccion_vieja[0])
            letra = seccion_vieja[1:]

            if grado_num < 5:
                # Promover
                nuevo_grado = grado_num + 1
                nueva_seccion = f"{nuevo_grado}{letra}"

                # ── Evita duplicados: si el estudiante YA tiene una matrícula en el año
                # nuevo (por ejemplo, porque el script se corrió antes parcialmente), se
                # omite en vez de insertar otra fila igual.
                res_dup = supabase.table("matricula").select("id") \
                    .eq("cedula_estudiante", cedula) \
                    .eq("codigo_ano_escolar", nuevo_codigo).execute()
                if res_dup.data:
                    omitidos += 1
                    continue

                nueva_matricula = {
                    "cedula_estudiante": cedula,
                    "codigo_ano_escolar": nuevo_codigo,
                    "codigo_seccion": nueva_seccion,
                    "estado_matricula": "A"
                }
                try:
                    supabase.table("matricula").insert(nueva_matricula).execute()
                    promovidos += 1
                    
                    # Actualizar el año y sección base en el perfil del estudiante
                    mapa_nombres_anio = {
                        1: "1er Año",
                        2: "2do Año",
                        3: "3er Año",
                        4: "4to Año",
                        5: "5to Año"
                    }
                    nombre_nuevo_anio = mapa_nombres_anio.get(nuevo_grado, f"{nuevo_grado} Año")
                    supabase.table("estudiante").update({
                        "anio": nombre_nuevo_anio,
                        "seccion": letra
                    }).eq("cedula", cedula).execute()
                    
                    # Cierra la matrícula vieja para que deje de aparecer como "activa"
                    # en la sección/año anterior (ej: NOTA: se asume 'I' de Inactivo,
                    # revisar con el equipo si el sistema usa otro valor para esto).
                    if id_matricula_vieja:
                        supabase.table("matricula").update({"estado_matricula": "I"}) \
                            .eq("id", id_matricula_vieja).execute()
                except Exception as e:
                    log(f"   [ERROR] No se pudo promover a {cedula}: {str(e)}")
            else:
                # 5to Año -> Egresado.
                try:
                    supabase.table("estudiante").update({"estado_estudiante": "E"}).eq("cedula", cedula).execute()
                    egresados += 1
                    if id_matricula_vieja:
                        supabase.table("matricula").update({"estado_matricula": "I"}) \
                            .eq("id", id_matricula_vieja).execute()
                except Exception as e:
                    log(f"   [ERROR] No se pudo marcar como egresado a {cedula}: {str(e)}")

        log(f"   [OK] {promovidos} estudiantes promovidos exitosamente.")
        log(f"   [INFO] {egresados} estudiantes egresados (5to Año).")
        if omitidos:
            log(f"   [INFO] {omitidos} estudiantes ya tenían matrícula en {nuevo_codigo}, se omitieron para evitar duplicados.")
        
    log("\n5. Cerrando el año anterior y activando el nuevo...")
    try:
        supabase.table("ano_escolar").update({"activo": False, "estado": "I"}).eq("codigo", codigo_actual).execute()
        supabase.table("ano_escolar").update({"activo": True, "estado": "A"}).eq("codigo", nuevo_codigo).execute()
        log(f"   [OK] {codigo_actual} -> Inactivo | {nuevo_codigo} -> ACTIVO VIGENTE.")
    except Exception as e:
        log(f"   [ERROR] Error en el cambio de año activo: {str(e)}")

    log("\n[PROCESO COMPLETADO EXITOSAMENTE]")
    return "\n".join(mensajes)

if __name__ == "__main__":
    promover_ano()
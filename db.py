"""
db.py — Cliente centralizado de Supabase
PRISMA — Sistema de Gestión Escolar

Este módulo existe para evitar importaciones circulares.
Tanto principal.py como los módulos de registro (registrar_personal.py,
regis_estudiante.py, etc.) importan 'supabase' desde aquí.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError(
        "Faltan credenciales de Supabase. "
        "Configura SUPABASE_URL y SUPABASE_KEY en el archivo .env"
    )

supabase: Client = create_client(supabase_url, supabase_key)

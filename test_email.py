"""
Script de prueba de envío de correo via Gmail API (OAuth2).
Ejecutar desde la raíz del proyecto:
    python test_email.py
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# Agregar el directorio raíz al path para importar la app
sys.path.insert(0, str(Path(__file__).parent))

DEST_EMAIL = "diegoalgtr1@gmail.com"

async def main():
    # Verificar variables requeridas
    required = ["GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET", "GMAIL_REFRESH_TOKEN", "MAIL_FROM"]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        print(f"❌ Faltan variables de entorno: {missing}")
        print("   Asegúrate de que estén en tu .env local")
        return

    print("Enviando correo de prueba via Gmail API...")
    print(f"  FROM: {os.getenv('MAIL_FROM')}")
    print(f"  TO  : {DEST_EMAIL}")
    print()

    # Importar la función de envío ya implementada
    from app.main import send_booking_email

    booking_data = {
        "user_name": "Diego (Prueba)",
        "room_name": "Sala Amarilla",
        "booking_date": "2026-02-23",
        "start_time": "09:00",
        "end_time": "10:00",
        "area": "TI - Prueba Gmail API",
    }

    # Forzar MAIL_ENABLED para la prueba
    os.environ["MAIL_ENABLED"] = "true"

    await send_booking_email(booking_data, DEST_EMAIL)

asyncio.run(main())

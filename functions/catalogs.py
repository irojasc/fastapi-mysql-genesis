from datetime import datetime, timezone, timedelta
import pytz

def normalize_last_sync(last_sync_str: str) -> str:
    """
    Convierte un string ISO con tz a UTC y aplica tolerancia de 5 minutos.
    Retorna string en formato MySQL (YYYY-MM-DD HH:MM:SS).
    """
    # # # Parsear string ISO con zona horaria
    # # dt_local = datetime.fromisoformat(last_sync_str)

    # # # Convertir a UTC
    # # dt_utc = dt_local.astimezone(timezone.utc)

    # Restar 10 minutos de tolerancia
    dt_utc_with_tolerance = last_sync_str - timedelta(minutes=5)

    # Formatear para MySQL
    return dt_utc_with_tolerance.strftime("%Y-%m-%d %H:%M:%S")


def get_lima_date_formatted() -> tuple[str, str]:
    """Calcula la fecha y hora actual en la zona horaria 'America/Lima' 
       y la formatea como (hora_str, fecha_str)."""
    
    # 1. Obtener la hora UTC actual
    now_utc = datetime.now(timezone.utc)
    
    # 2. Convertir a la zona horaria de Lima
    lima_tz = pytz.timezone("America/Lima")
    now_lima = now_utc.astimezone(lima_tz)
    
    # Fecha: YYYY-MM-DD
    fecha_str = now_lima.strftime("%Y-%m-%d")
    
    return fecha_str

def get_lima_time_formatted() -> tuple[str, str]:
    """Calcula la fecha y hora actual en la zona horaria 'America/Lima' 
       y la formatea como (hora_str, fecha_str)."""
    
    # 1. Obtener la hora UTC actual
    now_utc = datetime.now(timezone.utc)
    
    # 2. Convertir a la zona horaria de Lima
    lima_tz = pytz.timezone("America/Lima")
    now_lima = now_utc.astimezone(lima_tz)
    
    # 3. Formatear
    # Hora: HH:MM:SS
    hora_str = now_lima.strftime("%H:%M:%S") 
    
    return hora_str

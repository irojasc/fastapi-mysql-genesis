from config.db import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
import boto3

def get_s3_client():
    # Usamos un generador para que FastAPI gestione el ciclo de vida si fuera necesario
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )
        # config=Config(signature_version='s3v4') # Recomendado para regiones nuevas
    try:
        yield s3_client
    finally:
        # Aquí cerrarías conexiones si usaras una librería asíncrona como aioboto3
        pass
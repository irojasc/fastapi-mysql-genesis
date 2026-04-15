import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, aliased
load_dotenv(override=True)

engine = create_engine("mysql+pymysql://{}:{}@{}:{}/{}".format(
    os.getenv("DB_USER", default=None),
    os.getenv("DB_PASSWORD", default=None),
    os.getenv("DB_HOST", default=None),
    os.getenv("DB_PORT", default=None),
    os.getenv("DB_DATABASE", default=None),
        ),
    pool_pre_ping= True,
    pool_recycle=300,        # Recicla conexiones cada 5 minutos (evita el timeout de MySQL)
    pool_size=10,            # Conexiones base que se mantienen abiertas
    max_overflow=20,         # Conexiones extra permitidas en picos de tráfico
    pool_timeout=30
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

meta = MetaData()
SECRET_KEY = os.getenv("SECRET_KEY", default=None)
ALGORITHM = os.getenv("ALGORITHM_KEY", default=None)
CREDENTIALS_JSON = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON', default=None)
DECOLECTA_TOKEN = os.getenv('DECOLECTA_TOKEN', default=None)
MIFACT_TOKEN = os.getenv('MIFACT_TOKEN', default=None)
MIFACT_ENDPOINT = os.getenv('MIFACT_ENDPOINT', default=None)
MIFACT_MIRUC = os.getenv('MIFACT_MIRUC', default=None)
BUCKET_NAME = os.getenv('BUCKET_NAME', default=None)
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', default=None)
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', default=None)
AWS_REGION = os.getenv('AWS_REGION', default=None)



# con = engine.connect()
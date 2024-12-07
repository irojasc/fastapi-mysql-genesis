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
    #lo de arriba para conocer el background de sql
    )
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = Session()
meta = MetaData()
con = engine.connect()
SECRET_KEY = os.getenv("SECRET_KEY", default=None)
ALGORITHM = os.getenv("ALGORITHM_KEY", default=None)
CREDENTIALS_JSON = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON', None)
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
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

# from decouple import Config, RepositoryEnv
# DOTENV_FILE = './.env'
# env_config = Config(RepositoryEnv(DOTENV_FILE))
# engine = create_engine("mysql+pymysql://root:chuspa123@localhost:3306/genesisdb")

# engine = create_engine("mysql+pymysql://{}:{}@{}:{}/{}".format(DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_DATABASE))
    # env_config.get('MYSQL_USER'), 
    # env_config.get('MYSQL_PASSWORD'), 
    # env_config.get('MYSQL_HOST'), 
    # env_config.get('MYSQL_PORT'), 
    # env_config.get('MYSQL_DB'),
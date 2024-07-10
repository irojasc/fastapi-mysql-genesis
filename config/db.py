import os
from sqlalchemy import create_engine, MetaData
engine = create_engine("mysql+pymysql://{}:{}@{}:{}/{}".format(
    os.getenv("DB_USER", default=None),
    os.getenv("DB_PASSWORD", default=None),
    os.getenv("DB_HOST", default=None),
    os.getenv("DB_PORT", default=None),
    os.getenv("DB_DATABASE", default=None),
        )
    )
meta = MetaData()
con = engine.connect()



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
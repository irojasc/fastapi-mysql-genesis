from sqlalchemy import create_engine, MetaData
from decouple import Config, RepositoryEnv
DOTENV_FILE = './.env'
env_config = Config(RepositoryEnv(DOTENV_FILE))
# engine = create_engine("mysql+pymysql://root:chuspa123@localhost:3306/genesisdb")
# engine = create_engine("mysql+pymysql://{}:{}@{}:{}/{}".format(env_config.get('MYSQL_USER'), env_config.get('MYSQL_PASSWORD'), env_config.get('MYSQL_HOST'), env_config.get('MYSQL_PORT'), env_config.get('MYSQL_DB')))
engine = create_engine("mysql+pymysql://{}:{}@{}:{}/{}".format(DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_DATABASE))
meta = MetaData()
con = engine.connect()
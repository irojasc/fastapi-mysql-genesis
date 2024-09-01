from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import Integer, LargeBinary
from config.db import meta, engine

WareSet = Table("wareset", meta, 
                Column("lvl", Integer, nullable=False, unique=True, primary_key=True), 
                Column("locTooltip", LargeBinary, default=0))

meta.create_all(bind=engine)
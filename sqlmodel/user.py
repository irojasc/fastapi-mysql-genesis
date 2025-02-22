from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import Integer, String, Date, LargeBinary, BINARY
from config.db import meta, engine

User = Table("user", meta, 
                Column("id", Integer, nullable=False), 
                Column("userSet", Integer), 
                Column("idDoc", String(20), nullable=False), 
                Column("user", String(15), nullable=False,primary_key=True), 
                Column("pw", String(72)), 
                Column("enabled", BINARY, default=b'\x01'), 
                Column("editDate", Date, nullable=False), 
                Column("creationDate", Date, nullable=False),
                Column("userName", String(20), nullable=True),)

meta.create_all(bind=engine)
from sqlalchemy import Table, Column, DateTime
from sqlalchemy.sql.sqltypes import String, SmallInteger
from sqlalchemy.dialects.mysql import BIGINT
from config.db import meta, engine

ObjectFiles = Table("ObjectFiles", meta, 
                Column("DocEntry", BIGINT(unsigned=True), nullable=False, unique=True, primary_key=True, autoincrement=True), 
                Column("EntityType", String(20), nullable=False), #esto apunta a la tabla a la que pertenece el objecto
                Column("EntityEntry", SmallInteger(unsigned=True), nullable=False)
                Column("UploadEntry", BIGINT(unsigned=True), nullable=False) #p: pendiente, c:completed, f:failed, e: expired
                Column("FileRole", String(5), nullable=False),
                Column("IsActive", String(1), nullable=False),
                Column("LastDate", DateTime, nullable=False)
                )
meta.create_all(bind=engine)
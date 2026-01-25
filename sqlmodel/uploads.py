from sqlalchemy import Table, Column, DateTime, Enum
from sqlalchemy.sql.sqltypes import String
from sqlalchemy.dialects.mysql import BIGINT
from config.db import meta, engine

Uploads = Table("Uploads", meta, 
                Column("Uuid", BIGINT(unsigned=True), nullable=False, unique=True, primary_key=True, autoincrement=True), 
                Column("FileName", String(50), nullable=False), 
                Column("ContentType", String(50), nullable=False),
                Column("Status", Enum('P', 'C', 'F', 'E', name="doc_status"), default='P', nullable=False), #p: pendiente, c:completed, f:failed, e: expired
                Column("UserSign", String(15), nullable=False),
                Column("LastDate", DateTime, nullable=False)
                )
meta.create_all(bind=engine)
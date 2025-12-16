from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import String
from config.db import meta, engine

OAFV = Table("OAFV", meta, 
                Column("Code", String(2), primary_key=True), 
                Column("Name", String(50), nullable=False), 
                Column("VatCode", String(5), nullable=False),
                Column("IsActive", String(1), nullable=True, server_default="Y"),
                Column("SunatAfectacion", String(2, collation="utf8mb4_0900_ai_ci"), nullable=True),
                Column("SunatTributo", String(4, collation="utf8mb4_0900_ai_ci"), nullable=True),
                )
meta.create_all(bind=engine)
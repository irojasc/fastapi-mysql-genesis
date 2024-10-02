from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import Integer, String, Date
from config.db import meta, engine

Transfer = Table("transfer_", meta, 
                Column("codeTS", String(12), nullable=False, unique=True, primary_key=True), 
                Column("fromWareId", Integer, nullable=False), 
                Column("toWareId", Integer, nullable=True, default=None), 
                Column("fromUser", String(15), nullable=False), 
                Column("toUser", String(15), nullable=True, default=None), 
                Column("fromDate", Date, nullable=False), 
                Column("toDate", Date, nullable=True, default=None),
                Column("state", Integer, default=3),
                Column("idOperReas", Integer, nullable=True, default=None), 
                Column("note", String(60), nullable=True, default=None), 
                Column("cardCode", String(11), nullable=True, default=None),
                )
meta.create_all(bind=engine)
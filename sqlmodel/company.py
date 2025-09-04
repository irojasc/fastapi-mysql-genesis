from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import Integer, String, Date, BINARY, Boolean
from config.db import meta, engine

Company = Table("company", meta, 
                Column("cardCode", String(15), primary_key=True), 
                Column("docName", String(100), nullable=True), 
                Column("address", String(100), nullable=True), 
                Column("idUbigeo", Integer, nullable=True),
                Column("active", BINARY, default=b'\x01'),
                Column("type", String(1), default='S'),
                Column("LicTradNum", String(15), nullable=True),
                Column("creationDate", Date, nullable=True),
                Column("DocType", String(10), nullable=True),
                Column("CardStatus", String(100), nullable=True),
                Column("CardCond", String(100), nullable=True),
                Column("BusinessName", String(100), nullable=True),
                Column("TermCode", String(10), nullable=False)
                )
meta.create_all(bind=engine)


#from sqlalchemy import Table, Column
#from sqlalchemy.sql.sqltypes import Integer, String, Date, BINARY, Boolean
#from config.db import meta, engine
#
#Company = Table("company", meta, 
#                Column("cardCode", String(15), primary_key=True), 
#                Column("docName", String(50), nullable=True), 
#                Column("address", String(50), nullable=True), 
#                Column("email", String(15), nullable=True), 
#                Column("phone", String(15), nullable=True), 
#                Column("idUbigeo", Integer, nullable=True),
#                Column("active", BINARY, default=b'\x01'),
#                Column("type", String(1), default='S'),
#                Column("LicTradNum", String(15), nullable=True),
#                Column("ContactPerson", String(30), nullable=True),
#                Column("creationDate", Date, nullable=False)
#                )
#meta.create_all(bind=engine)

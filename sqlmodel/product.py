from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import Integer, String, Date, _Binary
from config.db import meta, engine

Product = Table("product", meta, 
                Column("id", Integer, nullable=False, unique=True, primary_key=True), 
                Column("idItem", Integer, nullable=True), 
                Column("isbn", String(15), nullable=True), 
                Column("title", String(90), nullable=False), 
                Column("autor", String(45), nullable=False), 
                Column("publisher", String(90), nullable=False),
                Column("content", String(800), default=None), 
                Column("dateOut", Date, default=None), 
                Column("idLanguage", Integer, default=None),
                Column("pages", Integer, default=None),
                Column("weight", Integer, default=None),
                Column("cover", _Binary, default=None),
                Column("width", Integer, default=None),
                Column("height", Integer, default=None),
                Column("creationDate", Date, nullable=False),
                Column("editDate", Date, nullable=False),
                Column("large", Integer, default=None),
                Column("wholesale", _Binary, default=None),
                Column("antique", _Binary, default=None),
                Column("isDelete", _Binary, default=None),
                Column("atWebProm", _Binary, default=None),
                )
meta.create_all(bind=engine)
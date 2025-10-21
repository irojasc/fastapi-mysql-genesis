from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import  String, Integer
from config.db import meta, engine

DocSeries = Table("DocSeries", meta, 
                Column("SeriesCode", String(10), primary_key=True), 
                Column("DocTypeCode", String(3), nullable=False), 
                Column("Prefix", String(10), nullable=True),
                Column("LastNumber", Integer, nullable=False),
                Column("NextNumber", Integer, nullable=True),
                Column("WareCode", Integer, nullable=True)
                )
meta.create_all(bind=engine)
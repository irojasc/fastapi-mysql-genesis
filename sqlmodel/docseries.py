from sqlalchemy import (
    Table,
    Column,
    String,
    DateTime,
    Enum,
    Integer
)
from sqlalchemy.sql.sqltypes import  String, Integer
from config.db import meta, engine

DocSeries = Table("DocSeries", meta, 
                Column("SeriesCode", String(10), unique=True, primary_key=True), 
                Column("DocTypeCode", String(3), nullable=False), 
                Column("Prefix", String(10), nullable=True),
                Column("LastNumber", Integer, nullable=False),
                Column("NextNumber", Integer, nullable=True),
                Column("WareCode", Integer, nullable=True),
                # Tipo de serie: normal o rezagada
                Column(
                    "SeriesType",
                    Enum("Regular", "Deferred", name="seriestype_enum"),
                    nullable=False,
                    default="Regular",
                    server_default="Regular"
                ),
                # Estado actual de la serie
                Column(
                    "Status",
                    Enum("Active", "Reserved", "Blocked", name="status_enum"),
                    nullable=False,
                    default="Reserved",
                    server_default="Reserved"
                ),
                # Auditoría (sin automático, como pediste)
                Column("CreateDate", DateTime, nullable=True),
                Column("UpdateDate", DateTime, nullable=True),
                Column("UpdateUser", String(15), nullable=True),
                )
meta.create_all(bind=engine)
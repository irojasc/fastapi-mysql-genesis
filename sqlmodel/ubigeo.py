from sqlalchemy import Table, Column, text
from sqlalchemy.sql.sqltypes import Integer, String
from sqlalchemy.dialects.mysql import TINYINT #SMALLINT,
from config.db import meta, engine

Ubigeo = Table("ubigeo", meta, 
                Column("idUbigeo", Integer, primary_key=True), 
                Column("pais", String(20), default='PERU'), 
                Column("dep_id", String(4), nullable=True), 
                Column("pro_id", String(4), nullable=True), 
                Column("dis_id", String(4), nullable=True), 
                Column("dep_name", String(25), nullable=True),
                Column("pro_name", String(25), nullable=True), 
                Column("dis_name", String(25), nullable=True),
                # NUEVOS CAMPOS: IsActive e IsPriority
                Column("IsActive", TINYINT(1), nullable=False, server_default=text("'0'")),
                #    comment="0: Oculto, 1: Visible en la web. Controla el alcance logístico."
                Column("IsPriority", TINYINT(1), nullable=False, server_default=text("'0'")),
                #    comment="0: Orden normal, 1: Aparece arriba en la lista. Facilita la UX para Cusco/Lima."
                )
meta.create_all(bind=engine)
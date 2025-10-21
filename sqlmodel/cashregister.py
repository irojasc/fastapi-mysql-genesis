from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import  String, Integer, DECIMAL, DateTime
from config.db import meta, engine

CashRegister = Table("CashRegister", meta,
                    Column("CodeTS", String(12), primary_key=True), 
                    Column("WareID", Integer, nullable=False), 
                    Column("User", Integer, nullable=False), 
                    Column("OpenDate", DateTime, nullable=False),
                    Column("CloseDate", DateTime, nullable=True),
                    Column("Status", String(100), nullable=True),
                    Column("CashOpen", DECIMAL(7, 2), nullable=False),
                    Column("CashTotalClose", DECIMAL(7, 2), nullable=True),
                    Column("CashSystem", DECIMAL(7, 2), nullable=True),
                    Column("CashDiff", DECIMAL(7, 2), nullable=True),
                    Column("CardTotal", DECIMAL(7, 2), nullable=True),
                    Column("TransferTotal", DECIMAL(7, 2), nullable=True),
                    Column("WalletTotalM", DECIMAL(7, 2), nullable=True),
                    Column("WalletTotalC", DECIMAL(7, 2), nullable=True),
                    Column("Obs", String(45), nullable=True),
                )
meta.create_all(bind=engine)


# Column("UpdateDate", DateTime, nullable=True)
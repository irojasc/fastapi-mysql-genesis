from sqlalchemy import (
    MetaData,
    Table,
    Column,
    String,
    BigInteger,
    Numeric,
    DateTime,
    # Integer,
    ForeignKeyConstraint,
    Index
)
from sqlalchemy.sql.sqltypes import Integer
from sqlalchemy.dialects.mysql import CHAR, JSON, TINYINT, TIMESTAMP

metadata = MetaData()

CheckoutAttempts = Table(
    'checkoutattempts',
    metadata,
    # Columnas
    Column('Uuid', CHAR(36), primary_key=True, nullable=False),
    Column('DocNum', BigInteger, unique=True, nullable=True),  # unsigned se maneja a nivel DB o con dialecto, BigInteger suele bastar
    Column('SessionId', CHAR(36), nullable=False),
    Column('CartPayload', JSON, nullable=False),
    Column('ShippingPayload', JSON, nullable=True),
    Column('BillingPayload', JSON, nullable=True),
    Column('ShippingAmount', Numeric(10, 2), nullable=False, server_default='0.00'),
    Column('TotalAmount', Numeric(10, 2), nullable=False),
    Column('CreateDate', TIMESTAMP, nullable=True),
    Column('PayId', String(50), nullable=True),
    Column('PayStatus', String(30), nullable=True),
    Column('PayDetail', String(100), nullable=True),
    Column('Amount', Numeric(10, 2), nullable=True),
    Column('DateApproved', DateTime, nullable=True),
    Column('MethodId', String(50), nullable=True),
    Column('TrackingSlug', String(100), unique=True, nullable=True),
    Column('CourierCode', String(50), nullable=True),
    Column('EmailId', String(50), nullable=True),
    Column('ShipType', String(20), nullable=True),
    Column('StepOrder', TINYINT, nullable=True),
    Column('PreparingBy', String(15), nullable=True),
    Column('PreparingAt', DateTime, nullable=True),
    Column('HandedOverBy', String(15), nullable=True),
    Column('HandedOverAt', DateTime, nullable=True),
    Column('idWare', Integer, nullable=True),

    # Claves Foráneas (Foreign Keys)
    ForeignKeyConstraint(
        ['HandedOverBy'], ['user.user'], 
        name='FK_CheckoutAttempts_HandedOverBy'
    ),
    ForeignKeyConstraint(
        ['PreparingBy'], ['user.user'], 
        name='FK_CheckoutAttempts_PreparingBy'
    ),
    # Clave foránea compuesta
    # ForeignKeyConstraint(
    #     ['ShipType', 'StepOrder'], 
    #     ['orderflowsteps.ShipType', 'orderflowsteps.StepOrder'], 
    #     name='FK_CheckoutAttempts_OrderFlowSteps'
    # ),

    # Índices adicionales (Los UNIQUE ya crean índices automáticamente)
    Index('idx_TrackingSlug', 'TrackingSlug'),
    Index('idx_CourierCode', 'CourierCode'),
    Index('FK_CheckoutAttempts_OrderFlowSteps', 'ShipType', 'StepOrder'),
    Index('FK_CheckoutAttempts_PreparingBy', 'PreparingBy'),
    Index('FK_CheckoutAttempts_HandedOverBy', 'HandedOverBy'),
    
    # Configuración del motor de MySQL
    mysql_engine='InnoDB',
    mysql_charset='latin1'
)
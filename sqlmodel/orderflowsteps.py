from sqlalchemy import (
    MetaData,
    Table,
    Column,
    String,
    ForeignKey,
    UniqueConstraint,
    Index
)
from sqlalchemy.dialects.mysql import TINYINT

metadata = MetaData()

OrderFlowSteps = Table(
    'orderflowsteps',
    metadata,
    # Columnas
    Column('ShipType', String(20), primary_key=True, nullable=False),
    Column('StepOrder', TINYINT, primary_key=True, nullable=False),
    Column('StatusCode', String(30), ForeignKey('orderstatus.Code', name='orderflowsteps_ibfk_1'), nullable=False),

    # Restricción Única Compuesta
    UniqueConstraint('ShipType', 'StatusCode', name='DeliveryType'),

    # Índices adicionales
    Index('StatusCode', 'StatusCode'),

    # Configuración del motor de MySQL
    mysql_engine='InnoDB',
    mysql_charset='latin1'
)
from sqlalchemy import select, update, case, and_, text
from datetime import datetime
from service.order_flow_config import obtener_config
from functions.sales import formatear_pedido


from sqlmodel.checkoutattempts import CheckoutAttempts
# from sqlalchemy import select, asc, func, insert, and_, desc, text, update, case, or_, extract
from sqlmodel.orderflowsteps import OrderFlowSteps
from sqlmodel.ware import Ware
from sqlmodel.ubigeo import Ubigeo
import pytz

class OrderFlowService:

    def __init__(self, session):
        self.session = session

    def _obtener_pedido(self, docnum: str):
        stmt = (
            select(
                CheckoutAttempts.c.DocNum,
                CheckoutAttempts.c.StepOrder,
                CheckoutAttempts.c.PreparingBy,
                CheckoutAttempts.c.PreparingAt,
                CheckoutAttempts.c.HandedOverBy,
                CheckoutAttempts.c.HandedOverAt,
                CheckoutAttempts.c.CourierCode,
                CheckoutAttempts.c.ShipType,
                CheckoutAttempts.c.idWare,
            )
            .where(CheckoutAttempts.c.DocNum == docnum)
            .with_for_update()
            .limit(1)
        )

        return self.session.execute(stmt).mappings().first()



    def update(self, params):
        try:
            # Obtener pedido
            pedido = self._obtener_pedido(params.DocNum)

            if pedido is None:
                return {
                    "cabecera": {
                        "ok": False,
                        "code": "NOT_FOUND",
                        "message": "Pedido no encontrado."
                    },
                    "detalle": {}
                }

            # Validar
            validacion = self._validar_transicion(
                pedido,
                params
            )

            # Si no puede continuar
            if not validacion["ok"]:

                return self._armar_respuesta(
                    params.DocNum,
                    validacion
                )

            # Actualizar
            self._actualizar_estado(
                pedido,
                params
            )

            # Confirmar cambios
            self.session.commit()

            return self._armar_respuesta(
                params.DocNum,
                {
                    "ok": True,
                    "code": "UPDATED",
                    "message": "Pedido actualizado correctamente."
                }
            )

        except Exception:

            self.session.rollback()
            raise

       
    
    def _validar_transicion(self, pedido, params):
        # 1. El frontend tiene una versión antigua
        if pedido["StepOrder"] != int(params.IdState):
            return {
                "ok": False,
                "code": "OUTDATED",
                "message": "El estado del pedido ha cambiado. Se muestra la información actualizada."
            }

        # 2. Buscar configuración de la etapa
        config = obtener_config(
            pedido["ShipType"],
            pedido["StepOrder"]
        )

        if config is None:
            return {
                "ok": False,
                "code": "INVALID_STEP",
                "message": "El pedido ya no admite más cambios."
            }

        # 3. Validar propietario
        owner_field = config.get("owner_field")
        require_owner = config.get("require_owner", True)

        if owner_field and require_owner:

            owner = pedido.get(owner_field)

            # Primera vez
            if owner is None:
                return {
                    "ok": True,
                    "code": "OK",
                    "message": ""
                }

            # El mismo usuario continúa
            if owner == params.User:
                return {
                    "ok": True,
                    "code": "OK",
                    "message": ""
                }

            # Otro usuario tiene el pedido
            return {
                "ok": False,
                "code": "TAKEN",
                "message": f"El pedido está siendo atendido por {owner}."
            }

        # No existe propietario para esta etapa
        return {
            "ok": True,
            "code": "OK",
            "message": ""
        }
    
    def _actualizar_estado(self, pedido, params):
        lima_tz = pytz.timezone("America/Lima")

        config = obtener_config(
            pedido["ShipType"],
            pedido["StepOrder"]
        )

        valores = {}

        # Siempre avanza al siguiente estado
        valores["StepOrder"] = config["next_id"]

        # -------------------------
        # Registrar propietario
        # -------------------------
        owner_field = config.get("owner_field")

        if owner_field and pedido.get(owner_field) is None:
            valores[owner_field] = params.User

        # -------------------------
        # Registrar almacén
        # -------------------------
        if config.get("set_ware") and params.WareID:
            if (
                config.get("set_ware")
                and params.WareID
                and pedido.get("idWare") is None
            ):
                valores["idWare"] = params.WareID
        
        # -------------------------
        # Registrar fecha
        # -------------------------
        date_field = config.get("date_field")

        if date_field:
            valores[date_field] = datetime.now(lima_tz)

        # -------------------------
        # Código de seguimiento
        # -------------------------
        if config.get("track") and params.NumTrack:
            valores["CourierCode"] = params.NumTrack

        # -------------------------
        # Finaliza proceso
        # -------------------------
        if config.get("finish"):
            valores["HandedOverBy"] = params.User
            valores["HandedOverAt"] = datetime.now(lima_tz)

        stmt = (
            update(CheckoutAttempts)
            .where(CheckoutAttempts.c.DocNum == params.DocNum)
            .values(**valores)
        )

        self.session.execute(stmt)
    

    def _armar_respuesta(
        self,
        docnum,
        estado
    ):

        respuesta = self._consultar_pedido_respuesta(docnum)

        if respuesta is None:

            return {
                "cabecera": estado,
                "detalle": {}
            }

        respuesta["cabecera"] = estado

        return respuesta
    
    def _consultar_pedido_respuesta(self, docnum):
        department = text("""
            CONVERT(
                JSON_UNQUOTE(
                    JSON_EXTRACT(checkoutattempts.ShippingPayload,'$.department')
                )
            USING latin1)
            """)
        stmt = select(  CheckoutAttempts.c.DocNum.label("num"), #numero de pedido
                        CheckoutAttempts.c.CreateDate.label("registro"), #fecha creacion de registro
                        CheckoutAttempts.c.DateApproved.label("pago"), #fecha de pago
                        CheckoutAttempts.c.HandedOverAt.label("entrega"), # fecha de entrega
                        CheckoutAttempts.c.ShippingPayload, #datos del cliente
                        CheckoutAttempts.c.MethodId.label("m_pago"), #modo de pago
                        CheckoutAttempts.c.Amount.label("total"), #Monto total, incluye delivery en caso es para envio
                        CheckoutAttempts.c.ShipType, #Tipo de entrega
                        CheckoutAttempts.c.PreparingBy.label("preparado"), #preparado por
                        CheckoutAttempts.c.HandedOverBy.label("entregado"), #entregado por
                        OrderFlowSteps.c.StepOrder,
                        OrderFlowSteps.c.StatusCode,
                        Ware.c.code.label("wareCode"),
                        # 1. Aplicamos la lógica condicional con CASE
                        case(
                            (CheckoutAttempts.c.ShipType == 'DELIVERY', Ubigeo.c.dep_name),
                            else_='TIENDA'
                        ).label("destino")
                    ).join(OrderFlowSteps, and_(CheckoutAttempts.c.StepOrder == OrderFlowSteps.c.StepOrder,
                                        CheckoutAttempts.c.ShipType == OrderFlowSteps.c.ShipType )
                    ).join(
                        Ware,
                        CheckoutAttempts.c.idWare == Ware.c.id,
                        isouter=True # Usamos LEFT JOIN (isouter=True) por si algún registro no tiene wareCode o no existe
                    ).join(
                        # 2. Hacemos el LEFT JOIN con Ubigeo SOLO si es DELIVERY
                        Ubigeo,
                        and_(
                        CheckoutAttempts.c.ShipType == 'DELIVERY',
                        department == Ubigeo.c.dep_id,
                        Ubigeo.c.pro_id == '01', #<-- forzamos esta condicion
                        Ubigeo.c.dis_id == '01' #<-- forzamos esta condicion
                        ),
                        isouter=True # Obligatorio para que si no es DELIVERY (o no encuentra match) no borre la fila
                    ).filter(
                        CheckoutAttempts.c.DocNum == docnum
                    )
        
        pedido = self.session.execute(stmt).mappings().first()

        if pedido is None:
            return None
        
        return formatear_pedido(dict(pedido))
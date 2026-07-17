pasos_aprobacion = {

    "DELIVERY": {

        "1": {
            "btn_txt": "ATENDER",
            "accion": "ATENDER",
            "next_id": 2,
            "next_name": "NOTIFICAR ENTREGA A COURIER",
            "isFinal": False,
            "btn_color": "#28a745",

            # Backend
            "owner_field": "PreparingBy",
            "date_field": "PreparingAt",
            "track": False,
            "finish": False,
            # Nuevo
            "set_ware": True,
            "require_owner": True
        },

        "2": {
            "btn_txt": "TERMINAR PREPARACION",
            "accion": "FINALIZAR Y NOTIFICAR ENTREGA A COURIER",
            "next_id": 3,
            "next_name": "EN TRANSITO",
            "isFinal": False,
            "btn_color": "#ffc107",

            # Backend
            "owner_field": "PreparingBy",
            "date_field": None,
            "track": True,
            "finish": True,
            # Nuevo
            "set_ware": False,
            "require_owner": True
        },

        "3": {
            "btn_txt": "EN TRANSITO",
            "accion": "EN TRANSITO",
            "next_id": None,
            "next_name": "EN TRANSITO",
            "isFinal": True,
            "btn_color": "#6c757d",

            # Backend
            "owner_field": None,
            "date_field": None,
            "track": False,
            "finish": True,
            # Nuevo
            "set_ware": False
        }

    },

    "PICKUP": {

        "1": {
            "btn_txt": "ATENDER",
            "accion": "ATENDER",
            "next_id": 2,
            "next_name": "FINALIZAR PREPARACION Y NOTIFICAR RECOJO",
            "isFinal": False,
            "btn_color": "#28a745",

            "owner_field": "PreparingBy",
            "date_field": None,
            "track": False,
            "finish": False,
            # Nuevo
            "set_ware": False,
            "require_owner": True
        },

        "2": {
            "btn_txt": "TERMINAR PREPARACION",
            "accion": "FINALIZAR PREPARACION Y NOTIFICAR RECOJO A CLIENTE",
            "next_id": 3,
            "next_name": "ENTREGAR",
            "isFinal": False,
            "btn_color": "#ffc107",

            "owner_field": "PreparingBy",
            "date_field": "PreparingAt",
            "track": False,
            "finish": False,
            # Nuevo
            "set_ware": False,
            "require_owner": True
        },

        "3": {
            "btn_txt": "TERMINAR ENTREGA",
            "accion": "ENTREGAR A CLIENTE",
            "next_id": 4,
            "next_name": "ENTREGADO",
            "isFinal": False,
            "btn_color": "#ffc107",

            "owner_field": "PreparingBy",
            "date_field": None,
            "track": False,
            "finish": True,
            # Nuevo
            "set_ware": False,
            "require_owner": False
        },

        "4": {
            "btn_txt": "ENTREGADO",
            "accion": "ENTREGADO",
            "next_id": None,
            "next_name": "ENTREGADO",
            "isFinal": True,
            "btn_color": "#6c757d",

            "owner_field": None,
            "date_field": None,
            "track": False,
            "finish": True,
            # Nuevo
            "set_ware": False,
            "require_owner": False
        }

    }

}


def obtener_config(ship_type: str, step: int):
    """
    Retorna la configuración de una etapa del flujo.
    """
    return pasos_aprobacion.get(ship_type, {}).get(str(step))
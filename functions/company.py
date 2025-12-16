def get_all_companies(data: list = []):
    return {
        "CardCode": data["cardCode"],
        "CardName": '' if data["docName"] is None else data["docName"],
        "Address": '' if data["address"] is None else data["address"],
        "Active": bool(data["active"][-1]),
        "CardType": '' if data["type"] is None else data["type"],
        "LicTradNum": '' if data["LicTradNum"] is None else data["LicTradNum"],
        "DocType": '' if data["DocType"] is None else data["DocType"],
        "ContactPerson": '' if data["contact_name"] is None else data["contact_name"],
        "Phone": '' if data["Phone"] is None else data["Phone"],
        "E_Mail": '' if data["Email"] is None else data["Email"],
        "City": data["dep_name"] if "dep_name" in data else ''
    }

def get_ubigeos_format(data: list = []):
    return {
        "id": data[0],
        "text": data[1],
    }


def get_company_foredit(data_list=[]):
    # --- 1. Campos comunes que siempre se copian ---
    campos_comunes = {
        'tipo_socio',
        'tipo_documento',
        'numero_documento',
        'codigo_socio',
        'nombre',
        'nombre_comercial',
        'direccion',
        'estado',
        'condicion',
        'moneda',
        'condicion_pago',
        "dep_id",
        "pro_id",
        "dis_id",
        "dep_name",
        "pro_name",
        "dis_name"
    }

    # Tomamos los valores comunes del primer diccionario
    base = {k: data_list[0][k] for k in campos_comunes}

    # ---- NUEVA LÓGICA PARA DEPARTAMENTO / PROVINCIA / DISTRITO ----
    # Helper interno
    def construir_ubicacion(prefix: str, data={}):
        """
        Construye el dict final para departamento/provincia/distrito.
        prefix: 'dep', 'pro', 'dis'
        """
        id_val = data.get(f"{prefix}_id")
        name_val = data.get(f"{prefix}_name")

        if id_val is None:
            return None

        return {
            "id": id_val,
            "name": name_val
        }

    base["departamento"] = construir_ubicacion(prefix="dep", data=base)
    base["provincia"] = construir_ubicacion(prefix="pro", data=base)
    base["distrito"] = construir_ubicacion(prefix="dis", data=base)

    # --- Función auxiliar para convertir default ---
    def parse_default(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value == 1
        return False

    # --- 2. Construcción de contactos ---
    contactos = {}

    # Caso A: solo un elemento y id es None
    if len(data_list) == 1 and data_list[0].get("id") is None:
        contactos = {
            "1": {
                "nombre": None,
                "telefono": None,
                "correo": None,
                "default": True
            },
            "2": {
                "nombre": None,
                "telefono": None,
                "correo": None,
                "default": False
            }
        }

    # Caso B: solo un elemento y id existe
    elif len(data_list) == 1 and data_list[0].get("id") is not None:
        item = data_list[0]
        id_str = str(item["id"])

        contactos[id_str] = {
            "nombre": item.get("nombre_contacto"),
            "telefono": item.get("telefono"),
            "correo": item.get("correo"),
            "default": parse_default(item.get("default", 1))  # por defecto True
        }

        # completar el segundo contacto si no existe
        if id_str != "2":
            contactos["2"] = {
                "nombre": None,
                "telefono": None,
                "correo": None,
                "default": False
            }

    # Caso C: llegan dos elementos con ids válidos (1 y 2)
    else:
        for item in data_list:
            id_str = str(item["id"])
            contactos[id_str] = {
                "nombre": item.get("nombre_contacto"),
                "telefono": item.get("telefono"),
                "correo": item.get("correo"),
                "default": parse_default(item.get("default", 0))
            }

    # --- Resultado final ---
    base["contactos"] = contactos
    base.pop("dep_id")
    base.pop("pro_id")
    base.pop("dis_id")
    base.pop("dep_name")
    base.pop("pro_name")
    base.pop("dis_name")

    return base


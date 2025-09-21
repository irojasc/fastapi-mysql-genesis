

def get_all_pricelist_format(data: list = []):
    result = {}

    for item in data:
        lista_key = f"LISTA_{item['code']}"
        if lista_key not in result:
            result[lista_key] = {
                "currency": "PEN",
                "validTo": None,
                "prices": []
            }
        # Añadir el producto a la lista correspondiente
        result[lista_key]["prices"].append({
            "idProduct": item["idProduct"],
            "pvNew": item["pvNew"],
            "dsct": item["dsct"]
        })

    return result
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


def get_all_companies(data: list = []):
    return {
        "CardCode": data[0],
        "CardName": '' if data[1] is None else data[1],
        "Address": '' if data[2] is None else data[2],
        "Active": bool(data[4][-1]),
        "CardType": '' if data[5] is None else data[5],
        "LicTradNum": '' if data[6] is None else data[6],
        "DocType": '' if data[8] is None else data[8],
        "ContactPerson": '' if data[14] is None else data[14],
        "Phone": '' if data[15] is None else data[15],
        "E_Mail": '' if data[16] is None else data[16],
        "City": '' if (data[17] is None) else data[17] if (len(data) == 18) else ''
    }

def get_ubigeos_format(data: list = []):
    return {
        "id": data[0],
        "text": data[1],
    }


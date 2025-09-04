def get_all_companies(data: list = []):
    return {
        "CardCode": data[0],
        "CardName": data[1],
        "Address": data[2],
        "E_Mail": "", #pendiente correcion
        "Phone": "", #pendiente correcion
        "Active": bool(data[4][-1]),
        "CardType": data[5],
        "LicTradNum": data[6],
        "ContactPerson": "", #pendiente correcion
        "City": data[13] if len(data) == 14 else None,
    }

#def get_all_companies(data: list = []):
#    return {
#        "docNum": data[0],
#        "docName": data[1],
#        "address": data[2],
#        "email": data[3],
#        "phone": data[4],
#        "active": bool(data[6][-1]),
#        "type": data[7],
#    }

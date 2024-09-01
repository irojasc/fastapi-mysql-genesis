

def get_all_companies(data: list = []):
    return {
        "docNum": data[0],
        "docName": data[1],
        "address": data[2],
        "email": data[3],
        "phone": data[4],
        "active": bool(data[6][-1]),
        "type": data[7],
    }

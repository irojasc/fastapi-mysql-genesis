import datetime

def changeBin2Bool(data):
    # Define the binary string
    valor = True if b'\x01' == data else False
    return valor

def get_all_inventory_data(data: list = []):
    tmpList = []
    for item in data:
        index = next((i for i, item_ in enumerate(tmpList) if item_["product"]["prdCode"] == '%s_%d' % (item[1], item[2])), None)
        if index is None:
            dict_data = {
                "product": {
                "id": item[2],
                "prdCode": '%s_%d' % (item[1], item[2]),
                "isbn": '' if item[3] is None else item[3],
                "title": item[4],
                "autor": item[5],
                "publisher": item[6],
                "dateOut": item[7].strftime('%Y-%m-%d') if bool(item[7]) else None,
                "lang": item[8],
                "pages": item[9],
                "weight": item[10],
                "cover": None if item[11] is None else changeBin2Bool(item[11]),
                "width": item[12],
                "height": item[13],
                "content": None,
                "itemCategory": None,
                "isDelete": False if item[24] is None else changeBin2Bool(item[24]),
                },
                "wareData": {}
            }
            dict_data["wareData"][item[0]] = {"qtyNew": item[14], "qtyOld": item[15], "qtyMinimun": item[16] , "qtyMaximum": item[23], "pvNew": item[17], "pvOld": item[18], "loc": item[19], "isEnabled": changeBin2Bool(item[20]), "dsct": item[21], "idWare": item[22]}
            tmpList.append(dict_data)
        else:
            tmpList[index]["wareData"][item[0]] = {"qtyNew": item[14], "qtyOld": item[15], "qtyMinimun": item[16] , "qtyMaximum": item[23], "pvNew": item[17], "pvOld": item[18], "loc": item[19], "isEnabled": changeBin2Bool(item[20]), "dsct": item[21], "idWare": item[22]}

    return tmpList

def get_all_active_transfer(data: list = []):
    myList = []
    try:
        for item in data:
            #verifica si el codeTS existe en myList
            index = next((index for (index, d) in enumerate(myList) if d["codeTS"] == item[0]), None)
            #en caso de que no exista, lo crea por primera vez
            if not(isinstance(index, int)):
                myList.append({
                    "codeTS": item[0],
                    "fromWare": item[1],
                    "toWare": item[2],
                    "fromUser": item[3],
                    "toUser": item[4],
                    "fromDate": item[5] and item[5].strftime("%d-%m-%Y"),
                    "toDate": item[6] and item[6].strftime("%d-%m-%Y"),
                    "state": item[7],
                    "cardCode": item[9],
                    "cardName": item[10],
                    "note": item[8],
                    "operation": item[11],
                    "reason": item[12],
                    "products": [
                        {
                            "id": item[13],
                            "isbn": item[14],
                            "title": item[15],
                            "qtyNew": item[16],
                            "qtyOld": item[17],
                        }
                    ]
                })
            #caso contario agrega el producto con sus cantidades
            else:
                myList[index]["products"].append(
                    {
                            "id": item[13],
                            "isbn": item[14],
                            "title": item[15],
                            "qtyNew": item[16],
                            "qtyOld": item[17],
                    })

        return (myList, 'Ok')
    except Exception as e:
        return ([], str(e))
                        
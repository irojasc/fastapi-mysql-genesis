import datetime

def changeBin2Bool(data):
    # Define the binary string
    valor = True if b'\x01' == data else False
    return valor

def get_all_inventory_data(data: list = []):
    tmpList = []
    for item in data:
        index = next((i for i, item_ in enumerate(tmpList) if item_["product"]["prdCode"] == '%s_%d' % (item["item_code"], item["id_product"])), None)
        if index is None:
            dict_data = {
                "product": {
                "id": item["id_product"],
                "prdCode": '%s_%d' % (item["item_code"], item["id_product"]),
                "isbn": '' if item["isbn"] is None else item["isbn"],
                "title": item["title"],
                "autor": item["autor"],
                "publisher": item["publisher"],
                "dateOut": item["dateOut"].strftime('%Y-%m-%d') if bool(item["dateOut"]) else None,
                "lang": item["language"],
                "pages": item["pages"],
                "weight": item["weight"],
                "cover": None if item["cover"] is None else changeBin2Bool(item["cover"]),
                "width": item["width"],
                "height": item["height"],
                "content": None,
                "itemCategory": None,
                "isDelete": False if item["isDelete"] is None else changeBin2Bool(item["isDelete"]),
                ##NUEVOS CAMPOS PARA FACTURACION
                "InvntItem": item["InvntItem"], 
                "SellItem": item["SellItem"], 
                "BuyItem": item["BuyItem"], 
                "InvntryUom": item["InvntryUom"], 
                "LastPurPrc": item["LastPurPrc"], 
                "LastProvider": item["LastProvider"], 
                "VatBuy": item["VatBuy"], 
                "VatSell": item["VatSell"]
                },
                "wareData": {}
            }
            dict_data["wareData"][item["ware_code"]] = {"qtyNew": item["qtyNew"], "qtyOld": item["qtyOld"], "qtyMinimun": item["qtyMinimun"] , "qtyMaximum": item["qtyMaximum"], "pvNew": item["pvNew"], "pvOld": item["pvOld"], "loc": item["loc"], "isEnabled": changeBin2Bool(item["isEnabled"]), "dsct": item["dsct"], "idWare": item["idWare"]}
            tmpList.append(dict_data)
        else:
            tmpList[index]["wareData"][item["ware_code"]] = {"qtyNew": item["qtyNew"], "qtyOld": item["qtyOld"], "qtyMinimun": item["qtyMinimun"] , "qtyMaximum": item["qtyMaximum"], "pvNew": item["pvNew"], "pvOld": item["pvOld"], "loc": item["loc"], "isEnabled": changeBin2Bool(item["isEnabled"]), "dsct": item["dsct"], "idWare": item["idWare"]}

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
                            "autor": item[16],
                            "publisher": item[17],
                            "qtyNew": item[18],
                            "qtyOld": item[19],
                            "pvWare": item[20] if len(item) > 20 else None, #<--este valor esta retornando como float
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
                            "autor": item[16],
                            "publisher": item[17],
                            "qtyNew": item[18],
                            "qtyOld": item[19],
                            "pvWare": item[20] if len(item) > 20 else None, #<--este valor esta retornando como float
                    })

        return (myList, 'Ok')
    except Exception as e:
        return ([], str(e))
                        

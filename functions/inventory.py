def changeBin2Bool(data):
    # Define the binary string
    return True if b'\x01' == data else False

def get_all_inventory_data(data: list = []):
    tmpList = []
    for item in data:
        index = next((i for i, item_ in enumerate(tmpList) if item_["product"]["prdCode"] == '%s_%d' % (item[1], item[2])), None)
        if index is None:
            dict_data = {
                "product": {
                "id": item[2],
                "prdCode": '%s_%d' % (item[1], item[2]),
                "isbn": item[3],
                "title": item[4],
                "autor": item[5],
                "publisher": item[6],
                "dateOut": item[7].strftime('%Y-%m-%d') if bool(item[7]) else None,
                "lang": item[8],
                "pages": item[9],
                "edition": item[10],
                "cover": changeBin2Bool(item[11]),
                "width": item[12],
                "height": item[13],
                "content": None,
                "itemCategory": None
                },
                "wareData": {}
            }
            dict_data["wareData"][item[0]] = {"qtyNew": item[14], "qtyOld": item[15], "qtyMinimun": item[16] ,"pvNew": item[17], "pvOld": item[18], "loc": item[19], "isEnabled": changeBin2Bool(item[20]), "dsct": item[21], "idWare": item[22]}
            tmpList.append(dict_data)
        else:
            tmpList[index]["wareData"][item[0]] = {"qtyNew": item[14], "qtyOld": item[15], "qtyMinimun": item[16] ,"pvNew": item[17], "pvOld": item[18], "loc": item[19], "isEnabled": changeBin2Bool(item[20]), "dsct": item[21], "idWare": item[22]}

    return tmpList

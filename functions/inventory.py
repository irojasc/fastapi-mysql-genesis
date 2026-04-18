from functions.catalogs import obtenerTiempo
from sqlalchemy import select, delete, insert, update
from sqlalchemy.orm import Session

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
    

def sync_product_categories(
        sessionx,
        product_id: int,
        desired: list[dict],
        ProductCategories = None
    ):
    try:
        # 1️⃣ Estado actual en DB
        rows = sessionx.execute(
            select(
                ProductCategories.c.idCategory,
                ProductCategories.c.isMain
                )
            .where(ProductCategories.c.idProduct == product_id)
        ).mappings().all()

        db_map = {
                row["idCategory"]: row["isMain"]
                for row in rows
            }
        
        incoming_map = {
            item["idCategory"]: item["isMain"]
            for item in desired
        }

        # 2️⃣ INSERT
        to_insert = [
            {
                "idProduct": product_id,
                "idCategory": cat_id,
                "isMain": is_main
            }
            for cat_id, is_main in incoming_map.items()
            if cat_id not in db_map
        ] #inserta si el key del desired list no esta en la lista general

        if to_insert: #verifica si  hay opciones para cambiar
            sessionx.execute(
                insert(ProductCategories),
                to_insert
            )

        # 3️⃣ UPDATE
        for cat_id, is_main in incoming_map.items():
            if cat_id in db_map and db_map[cat_id] != is_main:
                stmt = (
                    update(ProductCategories)
                    .where(
                        ProductCategories.c.idProduct == product_id,
                        ProductCategories.c.idCategory == cat_id
                    )
                    .values(isMain=is_main)
                )
                sessionx.execute(stmt)

        # 4️⃣ DELETE
        to_delete = [
            cat_id
            for cat_id in db_map
            if cat_id not in incoming_map
        ]

        if to_delete:
            stmt = (
                delete(ProductCategories)
                .where(
                    ProductCategories.c.idProduct == product_id,
                    ProductCategories.c.idCategory.in_(to_delete)
                )
            )
            sessionx.execute(stmt)
                
        return True, 'Ok!'
    except Exception as e:
        print(f"An error ocurred: {e}")
        return False, e

def sync_product_languages(
        sessionx: Session,
        product_id: int,
        langs: list[dict],
        ProductLanguage = None
    ):
    try:
        # -------------------------
        # 1️⃣ ids desde la lista
        # -------------------------
        new_ids = {lang["idLang"] for lang in langs if "idLang" in lang}

        # -------------------------
        # 2️⃣ ids actuales en DB
        # -------------------------
        stmt = select(ProductLanguage.c.idLanguage).where(
            ProductLanguage.c.idProduct == product_id
        )
        current_ids = {
            row.idLanguage for row in sessionx.execute(stmt)
        }

        # -------------------------
        # 3️⃣ diferencias
        # -------------------------
        to_insert = new_ids - current_ids
        to_delete = current_ids - new_ids

        # -------------------------
        # 4️⃣ DELETE masivo
        # -------------------------
        if to_delete:
            stmt = delete(ProductLanguage).where(
                ProductLanguage.c.idProduct == product_id,
                ProductLanguage.c.idLanguage.in_(to_delete)
            )
            sessionx.execute(stmt)

        # -------------------------
        # 5️⃣ INSERT masivo
        # -------------------------
        if to_insert:
            rows = [
                {
                    "idProduct": product_id,
                    "idLanguage": lang_id
                }
                for lang_id in to_insert
            ]

            stmt = insert(ProductLanguage).values(rows)
            sessionx.execute(stmt)

        return True, 'Ok'

    except Exception as e:
        print(f"An error ocurred: {e}")
        return False, e


def build_path(category_id: int, cat_by_id: dict):
    path = []
    current = cat_by_id[category_id]

    while current:
        path.append(current["id"])
        parent_id = current["id_parent"]
        current = cat_by_id.get(parent_id)

    return list(reversed(path))

def get_root(category_id: int, cat_by_id: dict):
    current = cat_by_id[category_id]
    while current["id_parent"] is not None:
        current = cat_by_id[current["id_parent"]]
    return current

def makeSelectedCategories(lines = [], cat_by_id = {}):
    try:
        result = []

        for row in lines:
            category = cat_by_id[row["idUltimo"]]
            root = get_root(row["idUltimo"], cat_by_id)
            path = build_path(row["idUltimo"], cat_by_id)

            if category["level"] == 1:
                # 🟢 Casuística especial: categoría raíz
                result.append({
                    "levelRaiz": root["level"],
                    "idRaiz": root["id"],
                    "nameRaiz": root["name"],

                    "levelUltimo": None,
                    "idUltimo": None,
                    "nameUltimo": None,

                    "isMain": row["isMain"],
                    "path": path,   # ejemplo: [2]
                })
            else:
                # 🔵 Caso normal
                result.append({
                    "levelRaiz": root["level"],
                    "idRaiz": root["id"],
                    "nameRaiz": root["name"],

                    "levelUltimo": category["level"],
                    "idUltimo": category["id"],
                    "nameUltimo": category["name"],

                    "isMain": row["isMain"],
                    "path": path,   # ejemplo: [2, 15, 18]
                })

        return result, True
    except Exception as e:
        return [], False
    

def validateWebFields(webWareExists=None, camposWeb=(None, None, None), idProduct= None, isbnProduct=None):
    def agregar_id_slug(id: int = None, slug:str = ''):
        return slug + "-" +  str(id)

    
    slug = camposWeb[0]
    metatitle = camposWeb[1]
    metadesc = camposWeb[2]
    isbn = isbnProduct
    seoedidate = None

    if webWareExists and (not(slug) or not(metatitle) or not(metadesc)):
        return False, "Debe registrar los 3 MetaDatos si activa almacen WEB", None, None
    
    if not(webWareExists) and (slug or metatitle or metadesc):
        return False, "Active almacen WEB para poder registrar los 3 MetaDatos", None, None
    
    if webWareExists and slug and metatitle and metadesc: #Registra slug siempre y cuando se cumpla los tres campos
        slug_final = agregar_id_slug(idProduct, slug) if slug is not None and not(isbn) else slug

        utc, utc_format, now_lima = obtenerTiempo()
        
        return True, "OK!", slug_final, utc #<- el tiempo cuando se agrega el slug
    
    if not(webWareExists) and not(slug) and not(metatitle) and not(metadesc):

        return True, "OK!", slug, None
    
    return False, 'Error', None, None


def validateSEOFielChanged(seodateedit=None, incomingData=None, currentData=None, new_langs_ids=[], current_langs_ids=[]):

    try:
        #CAMPOS QUE SE CONDIERAN NECESARIOS PARA REPORTAR LA ACTUALIZACION EN EL SLUG
        SEO_FIELDS = {
                "autor",
                "content",
                "cover",
                "dateOut",
                "height",
                "idItem",
                "isbn",
                "large",
                "MetaDesc",
                "MetaTitle",
                "pages",
                "publisher",
                "Slug",
                "title",
                "weight",
                "width",
                      }
        
        # 2. Creamos la "copia útil": solo llaves que están en nuestra lista blanca
        update_date = {k: v for k, v in incomingData.items() if k in SEO_FIELDS}

        seo_changed = False

        # 3. Comparar conjuntos
        if new_langs_ids != current_langs_ids:
            seo_changed = True

        # 3. Iterar y comparar
        for key, value in update_date.items():
            current_value = getattr(currentData, key)
            # Si el valor es diferente al que ya tenemos en DB
            if current_value != value:
                # Si el campo que cambió está en nuestra lista SEO, activamos la bandera
                if key in SEO_FIELDS:
                    seo_changed = True

        if seo_changed:
            utc, utc_format, now_lima = obtenerTiempo()
            seodateedit = utc

        return seodateedit, seo_changed
    
    except Exception as e:
        print(f"""{e}""")
        return seodateedit, False
    


    
                        

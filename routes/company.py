from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
# from sqlalchemy import select, insert, delete, asc, func
from sqlalchemy import select, asc, func, insert, and_, or_
from utils.validate_jwt import jwt_dependecy
from config.db import con, session
from sqlmodel.company import Company
from sqlmodel.banks import Banks
from sqlmodel.paymentterms import PaymentTerms
from sqlmodel.ocur import OCUR
from sqlmodel.companycontacts import CompanyContacts
from sqlmodel.companyaccounts import CompanyAccounts
from basemodel.company import BusinessPartner
from sqlmodel.ubigeo import Ubigeo
from functions.company import get_all_companies, get_ubigeos_format
from functions.catalogs import normalize_last_sync
from service.company import get_partner_by_ruc_dni # consume servicio de reniec o sunat
from routes.catalogs import Get_Time
from datetime import datetime
import json

company_route = APIRouter(
    prefix = '/company',
    tags=['Company']
)

@company_route.get("/business_partner/", status_code=200)
async def Get_Business_Partner_By_CardCode(CardCode:str=None, jwt_dependency: jwt_dependecy = None):
    """La parte de obtener Business partner por CardCode no esta desarrollada"""
    returnedValue = {"body": {}, "message": "ok"}
    status_code = 200
    try:
        if CardCode is not None:
            ##EDITAAAR VA EN ESTAR PARTE
            returnedValue.update({"body":{}})
        else:
            #Consulta bancos
            banks = session.query(Banks.c.BankCodeApi, Banks.c.BankName) \
            .order_by(Banks.c.BankName.asc()) \
            .all()

            #Consulta terminos de pago
            paymentterms = session.query(PaymentTerms.c.TermCode, PaymentTerms.c.TermName) \
            .order_by(PaymentTerms.c.TermName.asc()) \
            .all()

            #Consulta monedas
            currency = session.query(OCUR.c.CurrCode, OCUR.c.CurrName) \
            .all()

            returnedValue.update({"body":{
                "tipo_socio": None, # S o P : Supplier o Provider
                "tipo_documento": None, #
                "numero_documento": None,
                "nombre": None,
                "nombre_comercial": None,
                "direccion": None,
                "departamento": None,
                "provincia": None,
                "distrito": None,
                "estado": None,
                "condicion": None,
                "contactos": {
                    "1": {"nombre": None, "telefono": None, "correo": None, "default": True},
                    "2": {"nombre": None, "telefono": None, "correo": None, "default": False}
                },
                # "cuenta_bancaria": {"tipo_cuenta": None, "tipo_moneda": None, "banco": None, "n_cuenta": None, "n_cci": None, "titular": None },
                "cuenta_bancaria": {"tipo_cuenta": None, "banco": None, "n_cuenta": None, "n_cci": None, "titular": None }, #tipo de moneda sale por que ira en condiciones generales
                "condicion_pago": "CASH", #SE DEFINE POR DEFECTO CONTADO
                "moneda": "PEN", #SE DEFINE POR DEFECTO SOLES
                "bancos": list(map(lambda x: {"id": x[0], "name": x[1]}, banks)),
                "condiciones_pago": list(map(lambda x: {"id": x[0], "name": x[1]}, paymentterms)),
                "monedas": list(map(lambda x: {"id": x[0], "name": x[1]}, currency))
            }})

    except Exception as e:
        session.rollback()
        print(f"An error ocurred: {e}")
        returnedValue.update({"message": f"An error ocurred: {e}"})
        status_code=422,
    finally:
        session.close()
        return JSONResponse(
            status_code=status_code,
            content=returnedValue
        )

@company_route.post("/business_partner/", status_code=201)
async def Create_New_Business_Partner(BusinessPartner: BusinessPartner, jwt_dependency: jwt_dependecy = None):
    returnedValue = {"body": {}, "message": "Socio creado!!"}
    status_code = 201
    try:
        #HORA DE REGISTRO
        create_date = await Get_Time()

        #OBTIENE EL IDUBIGEO
        ubigeo = session.query(Ubigeo.c.idUbigeo, Ubigeo.c.dis_name).\
                filter(Ubigeo.c.dep_id == BusinessPartner.departamento). \
                filter(Ubigeo.c.pro_id == BusinessPartner.provincia). \
                filter(Ubigeo.c.dis_id == BusinessPartner.distrito). \
                first() 

        #INSERTA DATO SOCIO DE NEGOCIO
        defineCardCode = f"""{'P' if BusinessPartner.tipo_socio == 'S' else 'C'}{BusinessPartner.numero_documento}"""
        stmt = (
            insert(Company).
            values(
                cardCode= defineCardCode,
                docName= BusinessPartner.nombre or None,
                address= BusinessPartner.direccion or None,
                idUbigeo= ubigeo.idUbigeo if ubigeo is not None else None,
                type= BusinessPartner.tipo_socio or None,
                LicTradNum= BusinessPartner.numero_documento or None,
                creationDate= create_date["lima_bd_format"] or None,
                DocType= BusinessPartner.tipo_documento or None,
                CardStatus= BusinessPartner.estado or None,
                CardCond= BusinessPartner.condicion or None,
                BusinessName= BusinessPartner.nombre_comercial or None,
                TermCode= BusinessPartner.condicion_pago or None,
                UserSign= BusinessPartner.usuario_creacion or None,
                Currency= BusinessPartner.moneda or None
            )
        )
        res_partner = session.execute(stmt)
        session.commit()
        rowsAffected = res_partner.rowcount
        # print(rowsAffected)
        if(rowsAffected > 0): #VERIFICA QUE REGISTRA SOCIO PARA REGISTRAR CONTACTOS Y CUENTAS
            #CREA CONTACTOS
            if len(BusinessPartner.contactos) > 0:
                for contact in BusinessPartner.contactos:
                    stmt1 = (insert(CompanyContacts).
                            values(
                                cardCode=defineCardCode,
                                LineId=contact.id,
                                Name=contact.nombre,
                                Phone=contact.telefono,
                                Email=contact.correo,
                                DefaultContact=int(contact.default),
                                creationDate=create_date["lima_bd_format"] or None,
                        )
                    )
                    res_contact = session.execute(stmt1)
                    if (res_contact.rowcount > 0):
                        print(f"Grabo contacto {contact.nombre}") 
                    else:
                        returnedValue.update({"message": "Error al intentar grabar contactos"})
                        break
                session.commit()
            else:
                print("No registra contactos")

            #CREA CUENTAS BANCARIAS
            if len(BusinessPartner.cuenta_bancaria) > 0:
                for bankAccount in BusinessPartner.cuenta_bancaria:
                    stmt2 = (insert(CompanyAccounts).
                            values(
                            cardCode=defineCardCode,
                            LineId=bankAccount.id,
                            AccountType=bankAccount.tipo_cuenta,
                            BankCodeApi=bankAccount.banco,
                            AccountNumber=bankAccount.n_cuenta,
                            InterbankNumber=bankAccount.n_cci,
                            AccountHolder=bankAccount.titular,
                        )
                    )
                    res_account = session.execute(stmt2)
                    if (res_account.rowcount > 0):
                        print(f"Grabo cuenta bancaria de cci {bankAccount.n_cci}") 
                    else:
                        returnedValue.update({"message": "Error al intentar grabar dato bancario"})
                        break
                session.commit()
            else:
                print("No registra cuenta bancaria")
            
            #RETORNAR SOCIO CREADO
            value = await Get_All_Business_Partners_By_Param(CardCode=defineCardCode)
            returnedValue.update({"body": value})

        else:
            status_code=422,
            returnedValue.update({"message": "Error al registrar socio"})

    except Exception as e:
        session.rollback()
        print(f"An error ocurred: {e}")
        returnedValue.update({"message": f"An error ocurred: {e}"})
        status_code=422,
    finally:
        session.close()
        return JSONResponse(
            status_code= status_code[0] if isinstance(status_code, tuple) else status_code,
            content=returnedValue
        )

@company_route.get("/ubigeos/", status_code=200)
async def Get_Ubigeo_From_Root(departamento_id:str=None, provincia_id:str=None, jwt_dependency: jwt_dependecy = None):
# async def Get_Ubigeo_From_Root(departamento_id:str=None, provincia_id:str=None):
    #root1: padre departamento
    #root2: padre provincia
    #nivel: 2: provincia, 3: distrito
    returned = []
    try:
        if (departamento_id is not None) and (provincia_id is None): #consulta provincias
            results = session.query(Ubigeo.c.pro_id, Ubigeo.c.pro_name) \
            .filter(Ubigeo.c.dep_id == departamento_id) \
            .group_by(Ubigeo.c.pro_id, Ubigeo.c.pro_name) \
            .order_by(Ubigeo.c.pro_id.asc()) \
            .all()
        elif (departamento_id is not None) and (provincia_id is not None): #consulta distritos
            results = session.query(Ubigeo.c.dis_id, Ubigeo.c.dis_name) \
            .filter(Ubigeo.c.dep_id == departamento_id) \
            .filter(Ubigeo.c.pro_id == provincia_id) \
            .group_by(Ubigeo.c.dis_id, Ubigeo.c.dis_name) \
            .order_by(Ubigeo.c.dis_id.asc()) \
            .all()
        else:
            results = []
        returned = list(map(get_ubigeos_format, results))
    except Exception as e:
        session.rollback()
        print(f"An error ocurred: {e}")
        return []
    finally:
        session.close()
        return returned

@company_route.get("/get_partner_data_from_sunat_reniec/", status_code=200)
async def Get_Partner_Data_By_Ruc_Dni(nDocument:str=None, tDocument:str= 'ruc', jwt_dependency: jwt_dependecy = None):
    """IMPORTANTE, ༼ つ ◕_◕ ༽つ DEBE SER EL MISMO FORMATO SI CAMBIA DE PROVEEDOR VVVV \n
    CUANDO NO EXISTE UBIGEO, RETORNA '-'
    """
    #DNI:... {'first_name': '', 'first_last_name': '', 'second_last_name': '', 'full_name': '', 'document_number': ''}
    #RUC:... {"razon_social":"", "numero_documento":"", "estado":"", "condicion":"", "direccion":"", "ubigeo":"", "via_tipo":"","via_nombre":"", "zona_codigo":"",
    #"zona_tipo":"", "numero":"", "interior":"", "lote":"", "dpto":"", "manzana":"", "kilometro":"", "distrito":"", "provincia":"", "departamento":"", "es_agente_retencion":true}
    returned = {}, 422
    try:
        params = {
            "numero": nDocument
        }
        response, status_code = await get_partner_by_ruc_dni(params=params, tdocument=tDocument)
        
        if 'ubigeo' in response: #realiza consulta a backend genesis
            result = session.query(Ubigeo.c.dep_name, Ubigeo.c.pro_name, Ubigeo.c.dis_name). \
            filter(func.concat(Ubigeo.c.dep_id,Ubigeo.c.pro_id,Ubigeo.c.dis_id) == response["ubigeo"]).\
            first()
            if(result) and isinstance(response, dict):
                response.update({"distrito_gene": result[2]})
                response.update({"provincia_gene": result[1]})
                response.update({"departamento_gene": result[0]})
                response.update({"distrito_opciones_gene": await Get_Ubigeo_From_Root(departamento_id=response["ubigeo"][:2], provincia_id=response["ubigeo"][2:4])}) # consulta distrito
                response.update({"provincia_opciones_gene": await Get_Ubigeo_From_Root(departamento_id=response["ubigeo"][:2])}) #consulta provincia
            else:
                response.update({"distrito_gene": None})
                response.update({"provincia_gene": None})
                response.update({"departamento_gene": None})
                response.update({"distrito_opciones_gene": []})
                response.update({"provincia_opciones_gene": []})
            
        if response is not None:
            returned = response , status_code
    except Exception as e:
        session.rollback()
        print(f"An error ocurred: {e}")
    finally:
        session.close()
        return JSONResponse(
        status_code=returned[1],
        content={
            "response": returned[0],
        }
    )


@company_route.get("/get_all_business_partners", status_code=200)
async def Get_All_Business_Partners_By_Param(CardType:str=None, CardCode:str=None, jwt_dependency: jwt_dependecy = None):
    """🚨Consulta sin parametros(todos los partners con 1 contacto) genera file .json en servidor backend"""
    #ACEPTARA PARAMETROS, C Y S: DONDE C es customer y S es Supplier
    returned = []
    try:
        if CardCode is None:
            if CardType is not None:
                stmt = (
                    select(Company, CompanyContacts.c.Name.label("contact_name"), CompanyContacts.c.Phone, CompanyContacts.c.Email, Ubigeo.c.dep_name)
                    .join(CompanyContacts, and_(Company.c.cardCode == CompanyContacts.c.cardCode, CompanyContacts.c.DefaultContact == 1), isouter=True)
                    .join(Ubigeo, Company.c.idUbigeo == Ubigeo.c.idUbigeo, isouter=True)
                    .where(Company.c.type == CardType)
                    .where(Company.c.active == 1)
                    .order_by(asc(Company.c.docName))
                )
                results = session.execute(stmt).mappings().all() #obtine en formato diccionario
                returned = list(map(get_all_companies,results))

            else: #si es None, trae todo los resultados
                stmt = (
                    select(Company, CompanyContacts.c.Name.label("contact_name"), CompanyContacts.c.Phone, CompanyContacts.c.Email, Ubigeo.c.dep_name)
                    .join(CompanyContacts, and_(Company.c.cardCode == CompanyContacts.c.cardCode, CompanyContacts.c.DefaultContact == 1), isouter=True)
                    .join(Ubigeo, Company.c.idUbigeo == Ubigeo.c.idUbigeo, isouter=True)
                    .where(Company.c.active == 1)
                    .order_by(asc(Company.c.docName))
                )
                results = session.execute(stmt).mappings().all() #obtine en formato diccionario
                returned = list(map(get_all_companies,results))
                utc_time = await Get_Time()
                returned = {"last_sync": utc_time["lima"], "partners" : returned}

                #EXPORTA EN JSON
                with open("partners.json", "w", encoding='utf8') as outfile:
                    json.dump(returned, outfile, ensure_ascii=False, indent=4)

        else:
            stmt = (
                select(Company, CompanyContacts.c.Name.label("contact_name"), CompanyContacts.c.Phone, CompanyContacts.c.Email, Ubigeo.c.dep_name)
                .join(CompanyContacts, and_(Company.c.cardCode == CompanyContacts.c.cardCode, CompanyContacts.c.DefaultContact == 1), isouter=True)
                .join(Ubigeo, Company.c.idUbigeo == Ubigeo.c.idUbigeo, isouter=True)
                .where(Company.c.cardCode == CardCode)
            )
            socio = session.execute(stmt).mappings().first() #obtine en formato diccionario
            value = list(map(get_all_companies, [socio] if (socio is not None) and not(isinstance(socio, list)) else []))
            returned = value[0] if len(value) else {}

    except Exception as e:
        print("rollback")
        session.rollback()
        print(f"An error ocurred: {e}")
        returned = []
    finally:
        session.close()
        return returned
    
@company_route.get("/lastchanges", status_code=200)
async def Get_Last_Company(last_sync: datetime = Query(..., description="Formato esperado: YYYY-MM-DDTHH:MM:SSZ (ISO8601)"), jwt_dependency: jwt_dependecy = None):
    try:
        #convertir el last_sync
        formated_lastsync = normalize_last_sync(last_sync) #resta 5 minutos para traer todos los cambios
        stmt = (
            select(Company, CompanyContacts.c.Name.label("contact_name"), CompanyContacts.c.Phone, CompanyContacts.c.Email, Ubigeo.c.dep_name)
            .join(CompanyContacts, and_(Company.c.cardCode == CompanyContacts.c.cardCode, CompanyContacts.c.DefaultContact == 1), isouter=True)
            .join(Ubigeo, Company.c.idUbigeo == Ubigeo.c.idUbigeo, isouter=True)
            .filter(or_(Company.c.creationDate >= formated_lastsync, 
                        Company.c.updateDate >= formated_lastsync,
                        CompanyContacts.c.creationDate >= formated_lastsync,
                        CompanyContacts.c.updateDate >= formated_lastsync
                        ))
            .order_by(asc(Company.c.docName))
        )

        results = session.execute(stmt).mappings().all() #obtine en formato diccionario
        returned = list(map(get_all_companies,results))
        utc_time = await Get_Time() #consulta hora actual del sistema
        # print('Consulta proveedores: Hora Lima: ', utc_time["lima"])
        returned = {"last_sync": utc_time["lima"], "partners" : returned}

    except Exception as e:
        print("rollback")
        session.rollback()
        print(f"An error ocurred: {e}")
        returned = {}
    finally:
        session.close()
        return returned
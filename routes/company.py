from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, insert, delete
from utils.validate_jwt import jwt_dependecy
from config.db import con, session
from utils.validate_jwt import jwt_dependecy
from sqlmodel.company import Company
from sqlmodel.ubigeo import Ubigeo
from basemodel.company import company
from functions.company import get_all_companies

company_route = APIRouter(
    prefix = '/company',
    tags=['Company']
)


@company_route.get("/", status_code=200)
async def Get_All_Companies(jwt_dependency: jwt_dependecy):
    returned = []
    try:
        results = session.query(Company).all()
        returned = list(map(get_all_companies,results))
    except Exception as e:
        session.rollback()
        print(f"An error ocurred: {e}")
        return []
    finally:
        session.close()
        return returned



@company_route.get("/supplier", status_code=200)
async def Get_All_Suppliers(jwt_dependency: jwt_dependecy):
    returned = []
    try:
        results = session.query(Company).where(Company.c.type == 'S').where(Company.c.active == 1).all()
        returned = list(map(get_all_companies,results))
    except Exception as e:
        print("rollback")
        session.rollback()
        print(f"An error ocurred: {e}")
        returned = []
    finally:
        session.close()
        return returned
    
@company_route.post("/newcompany")
async def post_new_company(company: company, jwt_dependency: jwt_dependecy):
    response = False
    try:
        result = session.query(Ubigeo).where(Ubigeo.c.dep_name == company.DocDepartamento.name).where(Ubigeo.c.pro_name == company.DocProvincia.name).where(Ubigeo.c.dis_name == company.DocDistrito.name).all()
        if bool(result):
            stmt = (
            insert(Company).
            values(
                cardCode = company.DocNum,
                docName= company.DocName,
                address= company.DocAddress,
                email= company.DocEmail,
                phone= company.DocPhone,
                idUbigeo= result[0][0],
                type= company.TipoEmpresa,
                )
            )
            response_1 = session.execute(stmt)
            session.commit()
            if(response_1.rowcount > 0):
                response = True
        else:
            stmt = (
            insert(Ubigeo).
            values(
                dep_id= company.DocDepartamento.id,
                pro_id= company.DocProvincia.id,
                dis_id= company.DocDistrito.id,
                dep_name= company.DocDepartamento.name,
                pro_name= company.DocProvincia.name,
                dis_name= company.DocDistrito.name,
                )
            )
            response_2 = session.execute(stmt)
            session.commit()
            if(response_2.rowcount > 0):
                result_1 = session.query(Ubigeo).where(Ubigeo.c.dep_name == company.DocDepartamento.name).where(Ubigeo.c.pro_name == company.DocProvincia.name).where(Ubigeo.c.dis_name == company.DocDistrito.name).all()
                stmt = (insert(Company).values(
                doc = company.DocNum,
                docName= company.DocName,
                address= company.DocAddress,
                email= company.DocEmail,
                phone= company.DocPhone,
                idUbigeo= result_1[0][0],
                type= company.TipoEmpresa,
                )
                )
                response_3 = session.execute(stmt)
                session.commit()
                if(response_3.rowcount > 0):
                    response = True
    except Exception as e:
        print("rollback")
        session.rollback()
        print(f"An error ocurred: {e}")
        response = False
    finally:
        session.close()
        if response:
            raise HTTPException(status_code=201, detail="Something wrong happens")
        else:
            raise HTTPException(status_code=304, detail="Something wrong happens")
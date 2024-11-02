import os
import json
import gspread
from fastapi import APIRouter, Depends, HTTPException
from utils.validate_jwt import jwt_dependecy
from google.oauth2.service_account import Credentials
from google.auth.exceptions import GoogleAuthError
from gspread.exceptions import GSpreadException
from basemodel.product import product_maintenance
from dotenv import load_dotenv
load_dotenv(override=True)

credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')

# Parse the JSON string into a dictionary
credentials_dict = json.loads(credentials_json)

# creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
creds = Credentials.from_service_account_info(credentials_dict, scopes=["https://www.googleapis.com/auth/spreadsheets"])



request_route = APIRouter(
    prefix = '/request',
    tags=['Request']
)

@request_route.post("/product_maintenance", status_code=200)
async def get_last_row(jwt_dependency: jwt_dependecy, product_maintenance: product_maintenance):
    data = [
        product_maintenance.code,
        product_maintenance.isbn ,
        product_maintenance.title,
        product_maintenance.autor,
        product_maintenance.publisher,
        '', #proveedor
        '', #lenguaje
        '', #paginas
        '', #cubierta
        '', #ancho
        '', #alto
        product_maintenance.pv,
        product_maintenance.pvp,
        '', #"edicion"
        '', #"año mes edicion"
        product_maintenance.warehouse,
        product_maintenance.rqType,
        product_maintenance.asker,
        product_maintenance.date,
        ]
    try:
        client = gspread.authorize(creds)
        sheet_id = '1ArWWeiC9JsiLJw021O3EzS9i1XLMAbg0Z8S9b-5rmtY'
        sheet = client.open_by_key(sheet_id)
        row_counts = sheet.sheet1.row_count
        sheet.sheet1.append_row(data)
        return {"state": True}
    except GoogleAuthError as auth_error:
        print(f"Authentication error: {auth_error}")
        return {"state": False}
    except GSpreadException as gs_error:
        print(f"Gspread error: {gs_error}")
        return {"state": True}
    except Exception as e:
        print(f"get_last_row:get: An error ocurred: {e}")
        return {"state": True}


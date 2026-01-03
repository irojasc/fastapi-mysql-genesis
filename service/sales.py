import requests
from config.db import MIFACT_TOKEN, MIFACT_ENDPOINT, MIFACT_MIRUC
import httpx
import json

# params: cuerpo solicitado por mifact
async def post_sales_document(params:dict={}):
    if params:
        params.update({"TOKEN": MIFACT_TOKEN}) # <- agrega token mifact
        try:
            # print(json.dumps(params, indent=4, ensure_ascii=False))
            endpoint = f"""{MIFACT_ENDPOINT}SendInvoice"""
            response = requests.post(endpoint, json=params, timeout=30)
            return response.json(), response.status_code
        except Exception as e:
            print(f'Error at post_sales_document: {e}')
            return {"msg": e}, 422
    else:
        return None, 422
    
# consulta estado
async def check_sales_document_status(client: httpx.AsyncClient, params: dict = {}):
    if not params:
        return None, 422
    
    payload = {**params, "TOKEN": MIFACT_TOKEN, "NUM_NIF_EMIS": MIFACT_MIRUC}
    endpoint = f"{MIFACT_ENDPOINT}GetEstatusInvoice"

    try:
        # Aquí usamos el cliente asíncrono que pasamos por parámetro
        response = await client.post(endpoint, json=payload, timeout=30.0)
        return response.json(), response.status_code
    except Exception as e:
        print(f'Error at check_sales_document_status: {e}')
        return {"msg": str(e)}, 422
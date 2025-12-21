import requests
from config.db import MIFACT_TOKEN, MIFACT_ENDPOINT
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
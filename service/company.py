import requests
from config.db import DECOLECTA_TOKEN

# tDocument: Tipo de documento, puede ser ruc o dni
async def get_partner_by_ruc_dni(params=None, tdocument=None):
    agent = 'sunat' if tdocument == 'ruc' else 'reniec' if tdocument == 'dni' else ''
    if params:
        try:
            endpoint = f"""https://api.decolecta.com/v1/{agent}/{tdocument}"""
            headers = {"Authorization": 'Bearer %s' % DECOLECTA_TOKEN}
            response = requests.get(endpoint, params=params, headers=headers, timeout=30)
            return response.json(), response.status_code
        except Exception as e:
            print(f'Error at get_partner_by_ruc_dni: {e}')
            return {"msg": e}, 422
    else:
        return None, 422
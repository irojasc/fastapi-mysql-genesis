from config.db import DECOLECTA_TOKEN
import httpx

# tDocument: Tipo de documento, puede ser ruc o dni
async def get_partner_by_ruc_dni(client: httpx.AsyncClient = None, params=None, tdocument=None):
    agent = 'sunat' if tdocument == 'ruc' else 'reniec' if tdocument == 'dni' else ''
    if params:
        try:
            endpoint = f"""https://api.decolecta.com/v1/{agent}/{tdocument}"""
            headers = {"Authorization": f"Bearer {DECOLECTA_TOKEN}"}

            response = await client.get(
                endpoint, 
                params=params, 
                headers=headers, 
                timeout=30.0
            )

            return response.json(), response.status_code
        
        except httpx.HTTPStatusError as e:
            # Errores devueltos por la API (404, 500, etc.)
            return e.response.json(), e.response.status_code
        
        except httpx.RequestError as e:
            return {"msg": "Error de conexión con el proveedor externo"}, 502
        
        except Exception as e:
            print(f'Error at get_partner_by_ruc_dni: {e}')
            return {"msg": str(e)}, 422
    else:
        return None, 422


# headers = {"Authorization": 'Bearer %s' % DECOLECTA_TOKEN}
# response = requests.get(endpoint, params=params, headers=headers, timeout=30)
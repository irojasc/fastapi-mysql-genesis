from config.db import MIFACT_TOKEN, MIFACT_ENDPOINT, MIFACT_MIRUC
import httpx
# import json

# params: cuerpo solicitado por mifact
async def post_sales_document(client: httpx.AsyncClient = None, params:dict={}):
    if not params:
        return None, 422
    
    # 1. Preparación de datos
    params.update({"TOKEN": MIFACT_TOKEN})
    endpoint = f"{MIFACT_ENDPOINT}SendInvoice"

    try:
        # 2. Llamada asíncrona usando el cliente inyectado
        # Nota: el timeout en httpx se puede pasar directamente aquí o configurarlo en el cliente
        response = await client.post(
            endpoint, 
            json=params, 
            timeout=30.0
        )
        
        # # 3. Lanzar excepción si el status_code es 4xx o 5xx (Opcional pero recomendado)
        # response.raise_for_status()

        return response.json(), response.status_code

    except httpx.HTTPStatusError as e:
        print(str(e))
        return e.response.json(), e.response.status_code
    except httpx.RequestError as e:
        print(str(e))
        return {"msg": "External API connection error"}, 502
    except Exception as e:
        print(str(e))
        return {"msg": str(e)}, 422


# consulta estado
async def check_sales_document_file(client: httpx.AsyncClient, params: dict = {}): #este servicio tambien trae xml, cdr
    if not params:
        return None, 422
    
    payload = {**params, "TOKEN": MIFACT_TOKEN, "NUM_NIF_EMIS": MIFACT_MIRUC}
    endpoint = f"{MIFACT_ENDPOINT}GetInvoice"

    try:
        # Aquí usamos el cliente asíncrono que pasamos por parámetro
        response = await client.post(endpoint, json=payload, timeout=30.0)
        return response.json(), response.status_code
    except Exception as e:
        print(f'Error at check_sales_document_status: {e}')
        return {"msg": str(e)}, 422
    
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

# cancela / anula documento
async def cancel_sales_document(client: httpx.AsyncClient, params: dict = {}):
    if not params:
        return None, 422
    
    payload = {**params, "TOKEN": MIFACT_TOKEN, "NUM_NIF_EMIS": MIFACT_MIRUC, "COD_TIP_NIF_EMIS": "6"}
    endpoint = f"{MIFACT_ENDPOINT}LowInvoice"

    try:
        # Aquí usamos el cliente asíncrono que pasamos por parámetro
        response = await client.post(endpoint, json=payload, timeout=30.0)
        return response.json(), response.status_code
    except Exception as e:
        print(f'Error at cancel_sales_document: {e}')
        return {}, 422
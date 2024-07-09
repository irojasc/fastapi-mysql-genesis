from fastapi import FastAPI, status, Depends
from fastapi.responses import JSONResponse
import auth
from routes.product import product_route
from routes.user import user_route
from routes.warehouse import warehouse_route

app = FastAPI(
    title="GENESIS API",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    openapi_url='/json'
)

app.include_router(auth.router)
app.include_router(user_route)
app.include_router(product_route)
app.include_router(warehouse_route)

@app.get("/", status_code=status.HTTP_200_OK, tags=['Default'])
async def default():
    return JSONResponse(content={
            "state":True,
            "message": "Wellcome to Genesis API",
            }, status_code=200)

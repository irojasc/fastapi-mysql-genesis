import os
import uvicorn
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from routes.auth import auth_route
from routes.user import user_route
from routes.product import product_route
from routes.warehouse import warehouse_route
from routes.company import company_route

app = FastAPI(
    title="GENESIS API",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    openapi_url='/json'
)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_route)
app.include_router(user_route)
app.include_router(company_route)
app.include_router(product_route)
app.include_router(warehouse_route)

@app.get("/", status_code=status.HTTP_200_OK, tags=['Default'])
async def default():
    return JSONResponse(content={
            "state":True,
            "message": "Wellcome to Genesis API",
            }, status_code=200)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=os.getenv("PORT", default=5000), log_level="info")

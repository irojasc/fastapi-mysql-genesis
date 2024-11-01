from pydantic import BaseModel

# Define a Pydantic model
class product_maintenance(BaseModel):
    rqType: str 
    code: str = ''
    isbn: str = ''
    title: str = '' 
    autor: str = '' 
    publisher: str = '' 
    pvp: str = ''
    pv: str = ''
    asker: str 
    warehouse: str
    date: str
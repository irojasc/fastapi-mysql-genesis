from pydantic import BaseModel
class Token(BaseModel):
    userId: int
    userName: str
    hashed: str
    access_token: str
    token_type: str


    # class CreateUserRequest (BaseModel):
#     username: str
#     password: str
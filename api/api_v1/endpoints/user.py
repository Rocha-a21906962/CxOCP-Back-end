from azure.cosmos import CosmosClient
from fastapi import APIRouter, HTTPException
from models.user_model import User
from schemas.user_schema import UserAuth, UserOut
from services.user_service import UserService
import os

user_router = APIRouter()


@user_router.post("/create", summary="Create new user", response_model=UserOut)
async def create_user(data: UserAuth):
    client = CosmosClient(os.environ.get("COSMOS_DB_URI"), os.environ.get("COSMOS_DB_KEY"))
    database = client.get_database_client(os.environ.get("COSMOS_DB"))
    container = database.get_container_client(os.environ.get("COSMOS_DB_CONTAINER"))

    # Check if the user with the given email already exists
    existing_user_email = await UserService.get_user_by_email(data.email, container)
    if existing_user_email:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    # Check if the user with the given username already exists
    existing_user_username = await UserService.get_user_by_username(data.username, container)
    if existing_user_username:
        raise HTTPException(status_code=400, detail="User with this username already exists")

    # If the user doesn't exist, proceed to create the new user
    # data_to_add = {
    #     "id": "fed5e641-ac0e-42dc-9d1f-2fb5da0922c7",
    #     "username": "KnowULike",
    #     "email": "workbrigade@gmail.com",
    #     "hashed_password": "$2b$12$Mgf91aK1vF1eIgIFGYhm2OddygT4UO8VbCdYuAZZHxV9jxSJ.st.a",
    #     "first_name": None,
    #     "last_name": None,
    #     "disabled": None,
    # }

    # container.create_item(data_to_add)
    print(f"'Users' collection loaded with ${data} \n")
    return await UserService.create_user(data, container)
    # return {"message": "User created successfully"}

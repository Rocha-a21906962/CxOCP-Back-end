from azure.cosmos import CosmosClient
from fastapi import APIRouter, HTTPException
from models2.user_model import User
from schemas.user_schema import UserAuth
from services.user_service import UserService
import os

user_router = APIRouter()

@user_router.post("/create", summary="Create new user")
async def create_user(data: UserAuth):

    client = CosmosClient(os.environ.get("COSMOS_DB_URI"), os.environ.get("COSMOS_DB_KEY"))
    database = client.get_database_client(os.environ.get("COSMOS_DB_NAME"))
    container = database.get_container_client(os.environ.get("COSMOS_DB_CONTAINER"))

    # Check if the user with the given email already exists
    existing_user_email = await User.by_email(data.email, container)
    if existing_user_email:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    # Check if the user with the given username already exists
    # existing_user_username = await UserService.get_user_by_username(data.username)
    # if existing_user_username:
    #     raise HTTPException(status_code=400, detail="User with this username already exists")

    # If the user doesn't exist, proceed to create the new user
    print(data)
    # Add data to the container
    data_to_add = {
        "user_id": "fed5e641-ac0e-42dc-9d1f-2fb5da0922c7",
        "partition_key": "User",
        "username": "KnowULike",
        "email": "workbrigade@gmail.com",
        "hashed_password": "$2b$12$Mgf91aK1vF1eIgIFGYhm2OddygT4UO8VbCdYuAZZHxV9jxSJ.st.a",
        "first_name": None,
        "last_name": None,
        "disabled": None,
    }

    response = container.upsert_item(body=data_to_add)
    print(f"Added data to 'users' collection. Operation consumed {response['request_charge']} RUs.")
    # await UserService.create_user(data, container)
    return {"message": "User created successfully"}
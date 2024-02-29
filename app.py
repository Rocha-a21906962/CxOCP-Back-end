from env import OPENAI_ORG_ID, OPENAI_API_KEY
from models import Process, ChatRequest, ChatResponse
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
from openai import OpenAI
from typing import List

from database import (
    retrieve_data
)

from core.config import Settings
from azure.cosmos import CosmosClient, exceptions, PartitionKey
from api.api_v1.router import router

settings = Settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

origins = ["http://localhost:3000"]  # FE PORT

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods="*",
    allow_headers="*"
)

client = OpenAI(
    organization=OPENAI_ORG_ID,
    api_key=OPENAI_API_KEY
)

global cosmos_client
global cosmos_database
global users_container

@app.on_event("startup")
async def app_init():
    """
    Initialize crucial application services
    """

    try:
        cosmos_client = CosmosClient(url=settings.COSMOS_DB_URI, credential=settings.COSMOS_DB_KEY)
        print("Initialized Cosmos DB client.")
    except exceptions.CosmosResourceNotFoundError:
        print("Cosmos DB resource not found. Check your URI and key.")
    except Exception as e:
        print(f"Error initializing Cosmos DB client: {str(e)}")

    try:
        databases = list(cosmos_client.list_databases())
        if settings.COSMOS_DB_NAME not in [db['id'] for db in databases]:
            raise exceptions.ResourceNotFoundError(f"Database '{settings.COSMOS_DB_NAME}' not found.")

        cosmos_database = cosmos_client.get_database_client(settings.COSMOS_DB_NAME)
        print(f"Accessed database '{settings.COSMOS_DB_NAME}'.")
    except exceptions.ResourceNotFoundError:
        try:
            cosmos_database = cosmos_client.create_database(settings.COSMOS_DB_NAME)
            print(f"Created database '{settings.COSMOS_DB_NAME}'.")
        except exceptions.ResourceExistsError:
            print(f"Database '{settings.COSMOS_DB_NAME}' already exists.")
        except Exception as e:
            print(f"Error creating Cosmos DB database: {str(e)}")
            return
    except Exception as e:
        print(f"Error accessing Cosmos DB database: {str(e)}")
        return

    try:
        containers = list(cosmos_database.list_containers())

        if settings.COSMOS_DB_CONTAINER not in [container['id'] for container in containers]:
            raise exceptions.ResourceNotFoundError(
                f"Container '{settings.COSMOS_DB_CONTAINER}' not found in database '{settings.PROJECT_NAME}'.")

        users_container = cosmos_database.get_container_client(settings.COSMOS_DB_CONTAINER)
        print("Accessed 'users' collection.")
    except exceptions.ResourceNotFoundError:
        try:
            users_container = cosmos_database.create_container(id='users', partition_key=PartitionKey(path='/partition_key'))
            print("Created 'users' collection.")
        except exceptions.ResourceExistsError:
            print("Collection 'users' already exists.")
        except Exception as e:
            print(f"Error creating 'users' collection: {str(e)}")
    except Exception as e:
        print(f"Error accessing 'users' collection: {str(e)}")

app.include_router(router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)

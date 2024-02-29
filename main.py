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

from config import Settings
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
        if settings.PROJECT_NAME not in [db['id'] for db in databases]:
            raise exceptions.ResourceNotFoundError(f"Database '{settings.PROJECT_NAME}' not found.")

        cosmos_database = cosmos_client.get_database_client(settings.PROJECT_NAME)
        print(f"Accessed database '{settings.PROJECT_NAME}'.")
    except exceptions.ResourceNotFoundError:
        try:
            cosmos_database = cosmos_client.create_database(settings.PROJECT_NAME)
            print(f"Created database '{settings.PROJECT_NAME}'.")
        except exceptions.ResourceExistsError:
            print(f"Database '{settings.PROJECT_NAME}' already exists.")
        except Exception as e:
            print(f"Error creating Cosmos DB database: {str(e)}")
            return
    except Exception as e:
        print(f"Error accessing Cosmos DB database: {str(e)}")
        return

    try:
        containers = list(cosmos_database.list_containers())

        container_name_to_check = 'users'
        if container_name_to_check not in [container['id'] for container in containers]:
            raise exceptions.ResourceNotFoundError(
                f"Container '{container_name_to_check}' not found in database '{settings.PROJECT_NAME}'.")

        users_container = cosmos_database.get_container_client('users')
        print("Accessed 'users' collection.")
    except exceptions.ResourceNotFoundError:
        try:
            users_container = cosmos_database.create_container(id='users', partition_key=PartitionKey(path='/user_id', kind='Hash'))
            print("Created 'users' collection.")
        except exceptions.ResourceExistsError:
            print("Collection 'users' already exists.")
        except Exception as e:
            print(f"Error creating 'users' collection: {str(e)}")
    except Exception as e:
        print(f"Error accessing 'users' collection: {str(e)}")

app.include_router(router, prefix=settings.API_V1_STR)

@app.get('/')
def hello():
    return {"message": "Hello from Azure Container App!"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a Business Man. And you help with data mining."},
                {"role": "user", "content": request.message},
            ],
            temperature=0
        )

        response_message = response.choices[0].message.content

        print("OpenAI Response:", response_message)  # Print the entire response for debugging

        return ChatResponse(role="assistant", content=response_message)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/processes/", response_model=List[Process])
async def get_processes():
    # Use the retrieve_data function to retrieve data from the mock database
    processes = retrieve_data()
    return processes



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)

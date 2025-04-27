import os
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File
from azure.cosmos import CosmosClient
from api.dependencies.user_dependencies import get_current_user
from models.process_model import Process
from models.user_model import User
from schemas.process_schema import ProcessCreate, ProcessOut, ProcessUpdate
from services.process_service import ProcessService
from azure.storage.blob import BlobServiceClient
from fastapi import APIRouter, File, UploadFile, Depends
from core.config import Settings

settings = Settings()

CONNECTION_STRING = settings.AZURE_STORAGE_CONNECTION_STRING
CONTAINER_NAME = settings.AZURE_STORAGE_CONTAINER_NAME

process_router = APIRouter()

client = CosmosClient(os.environ.get("COSMOS_DB_URI"), os.environ.get("COSMOS_DB_KEY"))
database = client.get_database_client(os.environ.get("COSMOS_DB"))
processes_container = database.get_container_client(os.environ.get("COSMOS_DB_CONTAINER2"))

@process_router.get("/", summary="Get all processes of the user", response_model=List[ProcessOut])
async def get_processes(current_user: User = Depends(get_current_user)):
    return await ProcessService.list_processes(processes_container, current_user)

@process_router.post("/create", summary="Create a new process")
async def create_process(data: ProcessCreate, current_user: User = Depends(get_current_user)):
    print(f"'Processes' collection loaded with ${data} \n")
    return await ProcessService.create_process(processes_container, current_user, data)

@process_router.get("/{id}", summary="Get a process by id", response_model=ProcessOut)
async def retrieve(id: UUID, current_user: User = Depends(get_current_user)):
    return await ProcessService.retrieve_process(processes_container, current_user, id)

@process_router.put("/{id}", summary="Update a process by id", response_model=ProcessOut)
async def update(id: UUID, data: ProcessUpdate, current_user: User = Depends(get_current_user)):
    return await ProcessService.update_process(processes_container, current_user, id, data)

@process_router.delete("/{id}", summary="Delete a process by id")
async def delete(id: UUID, current_user: User = Depends(get_current_user)):
    await ProcessService.delete_process(processes_container, current_user, id)
    return None

blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

@process_router.post("/upload", summary="Upload a file and create a process")
async def upload_file(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):

    try:
        
        MAX_FILE_SIZE = 1 * 1024 * 1024 * 1024  # 1 GB limit
        print(f"File: {file.filename}, Size: {file.size} bytes")
        content = await file.read()

        file_size = len(content)
        print(f"File Size: {file_size} bytes")
        if file_size > MAX_FILE_SIZE:
            return {"message": "File is too large. Maximum allowed size is 1GB."}

        file.file.seek(0)

        if not file.filename.endswith(".csv"):
            return {"message": "Invalid file type. Only .csv files are allowed."}

        new_filename = "process.csv"

        title = file.filename

        content_text = content.decode('utf-8')

        process_data = ProcessCreate(title=title, content=content_text)

        process = await create_process(process_data, current_user)

        blob_client = container_client.get_blob_client(new_filename)

        blob_client.upload_blob(content, overwrite=True)  # Set overwrite=True to replace the blob if it already exists

        blob_url = blob_client.url
        print("message: File uploaded successfully")
        print(f"file_url: {blob_url}")
        return {"message": "File uploaded successfully", "process": process, "file_url": blob_url}
    
    except Exception as e:
        return {"message": "File upload failed", "error": str(e)}

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
from services.neo4j_service import Neo4jService
from azure.storage.blob import BlobServiceClient
from core.config import Settings
from datetime import datetime

settings = Settings()

CONNECTION_STRING = settings.AZURE_STORAGE_CONNECTION_STRING
CONTAINER_NAME = settings.AZURE_STORAGE_CONTAINER_NAME

process_router = APIRouter()

client = CosmosClient(os.environ.get("COSMOS_DB_URI"), os.environ.get("COSMOS_DB_KEY"))
database = client.get_database_client(os.environ.get("COSMOS_DB"))
processes_container = database.get_container_client(os.environ.get("COSMOS_DB_CONTAINER2"))

neo4j_service = Neo4jService()

@process_router.get("/", summary="Get all processes of the user", response_model=List[ProcessOut])
async def get_processes(current_user: User = Depends(get_current_user)):
    return await ProcessService.list_processes(processes_container, current_user)

@process_router.post("/create", summary="Create a new process")
async def create_process(data: ProcessCreate, current_user: User = Depends(get_current_user)):
    print(f"'Processes' collection loaded with ${data} \n")
    process = await ProcessService.create_process(processes_container, current_user, data)
    # Neo4j ingestion now handled in ProcessService.create_process or can be added here
    return process

@process_router.get("/{id}", summary="Get a process by id", response_model=ProcessOut)
async def retrieve(id: UUID, current_user: User = Depends(get_current_user)):
    return await ProcessService.retrieve_process(processes_container, current_user, id)

@process_router.put("/{id}", summary="Update a process by id", response_model=ProcessOut)
async def update(id: UUID, data: ProcessUpdate, current_user: User = Depends(get_current_user)):
    # Get the process document first
    query = f"SELECT * FROM c WHERE c.owner.id = '{current_user.id}' AND c.id = '{id}'"
    items = list(processes_container.query_items(query=query, enable_cross_partition_query=True))
    if not items:
        return {"message": "Process not found"}
    process = items[0]

    # Delete process and steps in Neo4j before update (old data)
    try:
        neo4j_service.delete_process(str(process['id']))
    except Exception as neo4j_error:
        print(f"Neo4j deletion failed on update: {neo4j_error}")

    # Update in Cosmos DB
    updated_process = await ProcessService.update_process(processes_container, current_user, id, data)

    # Ingest new data into Neo4j after update (new data)
    try:
        # Use the updated content and title if available
        content = data.content if data.content is not None else process.get('content', '')
        title = data.title if data.title is not None else process.get('title', '')
        neo4j_service.ingest_csv(content, str(process['id']), title)
    except Exception as neo4j_error:
        print("Neo4j ingestion failed on update:", neo4j_error)

    return updated_process

@process_router.delete("/{id}", summary="Delete a process by id")
async def delete(id: UUID, current_user: User = Depends(get_current_user)):
    # Get the process document
    query = f"SELECT * FROM c WHERE c.owner.id = '{current_user.id}' AND c.id = '{id}'"
    items = list(processes_container.query_items(query=query, enable_cross_partition_query=True))
    if not items:
        return {"message": "Process not found"}
    process = items[0]
    blob_filename = process.get("title")  # The filename used as the blob name

    # Delete from Cosmos DB
    await ProcessService.delete_process(processes_container, current_user, id)

    # Delete from Neo4j (process and steps together)
    try:
        neo4j_service.delete_process(str(process['id']))
    except Exception as neo4j_error:
        print(f"Neo4j deletion failed: {neo4j_error}")

    # Delete from Azure Blob Storage
    try:
        blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)
        blob_client = container_client.get_blob_client(blob_filename)
        blob_client.delete_blob()
    except Exception as e:
        # You may want to log this, but don't fail the request just for a missing blob
        print(f"Warning: Failed to delete blob '{blob_filename}': {e}")

    return {"message": "Process and associated file deleted."}

blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

@process_router.post("/upload", summary="Upload a file and create a process")
async def upload_file(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    try:
        MAX_FILE_SIZE = 1 * 1024 * 1024 * 1024  # 1 GB limit
        print(f"File: {file.filename}")
        content = await file.read()

        file_size = len(content)
        print(f"File Size: {file_size} bytes")
        if file_size > MAX_FILE_SIZE:
            return {"message": "File is too large. Maximum allowed size is 1GB."}

        file.file.seek(0)

        if not file.filename.endswith(".csv"):
            return {"message": "Invalid file type. Only .csv files are allowed."}

        new_filename = file.filename
        title = file.filename
        content_text = content.decode('utf-8')

        # Check if a process with this title already exists
        query = f"SELECT * FROM c WHERE c.owner.id = '{current_user.id}' AND c.title = '{title}'"
        items = list(processes_container.query_items(query=query, enable_cross_partition_query=True))
        if items:
            process_id = items[0]['id']

            # Delete old process and steps from Neo4j
            try:
                neo4j_service.delete_process(str(process_id))
            except Exception as neo4j_error:
                print(f"Neo4j deletion failed in upload: {neo4j_error}")

            updated_process = {
                **items[0],
                'content': content_text,
                'updated_at': datetime.now().isoformat(),
            }
            processes_container.upsert_item(body=updated_process)
            process = updated_process

            # Ingest new data into Neo4j
            try:
                neo4j_service.ingest_csv(content_text, process_id, title)
            except Exception as neo4j_error:
                print("Neo4j ingestion failed in upload:", neo4j_error)
        else:
            # Create new process in Cosmos DB
            process_data = ProcessCreate(title=title, content=content_text)
            process = await ProcessService.create_process(processes_container, current_user, process_data)
            # Insert into Neo4j for new process if not handled inside create_process
            try:
                neo4j_service.ingest_csv(content_text, process['id'], title)
            except Exception as neo4j_error:
                print("Neo4j ingestion failed in upload:", neo4j_error)

        blob_client = container_client.get_blob_client(new_filename)
        blob_client.upload_blob(content, overwrite=True)  # Set overwrite=True to replace the blob if it already exists

        blob_url = blob_client.url
        print("message: File uploaded successfully")
        print(f"file_url: {blob_url}")
        return {"message": "File uploaded successfully", "process": process, "file_url": blob_url}

    except Exception as e:
        return {"message": "File upload failed", "error": str(e)}
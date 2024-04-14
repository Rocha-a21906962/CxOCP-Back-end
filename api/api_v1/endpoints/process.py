import os
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends
from azure.cosmos import CosmosClient
from api.dependencies.user_dependencies import get_current_user
from models.process_model import Process
from models.user_model import User
from schemas.process_schema import ProcessCreate, ProcessOut, ProcessUpdate
from services.process_service import ProcessService

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



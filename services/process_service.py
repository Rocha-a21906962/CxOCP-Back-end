from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from models.process_model import Process
from models.user_model import User
from schemas.process_schema import ProcessCreate, ProcessUpdate

# import logging
# logging.basicConfig(level=logging.INFO)

class ProcessService:
    
    @staticmethod
    async def list_processes(container, user: User) -> List[Dict[str, Any]]:
        query = f"SELECT * FROM c WHERE c.owner.id = '{user.id}'"
        result = container.query_items(query=query, enable_cross_partition_query=True)
    
        processes = [
            {
                'id': item['id'],
                'status': item['status'],
                'title': item['title'],
                'content': item['content'],
                'created_at': item['created_at'],
                'updated_at': item['updated_at'],
                'owner': item['owner']
            }
            for item in result
        ]

        return processes
        
    @staticmethod
    async def create_process(container, user: User, data: ProcessCreate) -> Process:
        process = Process(**data.dict(), owner=user)
        await process.save(container, process.to_dict())
        return process.to_dict()
    
    @staticmethod
    async def retrieve_process(container, current_user: User, id: UUID) -> Optional[Dict[str, Any]]:
        query = f"SELECT * FROM c WHERE c.owner.id = '{current_user.id}' AND c.id = '{id}'"
        items = container.query_items(query=query, enable_cross_partition_query=True)
        
        for item in items:
            return {
                'id': item['id'],
                'status': item['status'],
                'title': item['title'],
                'content': item['content'],
                'created_at': item['created_at'],
                'updated_at': item['updated_at'],
                'owner': item['owner']
            }
        
        return None
    
    @staticmethod
    async def update_process(container, current_user: User, id: UUID, data: ProcessUpdate) -> Optional[Dict[str, Any]]:
        query = f"SELECT * FROM c WHERE c.owner.id = '{current_user.id}' AND c.id = '{id}'"
        items = container.query_items(query=query, enable_cross_partition_query=True)
        
        for item in items:
            updated_process = {
                'id': item['id'],
                'status': data.status if data.status is not None else item['status'],
                'title': data.title if data.title is not None else item['title'],
                'content': data.content if data.content is not None else item['content'],
                'created_at': item['created_at'],
                'updated_at': datetime.now().isoformat(),
                'owner': item['owner']
            }
            container.upsert_item(body=updated_process)
            return updated_process
        
        return None
    
    @staticmethod
    async def delete_process(container, current_user: User, id: UUID):
        query = f"SELECT * FROM c WHERE c.owner.id = '{current_user.id}' AND c.id = '{id}'"
        items = container.query_items(query=query, enable_cross_partition_query=True)
        
        found = False
        
        for item in items:
            # logging.info(f"Deleting item {item} \n")
            container.delete_item(item=item['id'], partition_key=item["id"])
            found = True
        
        if not found:
            print(f"Item with ID {id} not found for user {current_user.id}")
#interations between the application and the database

from cProfile import label
from pydoc import doc
from turtle import title
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ReturnDocument

from pydantic import BaseModel

from uuid import uuid4

from requests import session

class ListSummary(BaseModel):
    id: str
    title: str
    item_count: int

    @staticmethod
    def from_doc(doc) -> "ListSummary":
        return ListSummary(
            id=str(doc["_id"]),
            title=doc["title"],
            item_count=doc["item_count"],
        )
        
class ToDoListItem(BaseModel):
    id: str
    description: str
    completed: bool

    @staticmethod
    def from_doc(item) -> "ToDoListItem":
        return ToDoListItem(
            id=str(item["_id"]),
            label=item["label"],
            checked=item["checked"],
        )
        
class ToDoList(BaseModel):
    id: str
    title: str
    items: list[ToDoListItem]

    @staticmethod
    def from_doc(doc) -> "ToDoList":
        return ToDoList(
            id=str(doc["_id"]),
            title=doc["title"],
            items=[ToDoListItem.from_doc(item) for item in doc["items"]],
        )
class ToDoDAL:
    def __init__(self, todo_collection: AsyncIOMotorCollection):
        self._todo_collection = todo_collection

    async def list_todo_lists(self, session=None):
        async for doc in self._todo_collection.find(
            {}, 
            projection={
                "name": 1, 
                "item_count": {"$size": "$items"}
            },
            sort={"name": 1},
            session=session
        ):
            yield ListSummary.from_doc(doc)

    async def create_todo_list(self, name: str, session=None) -> str:
        response = await self._todo_collection.insert_one(
            {
                "title": name,
                "items": [],
            },
            session=session
        )
        return str(response.inserted_id)
    
    async def get_todo_list(self,id: str | ObjectId, session=None) -> ToDoList | None:
        doc = await self._todo_collection.find_one(
            {"_id": ObjectId(id)},
            session=session
        )
        return ToDoList.from_doc(doc)
    
    async def delete_todo_list(self, id: str | ObjectId, session=None) -> bool:
        response = await self._todo_collection.delete_one(
            {"_id": ObjectId(id)},
            session=session
        )
        return response.deleted_count == 1
    
    async def createItem(
            self,
            id: str | ObjectId,
            label: str, 
            session=None, ) -> ToDoList | None:
                
        result = await self._todo_collection.find_one_and_update(
            {"_id": ObjectId(id)},
            {
                "$push": {
                    "items": {
                        "id": uuid4().hex,
                        "label": label,
                        "checked": False,
                    }
                }
            },
            session=session,
            return_document=ReturnDocument.AFTER,
        )
        if result:
            return ToDoList.from_doc(result)
        


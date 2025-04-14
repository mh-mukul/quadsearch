from pydantic import BaseModel, Field


class CollectionCreatePayload(BaseModel):
    collection_name: str = Field(..., description="Name of the collection")


class SearchPayload(BaseModel):
    collection_name: str = Field(..., description="Name of the collection")
    query: str = Field(..., description="Query string to search for")
    limit: int = Field(..., description="Number of results to return", ge=1)

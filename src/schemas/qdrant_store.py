from typing import List
from pydantic import BaseModel, Field


class CollectionCreatePayload(BaseModel):
    collection_name: str = Field(..., description="Name of the collection")


class SearchPayload(BaseModel):
    collection_name: str = Field(..., description="Name of the collection")
    query: str = Field(..., description="Query string to search for")
    limit: int = Field(10, description="Number of results to return", ge=1)
    rerank: bool = Field(
        False, description="Whether to rerank results with a cross-encoder")
    min_score: float = Field(
        0.0, description="Minimum score threshold for results", ge=0.0, le=1.0)
    metadata_filter: dict = Field(
        None, description="Optional metadata filter to apply")


class ResultsSchema(BaseModel):
    pageContent: str = Field(..., description="Content of the document")
    metadata: dict = Field(..., description="Metadata of the document")
    id: str = Field(..., description="ID of the document")
    relevance_score: float = Field(...,
                                   description="Relevance score of the document")


class RerankRequestPayload(BaseModel):
    query: str = Field(..., description="Query string to rerank against")
    results: List[ResultsSchema]
    limit: int = Field(10, description="Number of results to return", ge=1)

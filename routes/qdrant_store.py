import os
from uuid import uuid4
from fastapi import APIRouter, Request, UploadFile, File, Form, Depends

from configs.logger import logger
from utils.auth import get_api_key
from utils.helper import ResponseHelper
from utils.qdrant_store import QdrantStore
from utils.extract_doc import prepare_documents_from_csv_stream
from schemas.qdrant_store import CollectionCreatePayload, SearchPayload

DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

qdrant = QdrantStore()
response = ResponseHelper()
router = APIRouter(prefix="/qdrant", tags=["Qdrant Store"])


@router.post("/create_collection")
def collection_create(
    request: Request,
    data: CollectionCreatePayload,
    _: None = Depends(get_api_key),
):
    try:
        qdrant.create_collection(collection_name=data.collection_name)
        return response.success_response(201, "Collection created.")
    except Exception as e:
        logger.error(f"Failed to create collection: {e}")
        return response.error_response(500, "Failed to create collection.", str(e))


@router.post("/add_document")
def document_add(
    request: Request,
    collection_name: str = Form(..., description="Name of the collection"),
    vector_columns: str = Form(...,
                               description="Comma-separated list of columns"),
    file: UploadFile = File(..., description="CSV file containing documents"),
    _: None = Depends(get_api_key),
):
    if file.content_type not in ["text/csv"]:
        return response.error_response(400, "Invalid file type. Only CSV files are allowed.")

    vector_columns = [col.strip() for col in vector_columns.split(",")]

    filename = uuid4().hex + ".csv"
    file_path = f"{DATA_DIR}/{filename}"
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    try:
        # Stream batches and upload to Qdrant
        for batch in prepare_documents_from_csv_stream(file_path):
            qdrant.add_documents(
                collection_name=collection_name,
                documents=batch,
                vector_columns=vector_columns
            )
        # Clean up the file after processing
        os.remove(file_path)
        return response.success_response(200, "Documents added successfully.")
    except Exception as e:
        os.remove(file_path)
        logger.error(f"Failed to add documents: {e}")
        return response.error_response(500, "Failed to add documents.", str(e))


@router.post("/search")
def document_search(
    request: Request,
    payload: SearchPayload,
    _: None = Depends(get_api_key),
):
    query = payload.query.strip()
    if not query:
        return response.error_response(400, "Query cannot be empty.")

    try:
        results = qdrant.search_documents(
            payload.collection_name, query, limit=payload.limit)
        if not results:
            return response.error_response(404, "No results found.")
        results = [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload,
            }
            for hit in results
        ]
        return response.success_response(200, "Success", results)
    except Exception as e:
        logger.error(f"Failed to search documents: {e}")
        return response.error_response(500, "Failed to search documents.", str(e))

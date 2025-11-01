import os
from uuid import uuid4
from fastapi import APIRouter, Request, UploadFile, File, Form, Depends

from src.configs.logger import logger
from src.utils.auth import get_api_key
from src.utils.helper import ResponseHelper
from src.utils.qdrant_store import QdrantStore, rerank_results
from src.utils.extract_doc import prepare_documents_from_csv_stream
from src.schemas.qdrant_store import CollectionCreatePayload, SearchPayload, RerankRequestPayload

from src.utils.doc_processor import process_document

DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

qdrant = QdrantStore()
response = ResponseHelper()
router = APIRouter(prefix="", tags=["Qdrant Store"])


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
    file: UploadFile = File(..., description="CSV file containing documents"),
    vector_columns: str = Form(...,
                               description="Comma-separated list of columns"),
    skip_empty: bool = Form(
        False, description="If True, skip rows with empty values in the specified columns"),
    batch_size: int = Form(
        100, description="Number of documents to yield per batch"),
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
        for batch in prepare_documents_from_csv_stream(file_path=file_path, skip_empty=skip_empty, batch_size=batch_size):
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
            payload.collection_name, query, limit=payload.limit, rerank=payload.rerank, min_score=payload.min_score)
        if not results:
            return response.success_response(200, "No results found.")
        return response.success_response(200, "Success", results)
    except Exception as e:
        logger.error(f"Failed to search documents: {e}")
        return response.error_response(500, "Failed to search documents.", str(e))


@router.post("/rerank")
def document_rerank(
    request: Request,
    payload: RerankRequestPayload,
    _: None = Depends(get_api_key),
):
    query = payload.query.strip()
    if not query:
        return response.error_response(400, "Query cannot be empty.")
    if not payload.results:
        return response.error_response(400, "Results cannot be empty.")

    try:
        results = rerank_results(payload.results, query)
        results = results[:payload.limit]
        if not results:
            return response.success_response(200, "No results found.")
        return response.success_response(200, "Success", results)
    except Exception as e:
        logger.error(f"Failed to rerank documents: {e}")
        return response.error_response(500, "Failed to rerank documents.", str(e))


@router.post("/process_doc")
def process_doc(
    request: Request,
    file: UploadFile = File(..., description="Document file to process"),
    _: None = Depends(get_api_key),
):
    filename = uuid4().hex + "_" + file.filename
    file_path = f"{DATA_DIR}/{filename}"
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    try:
        doc_info = process_document(file_path)
        os.remove(file_path)
        if doc_info['status'] == 'Success':
            return response.success_response(200, "Document processed successfully.", doc_info)
        else:
            return response.error_response(500, "Document processing failed.", doc_info)
    except Exception as e:
        os.remove(file_path)
        logger.error(f"Failed to process document: {e}")
        return response.error_response(500, "Failed to process document.", str(e))

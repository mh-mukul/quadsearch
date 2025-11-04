import os
from uuid import uuid4
from pathlib import Path
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer, CrossEncoder
from fastapi import APIRouter, Request, UploadFile, Form, File, Depends

from src.configs.logger import logger
from src.utils.auth import get_api_key
from src.utils.helper import ResponseHelper
from src.utils.qdrant_store import QdrantStore
from src.schemas.qdrant_store import CollectionCreatePayload, SearchPayload, RerankRequestPayload

from src.tasks import process_and_store_document

load_dotenv()
DOCUMENT_DIR = os.getenv('DOCUMENT_DIR', 'documents')

QADRANT_URL = os.getenv("QDRANT_URL")
QADRANT_API_KEY = os.getenv("QDRANT_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
RERANKER_MODEL = os.getenv(
    "RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

qdrant = QdrantStore(
    client=QdrantClient(url=QADRANT_URL, api_key=QADRANT_API_KEY),
    encoder=SentenceTransformer(EMBEDDING_MODEL),
    reranker=CrossEncoder(RERANKER_MODEL)
)

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
        results = qdrant.rerank_results(payload.results, query)
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
    collection_name: str = Form(
        ..., description="Qdrant collection name to store document chunks."),
    file: UploadFile = File(..., description="Document file to process"),
    _: None = Depends(get_api_key),
):
    filename = uuid4().hex + "_" + file.filename
    file_path = f"{DOCUMENT_DIR}/uploads/{filename}"
    os.makedirs(Path(file_path).parent, exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    try:
        task = process_and_store_document.delay(
            file_path, collection_name)
        return response.success_response(
            202,
            "Document processing started.",
            {"task_id": task.id, "file": file.filename},
        )
    except Exception as e:
        logger.error(f"Failed to start document processing task: {e}")
        return response.error_response(500, "Failed to start document processing.", str(e))

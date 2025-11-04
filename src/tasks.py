import os
from dotenv import load_dotenv

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer, CrossEncoder

from transformers import AutoTokenizer
from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter

from celery_config import celery_app
from src.utils.qdrant_store import QdrantStore
from src.utils.doc_processor import DoclingProcessor

load_dotenv()

QADRANT_URL = os.getenv("QDRANT_URL")
QADRANT_API_KEY = os.getenv("QDRANT_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
RERANKER_MODEL = os.getenv(
    "RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
CHUNKER_MODEL = os.getenv(
    "CHUNKER_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHUNKER_MAX_TOKENS = int(os.getenv("CHUNKER_MAX_TOKENS", 512))
DOCUMENT_DIR = os.getenv('DOCUMENT_DIR', 'documents')

qdrant = QdrantStore(
    client=QdrantClient(url=QADRANT_URL, api_key=QADRANT_API_KEY),
    encoder=SentenceTransformer(EMBEDDING_MODEL),
    reranker=CrossEncoder(RERANKER_MODEL)
)

converter = DocumentConverter()
chunker = HybridChunker(
    tokenizer=AutoTokenizer.from_pretrained(CHUNKER_MODEL),
    max_tokens=CHUNKER_MAX_TOKENS,
    merge_peers=True  # Merge small adjacent chunks
)
doc_processor = DoclingProcessor(converter=converter, chunker=chunker)


@celery_app.task(name="process_and_store_document")
def process_and_store_document(file_path: str, collection_name: str):
    """
    Celery task to process a document and store its chunks in Qdrant.

    :param file_path: Path to the document file.
    :param collection_name: Name of the Qdrant collection to store chunks.
    """
    try:
        # Process document
        doc_info = doc_processor.process_document(file_path)
        if doc_info['status'] == 'Success':
            # Chunk document
            chunk_info = doc_processor.chunk_document(file_path=doc_info['output_file'], dl_doc=doc_info['docling_doc'])
            chunks = chunk_info['chunks']

            # Prepare documents for Qdrant
            documents = []
            for idx, chunk in enumerate(chunks):
                documents.append({
                    'content': chunk,
                    'metadata': {
                        'source_file': doc_info['file'],
                        'chunk_index': idx,
                    }
                })

            # Add documents to Qdrant
            qdrant.add_documents(collection_name, documents)
            return f"Document '{doc_info['file']}' processed and stored successfully."
        else:
            return f"Document processing failed: {doc_info}"
    except Exception as e:
        return f"Error in processing and storing document: {e}"

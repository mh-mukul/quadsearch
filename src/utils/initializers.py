import os
from dotenv import load_dotenv

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer, CrossEncoder

from transformers import AutoTokenizer
from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter

from src.utils.qdrant_store import QdrantStore
from src.utils.doc_processor import DoclingProcessor

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
ARTIFACTS_DIR = os.getenv("ARTIFACTS_DIR", "./data/artifacts")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
RERANKER_MODEL = os.getenv(
    "RERANKER_MODEL", "ms-marco-MiniLM-L-6-v2")
CHUNKER_MODEL = os.getenv(
    "CHUNKER_MODEL", "all-MiniLM-L6-v2")
CHUNKER_MAX_TOKENS = int(os.getenv("CHUNKER_MAX_TOKENS", 512))
DOCUMENT_DIR = os.getenv('DOCUMENT_DIR', 'documents')

qdrant = QdrantStore(
    client=QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY),
    encoder=SentenceTransformer(os.path.join(ARTIFACTS_DIR, EMBEDDING_MODEL)),
    reranker=CrossEncoder(os.path.join(ARTIFACTS_DIR, RERANKER_MODEL))
)

converter = DocumentConverter()
chunker = HybridChunker(
    tokenizer=AutoTokenizer.from_pretrained(
        os.path.join(ARTIFACTS_DIR, CHUNKER_MODEL)),
    max_tokens=CHUNKER_MAX_TOKENS,
    merge_peers=True  # Merge small adjacent chunks
)
doc_processor = DoclingProcessor(converter=converter, chunker=chunker)

import os
from uuid import uuid4
from typing import List
from dotenv import load_dotenv
from configs.logger import logger
from qdrant_client import models, QdrantClient
from schemas.qdrant_store import ResultsSchema
from sentence_transformers import SentenceTransformer, CrossEncoder

load_dotenv()

QADRANT_URL = os.getenv("QDRANT_URL")
QADRANT_API_KEY = os.getenv("QDRANT_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
RERANKER_MODEL = os.getenv(
    "RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

client = QdrantClient(
    url=QADRANT_URL,
    api_key=QADRANT_API_KEY,
)
encoder = SentenceTransformer(EMBEDDING_MODEL, trust_remote_code=True)
reranker = CrossEncoder(RERANKER_MODEL)


class QdrantStore:
    def create_collection(self, collection_name: str):
        """
        Create a Qdrant collection.

        :param collection_name: Name of the collection.
        """
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=768,   # Important: Ensure this matches the embedding model size that you use
                distance=models.Distance.COSINE,
            ),
        )

    def add_documents(self, collection_name: str, documents: list, vector_columns: list[str]):
        """
        Add documents to the Qdrant collection.

        :param collection_name: Name of the collection.
        :param documents: List of documents to add.
        :param vector_columns: List of column names to use for vectorization.
        """
        client.upload_points(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=uuid4().hex,
                    vector=encoder.encode(
                        " ".join(
                            f"{col}: {doc[col]}" for col in vector_columns if col in doc)
                    ).tolist(),
                    payload=doc
                )
                for doc in documents
            ]
        )

    def search_documents(self, collection_name: str, query: str, limit: int = 25, rerank: bool = False, min_score: float = 0.0):
        """
        Search and optionally rerank results.

        :param collection_name: Name of the collection.
        :param query: Query string to search for.
        :param limit: Number of results to return.
        :param rerank: Whether to rerank results with a cross-encoder.
        :return: List of (doc, score).
        """
        # Step 1: Retrieve candidates with vector search
        hits = client.query_points(
            collection_name=collection_name,
            query=encoder.encode(query).tolist(),
            limit=limit,
            score_threshold=min_score if min_score > 0.0 else None,
        )

        logger.info(f"Initial search results: {hits}")

        results = [
            ResultsSchema(
                pageContent=hit.payload.get("content"),
                metadata=hit.payload.get("metadata"),
                id=hit.id,
                relevance_score=float(hit.score)
            )
            for hit in hits.points
        ]

        # Step 2: Rerank
        if rerank and results:
            results = rerank_results(results, query)

        return results


def rerank_results(results: List[ResultsSchema], query: str):
    # Prepare pairs for cross-encoder
    pairs = [(query, item.pageContent) for item in results]
    # Get relevance scores
    relevance_score = reranker.predict(pairs)

    # Attach relevance score
    for item, score in zip(results, relevance_score):
        item.relevance_score = float(score)

    # Sort by relevance score (descending)
    results = sorted(results, key=lambda x: x.relevance_score, reverse=True)
    return results

import os
from uuid import uuid4
from dotenv import load_dotenv
from configs.logger import logger
from qdrant_client import models, QdrantClient
from sentence_transformers import SentenceTransformer, CrossEncoder

load_dotenv()

QADRANT_URL = os.getenv("QDRANT_URL")
QADRANT_API_KEY = os.getenv("QDRANT_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

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
            {"doc": hit.payload, "vector_score": hit.score}
            for hit in hits.points
        ]

        # Step 2: Rerank
        if rerank and results:
            pairs = [(query, r["doc"].get("text", str(r["doc"]))) for r in results]
            rerank_scores = reranker.predict(pairs)

            # Attach reranker score
            for r, s in zip(results, rerank_scores):
                r["rerank_score"] = float(s)

            # Sort by reranker score (descending)
            results = sorted(results, key=lambda x: x["rerank_score"], reverse=True)

        logger.info(f"Final search results: {results}")

        return results

from uuid import uuid4
from typing import List
from qdrant_client import models, QdrantClient
from sentence_transformers import SentenceTransformer, CrossEncoder

from src.configs.logger import logger
from src.schemas.qdrant_store import ResultsSchema


class QdrantStore:
    def __init__(self, client: QdrantClient, encoder: SentenceTransformer, reranker: CrossEncoder):
        self.client = client
        self.encoder = encoder
        self.reranker = reranker

        try:
            self.vector_size = self.encoder.get_sentence_embedding_dimension()
            logger.info(
                f"QdrantStore initialized with vector size: {self.vector_size}")
        except Exception as e:
            logger.error(
                f"Failed to get sentence embedding dimension from encoder: {e}")
            raise ValueError(f"Invalid SentenceTransformer model: {e}") from e

    def create_collection(self, collection_name: str):
        """
        Create a Qdrant collection.

        :param collection_name: Name of the collection.
        """
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=self.vector_size,
                distance=models.Distance.COSINE,
            ),
        )

    def add_documents(self, collection_name: str, documents: list):
        """
        Add documents to the Qdrant collection.

        :param collection_name: Name of the collection.
        :param documents: List of documents to add.
        """
        # 1. Prepare all texts in a batch
        texts_to_encode = [
            doc.get("content", "") for doc in documents
        ]

        # 2. Encode the entire batch in one call
        vectors = self.encoder.encode(texts_to_encode)

        # 3. Create points (this part is fast)
        points = [
            models.PointStruct(
                id=uuid4().hex, vector=vector.tolist(), payload=doc)
            for doc, vector in zip(documents, vectors)
        ]

        # 4. Upload all points in one batch
        self.client.upload_points(
            collection_name=collection_name,
            points=points,
        )

    def search_documents(self, collection_name: str, query: str, limit: int = 25, rerank: bool = False, min_score: float = 0.0):
        """
        Search and optionally rerank results.

        :param collection_name: Name of the collection.
        :param query: Query string to search for.
        :param limit: Number of results to return.
        :param rerank: Whether to rerank results with a cross-encoder.
        :param min_score: Minimum score for results to be included.
        :return: List of (doc, score).
        """
        # Step 1: Retrieve candidates with vector search
        hits = self.client.query_points(
            collection_name=collection_name,
            query=self.encoder.encode(query).tolist(),
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
            results = self.rerank_results(results, query)

        return results

    def rerank_results(self, results: List[ResultsSchema], query: str):
        """
        Rerank results using a cross-encoder.

        :param results: List of results to rerank.
        :param query: Query string.
        :return: Reranked list of results.
        """
        # Prepare pairs for cross-encoder
        pairs = [(query, item.pageContent) for item in results]
        # Get relevance scores
        relevance_score = self.reranker.predict(pairs)

        # Attach relevance score
        for item, score in zip(results, relevance_score):
            item.relevance_score = float(score)

        # Sort by relevance score (descending)
        results = sorted(
            results, key=lambda x: x.relevance_score, reverse=True)
        return results

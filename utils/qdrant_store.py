import os
from uuid import uuid4
from dotenv import load_dotenv
from qdrant_client import models, QdrantClient
from sentence_transformers import SentenceTransformer

load_dotenv()

QADRANT_URL = os.getenv("QDRANT_URL")
QADRANT_API_KEY = os.getenv("QDRANT_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

client = QdrantClient(
    url=QADRANT_URL,
    api_key=QADRANT_API_KEY,
)
encoder = SentenceTransformer(EMBEDDING_MODEL)


class QdrantStore:
    def create_collection(self, collection_name: str):
        """
        Create a Qdrant collection.

        :param collection_name: Name of the collection.
        """
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=384,   # Important: Ensure this matches the embedding model size that you use
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

    def search_documents(self, collection_name: str, query: str, limit: int = 5):
        """
        Search for documents in the Qdrant collection.

        :param collection_name: Name of the collection.
        :param query: Query string to search for.
        :param limit: Number of results to return.
        :return: List of search results.
        """
        hits = client.query_points(
            collection_name=collection_name,
            query=encoder.encode(query).tolist(),
            limit=limit,
        )
        return hits

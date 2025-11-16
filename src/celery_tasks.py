from datetime import datetime, timezone

from src.models.tasks import Tasks
from celery_config import celery_app
from src.configs.logger import logger
from src.configs.database import SessionLocal
from src.utils.initializers import qdrant, doc_processor


@celery_app.task(name="process_and_store_document", bind=True)
def process_and_store_document(self, file_path: str, collection_name: str, metadata: dict = None):
    """
    Celery task to process a document and store its chunks in Qdrant.

    :param self: Task instance (automatically injected by Celery)
    :param file_path: Path to the document file.
    :param collection_name: Name of the Qdrant collection to store chunks.
    :param metadata: Optional metadata for the document.
    """
    db = SessionLocal()
    try:
        # Create task record
        task = Tasks(task_id=self.request.id, status="PROCESSING")
        db.add(task)
        db.commit()

        # Process document
        doc_info = doc_processor.process_document(file_path)
        if doc_info['status'] == 'Success':
            # Chunk document
            chunk_info = doc_processor.chunk_document(
                file_path=doc_info['output_file'], dl_doc=doc_info['docling_doc'])
            chunks = chunk_info['chunks']

            # Prepare documents for Qdrant
            documents = []
            for idx, chunk in enumerate(chunks):
                documents.append({
                    'content': chunk,
                    'metadata': {
                        'source_file': doc_info['file'],
                        **(metadata or {})
                    }
                })

            # Add documents to Qdrant
            qdrant.add_documents(collection_name, documents)

            # Update task status
            task.status = "COMPLETED"
            task.completed_at = datetime.now(tz=timezone.utc)
            db.commit()

            return f"Document '{doc_info['file']}' processed and stored successfully."
        else:
            # Update task status for processing failure
            task.status = "FAILED"
            task.completed_at = datetime.now(tz=timezone.utc)
            db.commit()
            return f"Document processing failed: {doc_info}"
    except Exception as e:
        logger.error(f"Error in processing and storing document: {e}")
        # Update task status for error
        task.status = "FAILED"
        task.completed_at = datetime.now(tz=timezone.utc)
        db.commit()
        return f"Error in processing and storing document: {e}"
    finally:
        db.close()


@celery_app.task(name="process_and_store_content", bind=True)
def process_and_store_content(self, content: str, collection_name: str, metadata: dict = None):
    """
    Celery task to process text content and store its chunks in Qdrant.

    :param self: Task instance (automatically injected by Celery)
    :param content: Text content to process.
    :param collection_name: Name of the Qdrant collection to store chunks.
    :param metadata: Optional metadata for the content.
    """
    db = SessionLocal()
    try:
        # Create task record
        task = Tasks(task_id=self.request.id, status="PROCESSING")
        db.add(task)
        db.commit()

        # Prepare documents for Qdrant
        documents = [{
            'content': content,
            'metadata': {
                **(metadata or {})
            }
        }]

        # Add documents to Qdrant
        qdrant.add_documents(collection_name, documents)

        # Update task status
        task.status = "COMPLETED"
        task.completed_at = datetime.now(tz=timezone.utc)
        db.commit()

        return "Content processed and stored successfully."
    except Exception as e:
        logger.error(f"Error in processing and storing content: {e}")
        # Update task status for error
        task.status = "FAILED"
        task.completed_at = datetime.now(tz=timezone.utc)
        db.commit()
        return f"Error in processing and storing content: {e}"
    finally:
        db.close()

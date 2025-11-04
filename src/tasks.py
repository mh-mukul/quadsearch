from celery_config import celery_app
from src.configs.logger import logger
from src.utils.initializers import qdrant, doc_processor



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
        logger.error(f"Error in processing and storing document: {e}")
        return f"Error in processing and storing document: {e}"

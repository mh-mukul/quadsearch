import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter

from src.configs.logger import logger


load_dotenv()

DOCUMENT_DIR = os.getenv('DOCUMENT_DIR', 'documents')


class DoclingProcessor:
    def __init__(self, converter: DocumentConverter, chunker: HybridChunker):
        self.converter = converter
        self.chunker = chunker

        logger.info(
            f"DoclingProcessor initialized with chunker size: {chunker.max_tokens}")

    def process_document(self, file_path: str) -> dict:
        """Process a single document and return metadata.

        :param file_path: Path to the document file.
        :return: Metadata dictionary about the processing result.
        """
        try:
            logger.info(f"📄 Processing: {Path(file_path).name}")

            # Convert document
            result = self.converter.convert(file_path)
            dl_doc = result.document

            # Convert to markdown
            logger.info(f"   Step: Converting document to markdown...")
            markdown = dl_doc.export_to_markdown()
            # Save output
            output_file = f"{DOCUMENT_DIR}/processed/{Path(file_path).stem}.md"
            os.makedirs(Path(output_file).parent, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown)

            # Get document info
            doc_info = {
                'file': Path(file_path).name,
                'format': Path(file_path).suffix,
                'docling_doc': dl_doc,
                'status': 'Success'
            }

            doc_info['output_file'] = output_file

            logger.info(f"   ✓ Converted successfully")
            logger.info(f"   ✓ Output: {output_file}")

            return doc_info
        except Exception as e:
            logger.error(f"   ✗ Error: {e}")
            return {
                'file': Path(file_path).name,
                'format': Path(file_path).suffix,
                'status': 'Failed',
                'error': str(e)
            }

    def chunk_document(self, file_path: str, dl_doc) -> dict:
        """Chunk a document and return metadata.

        :param file_path: Path to the document file.
        :param dl_doc: Docling document object.
        :return: Metadata dictionary about the chunking result.
        """
        try:
            chunks_info = {
                'file': Path(file_path).name,
                'format': Path(file_path).suffix,
                'status': 'Success'
            }
            # Chunk document
            logger.info(f"   Step: Chunking document...")
            chunk_iter = self.chunker.chunk(dl_doc=dl_doc)
            chunks = list(chunk_iter)
            chunks_info['num_chunks'] = len(chunks)
            logger.info(f"   ✓ Generated {len(chunks)} chunks")

            chunks_info['chunks'] = [
                {
                    'id': uuid.uuid4().hex,
                    'content': self.chunker.contextualize(chunk=chunk)
                } for chunk in chunks
            ]

            return chunks_info

        except Exception as e:
            logger.error(f"   ✗ Error: {e}")
            return {
                'file': Path(file_path).name,
                'format': Path(file_path).suffix,
                'status': 'Failed',
                'error': str(e)
            }

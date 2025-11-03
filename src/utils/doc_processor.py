import uuid
from pathlib import Path
from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter

from src.configs.logger import logger


class DoclingProcessor:
    def __init__(self, converter: DocumentConverter, chunker: HybridChunker):
        self.converter = converter
        self.chunker = chunker

    def process_document(self, file_path: str) -> dict:
        """Process a single document and return metadata."""
        try:
            logger.info(f"📄 Processing: {Path(file_path).name}")

            # Convert document
            result = self.converter.convert(file_path)
            dl_doc = result.document

            # Convert to markdown
            logger.info(f"   Step: Converting document to markdown...")
            markdown = dl_doc.export_to_markdown()
            # Save output
            output_file = f"data/output_{Path(file_path).stem}.md"
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
        """Chunk a document and return metadata."""
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
            # # Save chunks
            # output_path = f"data/chunks_{Path(file_path).stem}.txt"
            # with open(output_path, 'w', encoding='utf-8') as f:
            #     for i, chunk in enumerate(chunks):
            #         f.write(f"{'='*60}\n")
            #         f.write(f"CHUNK {i}\n")
            #         f.write(f"{'='*60}\n")

            #         # Use contextualize to preserve headings and metadata
            #         contextualized_text = self.chunker.contextualize(
            #             chunk=chunk)
            #         f.write(contextualized_text)
            #         f.write("\n\n")
            #     logger.info(f"\n✓ Chunks saved to: {output_path}")

            return chunks_info

        except Exception as e:
            logger.error(f"   ✗ Error: {e}")
            return {
                'file': Path(file_path).name,
                'format': Path(file_path).suffix,
                'status': 'Failed',
                'error': str(e)
            }

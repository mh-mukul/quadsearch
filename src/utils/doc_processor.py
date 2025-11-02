from pathlib import Path
from annotated_types import doc
from transformers import AutoTokenizer
from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter

from src.configs.logger import logger

converter = DocumentConverter()
model_id = "sentence-transformers/all-MiniLM-L6-v2"
tokenizer = AutoTokenizer.from_pretrained(model_id)
chunker = HybridChunker(
    tokenizer=tokenizer,
    max_tokens=512,
    merge_peers=True  # Merge small adjacent chunks
)


def process_document(file_path: str) -> dict:
    """Process a single document and return metadata."""
    try:
        logger.info(f"📄 Processing: {Path(file_path).name}")

        # Convert document
        result = converter.convert(file_path)
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
            'status': 'Success'
        }

        doc_info['output_file'] = output_file

        logger.info(f"   ✓ Converted successfully")
        logger.info(f"   ✓ Output: {output_file}")

        # Chunk document
        logger.info(f"   Step: Chunking document...")
        chunk_iter = chunker.chunk(dl_doc=dl_doc)
        chunks = list(chunk_iter)
        doc_info['num_chunks'] = len(chunks)
        logger.info(f"   ✓ Generated {len(chunks)} chunks")

        output_path = f"data/chunks_{Path(file_path).stem}.txt"
        # Save chunks
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, chunk in enumerate(chunks):
                f.write(f"{'='*60}\n")
                f.write(f"CHUNK {i}\n")
                f.write(f"{'='*60}\n")

                # Use contextualize to preserve headings and metadata
                contextualized_text = chunker.contextualize(chunk=chunk)
                f.write(contextualized_text)
                f.write("\n\n")
            print(f"\n✓ Chunks saved to: {output_path}")

        return doc_info

    except Exception as e:
        logger.error(f"   ✗ Error: {e}")
        return {
            'file': Path(file_path).name,
            'format': Path(file_path).suffix,
            'status': 'Failed',
            'error': str(e)
        }

from docling.document_converter import DocumentConverter
from pathlib import Path

converter = DocumentConverter()


def process_document(file_path: str) -> dict:
    """Process a single document and return metadata."""
    try:
        print(f"\n📄 Processing: {Path(file_path).name}")

        # Convert document
        result = converter.convert(file_path)

        # Export to markdown
        markdown = result.document.export_to_markdown()

        # Get document info
        doc_info = {
            'file': Path(file_path).name,
            'format': Path(file_path).suffix,
            'status': 'Success',
            'markdown_length': len(markdown),
            'preview': markdown[:200].replace('\n', ' ')
        }

        # Save output
        output_file = f"data/output_{Path(file_path).stem}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown)

        doc_info['output_file'] = output_file

        print(f"   ✓ Converted successfully")
        print(f"   ✓ Output: {output_file}")

        return doc_info

    except Exception as e:
        print(f"   ✗ Error: {e}")
        return {
            'file': Path(file_path).name,
            'format': Path(file_path).suffix,
            'status': 'Failed',
            'error': str(e)
        }

from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker
from transformers import AutoTokenizer
from pathlib import Path


def chunk_document(file_path: str, max_tokens: int = 512):
    """Convert and chunk document using HybridChunker."""

    print(f"\n📄 Processing: {Path(file_path).name}")

    # Step 1: Convert document to DoclingDocument
    print("   Step 1: Converting document...")
    converter = DocumentConverter()
    result = converter.convert(file_path)
    doc = result.document

    # Step 2: Initialize tokenizer (using sentence-transformers model)
    print("   Step 2: Initializing tokenizer...")
    model_id = "sentence-transformers/all-MiniLM-L6-v2"
    tokenizer = AutoTokenizer.from_pretrained(model_id)

    # Step 3: Create HybridChunker
    print(f"   Step 3: Creating chunker (max {max_tokens} tokens)...")
    chunker = HybridChunker(
        tokenizer=tokenizer,
        max_tokens=max_tokens,
        merge_peers=True  # Merge small adjacent chunks
    )

    # Step 4: Generate chunks
    print("   Step 4: Generating chunks...")
    chunk_iter = chunker.chunk(dl_doc=doc)
    chunks = list(chunk_iter)

    return chunks, tokenizer, chunker


def analyze_chunks(chunks, tokenizer):
    """Analyze and display chunk statistics."""

    print("\n" + "=" * 60)
    print("CHUNK ANALYSIS")
    print("=" * 60)

    total_tokens = 0
    chunk_sizes = []

    for i, chunk in enumerate(chunks):
        # Get text content
        text = chunk.text
        tokens = tokenizer.encode(text)
        token_count = len(tokens)

        total_tokens += token_count
        chunk_sizes.append(token_count)

        # Display first 3 chunks in detail
        if i < 3:
            print(f"\n--- Chunk {i} ---")
            print(f"Tokens: {token_count}")
            print(f"Characters: {len(text)}")
            print(f"Preview: {text[:150]}...")

            # Show metadata if available
            if hasattr(chunk, 'meta') and chunk.meta:
                print(f"Metadata: {chunk.meta}")

    # Summary statistics
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)
    print(f"Total chunks: {len(chunks)}")
    print(f"Total tokens: {total_tokens}")
    print(f"Average tokens per chunk: {total_tokens / len(chunks):.1f}")
    print(f"Min tokens: {min(chunk_sizes)}")
    print(f"Max tokens: {max(chunk_sizes)}")

    # Token distribution
    print(f"\nToken distribution:")
    ranges = [(0, 128), (128, 256), (256, 384), (384, 512)]
    for start, end in ranges:
        count = sum(1 for size in chunk_sizes if start <= size < end)
        print(f"  {start}-{end} tokens: {count} chunks")


def save_chunks(chunks, chunker, output_path: str):
    """Save chunks to file with separators, preserving context and headings."""

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
    print("   (with preserved headings and document context)")

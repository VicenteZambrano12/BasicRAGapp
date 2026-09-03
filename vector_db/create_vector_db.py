import os
import re
import sys
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from utils.vector_db_manager import get_vector_store
from config.config_loader import config

def extract_folder_and_subject(path: str):
    """Extract folder name and subject from file path."""
    folder_name = os.path.basename(os.path.dirname(path))
    filename = os.path.splitext(os.path.basename(path))[0]
    
    suffix = f"_{folder_name.lower()}"
    if filename.lower().endswith(suffix):
        subject = filename[: -len(suffix)]
    else:
        subject = filename
    
    return folder_name, subject

def create_vector_db(path, use_ultra_compact=False):
    """
    Create vector database with optimized chunking for context window management.
    Uses Google Gemini Embeddings.
    """
    folder, subject = extract_folder_and_subject(path)
    
    print("Loading Gemini embeddings model...")
    

    try:
        embeddings = VertexAIEmbeddings(
            model_name=config("EMBEDDING_MODEL", default="text-embedding-004"),
            project=config("GOOGLE_CLOUD_PROJECT"),
            location=config("GOOGLE_CLOUD_LOCATION", default="us-central1"),
        )
        print("✓ Gemini Embeddings model loaded (text-embedding-004)")
    except Exception as e:
        print(f"❌ Failed to initialize Gemini embeddings: {e}")
        raise e
    # Get vector store (will use configuration from environment)
    print(f"Connecting to vector database for collection: {subject}")
    vector_store = get_vector_store(
        collection_name=subject,
        embeddings=embeddings
    )
    print("✓ Vector store connected")
    
    # Load PDF
    print(f"Loading PDF from: {path}")
    loader = PyPDFLoader(path)
    docs = loader.load()
    
    print(f"✓ Loaded {len(docs)} pages from PDF")
    
    # Clean all document content
    print("Cleaning document content...")
    for doc in docs:
        doc.page_content = clean_text(doc.page_content)
    
    # Configure chunking based on mode
    if use_ultra_compact:
        chunk_size = 300
        chunk_overlap = 30
        print("Using ultra-compact chunking (300 chars)")
    else:
        chunk_size = 500
        chunk_overlap = 50
        print("Using standard compact chunking (500 chars)")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    all_splits = text_splitter.split_documents(docs)
    
    # Filter out empty or invalid chunks and clean content
    print("Validating and cleaning chunks...")
    valid_splits = []
    for doc in all_splits:
        # Clean the content
        cleaned_content = clean_text(doc.page_content)
        
        # Only keep non-empty chunks
        if cleaned_content and len(cleaned_content.strip()) > 0:
            doc.page_content = cleaned_content
            valid_splits.append(doc)
    
    all_splits = valid_splits
    
    print(f"✓ Created {len(all_splits)} valid chunks")
    avg_size = sum(len(doc.page_content) for doc in all_splits) / len(all_splits) if all_splits else 0
    print(f"  Average chunk size: {avg_size:.0f} chars")
    
    # Add metadata
    for doc in all_splits:
        if use_ultra_compact:
            doc.metadata['compact'] = True
        doc.metadata['chunk_size'] = chunk_size
    
    # Add documents in batches
    # Note: Gemini API has rate limits, so keeping batch size reasonable is good
    batch_size = 100 
    total_batches = (len(all_splits) + batch_size - 1) // batch_size
    
    print(f"Adding {len(all_splits)} documents in {total_batches} batches...")
    
    failed_docs = []
    for i in range(0, len(all_splits), batch_size):
        batch = all_splits[i:i + batch_size]
        batch_num = i//batch_size + 1
        
        try:
            vector_store.add_documents(documents=batch)
            print(f"  ✓ Batch {batch_num}/{total_batches} added")
        except Exception as e:
            print(f"  ❌ Error in batch {batch_num}: {str(e)[:100]}")
            print(f"  → Attempting to add documents individually...")
            
            # Try adding documents one by one
            for j, doc in enumerate(batch):
                doc_idx = i + j
                try:
                    # Extra validation before adding
                    vector_store.add_documents(documents=[doc])
                except Exception as doc_error:
                    failed_docs.append((doc_idx, doc, str(doc_error)))
                    safe_preview = doc.page_content[:100].encode('ascii', errors='ignore').decode('ascii')
                    print(f"    ✗ Failed to add document {doc_idx}: {str(doc_error)[:80]}")
                    print(f"      Content preview: {safe_preview}...")
    
    if failed_docs:
        print(f"\n⚠ Warning: {len(failed_docs)} documents failed to add")
        print(f"✓ Successfully added {len(all_splits) - len(failed_docs)}/{len(all_splits)} documents")
    else:
        print(f"✓ All documents added successfully")
    
    print(f"✓ Vector DB created for collection: {subject}")
    return subject

def create_vector_db_ultra_compact(path):
    """
    Ultra-compact version for very large documents.
    Wrapper around create_vector_db with ultra_compact=True.
    """
    return create_vector_db(path, use_ultra_compact=True)

if __name__ == "__main__":
    # Example usage
    if len(sys.argv) < 2:
        print("Usage: python create_vector_db.py <path_to_pdf> [--ultra-compact]")
        print("\nExample:")
        print('  python create_vector_db.py "docs/history_andalucia.pdf"')
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    use_ultra = "--ultra-compact" in sys.argv
    
    print("=" * 60)
    print("Creating Vector Database (Gemini Embeddings)")
    print("=" * 60)
    print(f"Vector DB Type: {os.getenv('VECTOR_DB_TYPE', 'qdrant')}")
    print(f"Mode: {'Ultra-Compact' if use_ultra else 'Standard'}")
    print("=" * 60)
    
    try:
        collection = create_vector_db(pdf_path, use_ultra_compact=use_ultra)
        print("=" * 60)
        print(f"✅ SUCCESS! Collection '{collection}' created")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
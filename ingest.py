import os
import glob
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.embeddings import Embeddings
from google import genai

# Assuming these are available in your repository structure
from src.config.config_loader import config
from vector_db.manager import get_vector_store

class ModernGeminiEmbeddings(Embeddings):
    """
    A custom LangChain Embeddings wrapper that uses the modern 
    google-genai SDK to avoid v1beta 404 errors and deprecation warnings.
    """
    def __init__(self, api_key: str, model: str = "text-embedding-004"):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # Optimizes representations specifically for document candidate retrieval
        response = self.client.models.embed_content(
            model=self.model,
            contents=texts,
            config={"task_type": "RETRIEVAL_DOCUMENT"}
        )
        return [e.values for e in response.embeddings]

    def embed_query(self, text: str) -> list[float]:
        # Optimizes representations to identify matching document spaces
        response = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config={"task_type": "RETRIEVAL_QUERY"}
        )
        return response.embeddings[0].values

def clean_text(text: str) -> str:
    """Normalize whitespace while preserving paragraph boundaries."""
    paragraphs = (" ".join(line.split()) for line in text.splitlines())
    return "\n\n".join(paragraph for paragraph in paragraphs if paragraph)

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

def create_vector_db(path: str, use_ultra_compact=False):
    """
    Create vector database with optimized chunking for context window management.
    Uses Google Gemini Embeddings with Task Type Conditioning.
    """
    folder, subject = extract_folder_and_subject(path)
    
    print(f"\nLoading Gemini embeddings model for {subject}...")
    try:
        google_api_key = config(
            "GOOGLE_API_KEY",
            default=os.getenv("GOOGLE_API_KEY") or os.getenv("GCP_API_KEY") or os.getenv("GEMINI_API_KEY"),
        )
        
        if not google_api_key:
            raise RuntimeError("Gemini API key is not configured.")
            
        # 1. Asymmetric Subspace Alignment handled inside ModernGeminiEmbeddings
        embeddings = ModernGeminiEmbeddings(
            model="text-embedding-004",
            api_key=google_api_key
        )
        print(f"✓ Gemini Embeddings model loaded (text-embedding-004)")
    except Exception as e:
        print(f"❌ Failed to initialize Gemini embeddings: {e}")
        raise e

    print(f"Connecting to vector database for collection: {subject}")
    # Note: Ensure get_vector_store configures Qdrant with Distance.DOT and Scalar Quantization
    vector_store = get_vector_store(
        collection_name=subject,
        embeddings=embeddings
    )
    print("✓ Vector store connected")
    
    print(f"Loading PDF from: {path}")
    loader = PyPDFLoader(path)
    docs = loader.load()
    
    # 2. Context-Preserving Chunking: Adjusted to token-equivalent char sizes
    if use_ultra_compact:
        # ~256 tokens / 10% overlap for Factoid/Q&A
        chunk_size = 1000
        chunk_overlap = 100
        print("Using compact chunking (~256 tokens)")
    else:
        # ~512 tokens / 15% overlap for Technical/Legal
        chunk_size = 2000
        chunk_overlap = 300
        print("Using standard chunking (~512 tokens)")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    all_splits = text_splitter.split_documents(docs)
    
    print("Validating, cleaning, and injecting context into chunks...")
    valid_splits = []
    for doc in all_splits:
        cleaned_content = clean_text(doc.page_content)
        
        if cleaned_content and len(cleaned_content.strip()) > 0:
            # 3. Metadata Enrichment and Context Injection
            # Prepend the structural breadcrumb (Document Title) to the text
            doc.page_content = f"{subject.replace('-', ' ').title()}\n\n{cleaned_content}"
            
            if use_ultra_compact:
                doc.metadata['compact'] = True
            doc.metadata['chunk_size'] = chunk_size
            valid_splits.append(doc)
    
    all_splits = valid_splits
    
    batch_size = 100 
    total_batches = (len(all_splits) + batch_size - 1) // batch_size
    print(f"Adding {len(all_splits)} documents in {total_batches} batches...")
    
    failed_docs = []
    for i in range(0, len(all_splits), batch_size):
        batch = all_splits[i:i + batch_size]
        try:
            vector_store.add_documents(documents=batch)
        except Exception as e:
            # Fallback to single insertion on batch failure
            for j, doc in enumerate(batch):
                try:
                    vector_store.add_documents(documents=[doc])
                except Exception as doc_error:
                    failed_docs.append((i+j, doc, str(doc_error)))
    
    if failed_docs:
        print(f"\n⚠ Warning: {len(failed_docs)} documents failed to add")
    else:
        print(f"✓ All documents added successfully")
        
    return subject

def process_directory(content_dir: str):
    base_path = Path(content_dir)
    pdf_files = list(base_path.rglob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found inside {content_dir}.")
        return

    for pdf_path in pdf_files:
        print(f"\n--- Processing: {pdf_path.name} ---")
        try:
            collection = create_vector_db(str(pdf_path), use_ultra_compact=False)
            print(f"✅ SUCCESS! Indexed to collection '{collection}'")
        except Exception as e:
            print(f"\n❌ ERROR processing '{pdf_path.name}': {e}")

if __name__ == "__main__":
    CONTENT_DIRECTORY = os.getenv("CONTENT_DIRECTORY", "./content")
    process_directory(CONTENT_DIRECTORY)
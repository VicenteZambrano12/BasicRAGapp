import hashlib
import mimetypes
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.cloud import storage
from google.cloud.exceptions import NotFound
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.embeddings import Embeddings
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv(override=True)

# Assuming these are available in your repository structure
from src.config.config_loader import config
from vector_db.manager import get_vector_store

class ModernGeminiEmbeddings(Embeddings):
    """
    A custom LangChain Embeddings wrapper that automatically detects 
    and bridges Vertex AI Enterprise and Google AI Studio environments.
    """
    def __init__(self, model: str):
        self.model = model
        self.client = genai.Client(
            vertexai=True,
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION"),
        )

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
    """Derive the collection name from the immediate parent folder, e.g. content/Biologia/*.pdf -> 'biologia'."""
    folder_name = os.path.basename(os.path.dirname(path))
    subject = re.sub(r"[^a-z0-9_]+", "_", folder_name.strip().lower()).strip("_")
    return folder_name, subject


def compute_sha256(path: str) -> str:
    """Compute the SHA-256 checksum of a local file, streaming to bound memory use."""
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def _upload_blob(blob, local_path: str, file_hash: str, generation) -> None:
    # if_generation_match makes the upload idempotent under concurrent runs:
    # 0 requires the object to not exist yet, otherwise it must match the current generation.
    blob.metadata = {
        "source_sha256": file_hash,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }
    blob.upload_from_filename(local_path, if_generation_match=generation)


def upload_to_gcs(bucket: "storage.Bucket", local_path: str, object_name: str) -> dict:
    """
    Upload a local file to GCS unless an identical copy is already stored there.
    Returns metadata linking the vector payloads back to the GCS object.
    """
    file_hash = compute_sha256(local_path)
    blob = bucket.blob(object_name)

    try:
        blob.reload()
        existing_hash = (blob.metadata or {}).get("source_sha256")
        if existing_hash == file_hash:
            print(f"↷ Skipping GCS upload (unchanged): {object_name}")
        else:
            print(f"⬆ Uploading (changed): {object_name}")
            _upload_blob(blob, local_path, file_hash, blob.generation)
            blob.reload()
    except NotFound:
        print(f"⬆ Uploading (new): {object_name}")
        _upload_blob(blob, local_path, file_hash, 0)
        blob.reload()

    mime_type, _ = mimetypes.guess_type(local_path)
    return {
        "gcs_uri": f"gs://{bucket.name}/{object_name}",
        "bucket_name": bucket.name,
        "object_name": object_name,
        "source_sha256": file_hash,
        "gcs_generation": str(blob.generation),
        "mime_type": mime_type or "application/octet-stream",
        "file_size_bytes": blob.size,
    }

def create_vector_db(path: str, bucket: "storage.Bucket", content_root: str, use_ultra_compact=False):
    """
    Upload the source file to GCS, then create/update the vector database with
    optimized chunking for context window management. Uses Google Gemini
    Embeddings with Task Type Conditioning. Each chunk's metadata links back
    to the GCS object it was extracted from.
    """
    folder, subject = extract_folder_and_subject(path)

    relative_path = Path(path).resolve().relative_to(Path(content_root).resolve()).as_posix()
    print(f"Uploading source file to GCS: {relative_path}")
    gcs_location = upload_to_gcs(bucket, path, relative_path)
    print(f"✓ GCS object ready: {gcs_location['gcs_uri']} (generation {gcs_location['gcs_generation']})")

    print(f"\nLoading Gemini embeddings model for {subject}...")
    try:
        credentials_path = config("GOOGLE_APPLICATION_CREDENTIALS")
        if not os.path.exists(credentials_path):
            raise RuntimeError(f"Google credentials file was not found: {credentials_path}")

        embedding_model = config("EMBEDDING_MODEL")
        embeddings = ModernGeminiEmbeddings(
            model=embedding_model,
        )
        print(f"✓ Gemini Embeddings model loaded ({embedding_model})")
    except Exception as e:
        print(f"❌ Failed to initialize Gemini embeddings: {e}")
        raise e

    print(f"Connecting to vector database for collection: {subject}")
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
        chunk_size = 1000
        chunk_overlap = 100
        print("Using compact chunking (~256 tokens)")
    else:
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
    ingested_at = datetime.now(timezone.utc).isoformat()
    valid_splits = []
    for doc in all_splits:
        cleaned_content = clean_text(doc.page_content)
        
        if cleaned_content and len(cleaned_content.strip()) > 0:
            # 3. Metadata Enrichment and Context Injection
            doc.page_content = f"{subject.replace('-', ' ').title()}\n\n{cleaned_content}"
            
            if use_ultra_compact:
                doc.metadata['compact'] = True
            doc.metadata['chunk_size'] = chunk_size

            # Link this chunk back to the exact GCS object it was extracted from.
            doc.metadata.update(gcs_location)
            doc.metadata['relative_path'] = relative_path
            doc.metadata['file_name'] = os.path.basename(path)
            doc.metadata['embedding_model'] = embedding_model
            doc.metadata['ingested_at'] = ingested_at
            page_number = doc.metadata.get('page')
            if page_number is not None:
                doc.metadata['page_number'] = page_number + 1

            valid_splits.append(doc)

    # Chunk position/count depends on the final valid_splits list, so it is
    # assigned in a second pass once empty chunks have been filtered out.
    point_ids = []
    for index, doc in enumerate(valid_splits):
        doc.metadata['chunk_index'] = index
        doc.metadata['chunk_count'] = len(valid_splits)
        doc.metadata['chunk_id'] = f"{relative_path}:{index:06d}"
        # Deterministic ID: reruns upsert the same point instead of duplicating it.
        point_ids.append(str(uuid.uuid5(uuid.NAMESPACE_URL, doc.metadata['chunk_id'])))

    all_splits = valid_splits
    
    batch_size = 100 
    total_batches = (len(all_splits) + batch_size - 1) // batch_size
    print(f"Adding {len(all_splits)} documents in {total_batches} batches...")
    
    failed_docs = []
    for i in range(0, len(all_splits), batch_size):
        batch = all_splits[i:i + batch_size]
        batch_ids = point_ids[i:i + batch_size]
        try:
            vector_store.add_documents(documents=batch, ids=batch_ids)
        except Exception as e:
            for j, doc in enumerate(batch):
                try:
                    vector_store.add_documents(documents=[doc], ids=[batch_ids[j]])
                except Exception as doc_error:
                    failed_docs.append((i+j, doc, str(doc_error)))
    
    if failed_docs:
        print(f"\n⚠ Warning: {len(failed_docs)} documents failed to add")
    else:
        print(f"✓ All documents added successfully")
        # Safe to prune now: every current chunk was just (re)upserted successfully,
        # so any stored chunk at or beyond this count must be stale.
        vector_store.delete_stale_chunks(relative_path, len(all_splits))
        
    return subject

def process_directory(content_dir: str, bucket: "storage.Bucket"):
    base_path = Path(content_dir)
    pdf_files = list(base_path.rglob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found inside {content_dir}.")
        return

    for pdf_path in pdf_files:
        print(f"\n--- Processing: {pdf_path.name} ---")
        try:
            collection = create_vector_db(str(pdf_path), bucket, content_dir, use_ultra_compact=False)
            print(f"✅ SUCCESS! Indexed to collection '{collection}'")
        except Exception as e:
            print(f"\n❌ ERROR processing '{pdf_path.name}': {e}")

if __name__ == "__main__":
    CONTENT_DIRECTORY = os.getenv("CONTENT_DIRECTORY", "./content")
    bucket_name = config("GCS_BUCKET_NAME")
    storage_client = storage.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))
    gcs_bucket = storage_client.bucket(bucket_name)
    process_directory(CONTENT_DIRECTORY, gcs_bucket)
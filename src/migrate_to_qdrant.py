#!/usr/bin/env python3
"""
Migration script: Chroma → Qdrant (Local or Cloud)
Migrate existing Chroma vector databases to Qdrant
"""
import os
import sys
from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

def get_embeddings():
    """Load embeddings model"""
    print("📦 Loading embeddings model...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True},
    )
    print("✅ Embeddings loaded\n")
    return embeddings

def get_qdrant_config(use_local=False, url=None, api_key=None):
    """Get Qdrant configuration for connection"""
    if use_local:
        # Local Qdrant container
        local_url = url or "http://localhost:6333"
        print(f"🔧 Connecting to local Qdrant: {local_url}")
        return {"url": local_url, "api_key": None}
    else:
        # Qdrant Cloud
        if not url or not api_key:
            raise ValueError("Qdrant Cloud requires URL and API key")
        print(f"🌐 Connecting to Qdrant Cloud: {url}")
        return {"url": url, "api_key": api_key}

def find_chroma_databases(base_path="./vector_db"):
    """Find all Chroma databases in the vector_db directory"""
    base = Path(base_path)
    if not base.exists():
        return []
    
    # Chroma creates a chroma.sqlite3 file in each collection directory
    databases = []
    for item in base.iterdir():
        if item.is_dir():
            chroma_file = item / "chroma.sqlite3"
            if chroma_file.exists():
                databases.append(item.name)
    
    return databases

def migrate_collection(collection_name, embeddings, qdrant_config, chroma_path="./vector_db", dry_run=False):
    """Migrate a single collection from Chroma to Qdrant"""
    print(f"\n{'='*60}")
    print(f"📦 Migrating: {collection_name}")
    print(f"{'='*60}")
    
    # Load from Chroma
    chroma_db_path = os.path.join(chroma_path, collection_name)
    print(f"📂 Loading from Chroma: {chroma_db_path}")
    
    try:
        chroma_db = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=chroma_db_path,
        )
        
        # Get all documents
        print("📥 Retrieving documents from Chroma...")
        results = chroma_db.get()
        
        if not results['ids']:
            print("⚠️  No documents found in collection")
            return False
        
        doc_count = len(results['ids'])
        print(f"✅ Found {doc_count} documents")
        
        # Reconstruct documents
        from langchain_core.documents import Document
        documents = []
        for i in range(doc_count):
            doc = Document(
                page_content=results['documents'][i],
                metadata=results['metadatas'][i] if results['metadatas'] else {}
            )
            documents.append(doc)
        
        if dry_run:
            print("🔍 DRY RUN - Would migrate:")
            print(f"   Collection: {collection_name}")
            print(f"   Documents: {doc_count}")
            avg_length = sum(len(d.page_content) for d in documents) / len(documents)
            print(f"   Avg doc size: {avg_length:.0f} chars")
            return True
        
        # Upload to Qdrant
        print(f"📤 Uploading to Qdrant...")
        
        # Prepare kwargs for QdrantVectorStore
        qdrant_kwargs = {
            "collection_name": collection_name,
            "url": qdrant_config["url"],
        }
        
        # Only add api_key if it's not None
        if qdrant_config["api_key"]:
            qdrant_kwargs["api_key"] = qdrant_config["api_key"]
        
        # Create Qdrant vector store from documents
        qdrant_store = QdrantVectorStore.from_documents(
            documents,
            embeddings,
            **qdrant_kwargs
        )
        
        print(f"✅ Successfully migrated {doc_count} documents!")
        
        # Verify
        print("🔍 Verifying migration...")
        test_query = documents[0].page_content[:100]
        results = qdrant_store.similarity_search(test_query, k=1)
        if results:
            print("✅ Verification successful - documents are searchable")
        else:
            print("⚠️  Warning: Verification failed - check Qdrant connection")
        
        return True
        
    except Exception as e:
        print(f"❌ Error migrating {collection_name}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("  Chroma → Qdrant Migration Tool")
    print("=" * 60)
    print()
    
    # Parse arguments
    dry_run = "--dry-run" in sys.argv
    use_local = "--local" in sys.argv
    chroma_path = "./vector_db"
    specific_collection = None
    custom_url = None
    
    for arg in sys.argv[1:]:
        if arg.startswith("--path="):
            chroma_path = arg.split("=", 1)[1]
        elif arg.startswith("--url="):
            custom_url = arg.split("=", 1)[1]
        elif not arg.startswith("--"):
            specific_collection = arg
    
    # Check Qdrant configuration
    if use_local:
        print("🏠 Using LOCAL Qdrant")
        qdrant_url = custom_url or "http://localhost:6333"
        qdrant_key = None
        print(f"📍 Location: {qdrant_url}")
    else:
        print("☁️  Using Qdrant CLOUD")
        qdrant_url = os.getenv("QDRANT_URL") or custom_url
        qdrant_key = os.getenv("QDRANT_API_KEY")
        
        if not qdrant_url or not qdrant_key:
            print("❌ Error: Qdrant Cloud credentials not set!")
            print()
            print("Please either:")
            print("1. Use --local flag for local Qdrant container")
            print("2. Set environment variables for Qdrant Cloud:")
            print('   export QDRANT_URL="https://your-cluster.qdrant.io:6333"')
            print('   export QDRANT_API_KEY="your-api-key"')
            print()
            sys.exit(1)
        
        print(f"📍 Location: {qdrant_url}")
    
    print()
    
    if dry_run:
        print("🔍 DRY RUN MODE - No data will be uploaded")
        print()
    
    # Get Qdrant configuration
    try:
        qdrant_config = get_qdrant_config(use_local, qdrant_url, qdrant_key)
        
        # Test connection
        test_client = QdrantClient(
            url=qdrant_config["url"],
            api_key=qdrant_config["api_key"]
        )
        test_client.get_collections()  # Test the connection
        print("✅ Connected to Qdrant\n")
    except Exception as e:
        print(f"❌ Failed to connect to Qdrant: {e}")
        sys.exit(1)
    
    # Load embeddings
    embeddings = get_embeddings()
    
    # Find collections to migrate
    if specific_collection:
        collections = [specific_collection]
        print(f"📋 Migrating specific collection: {specific_collection}")
    else:
        collections = find_chroma_databases(chroma_path)
        if not collections:
            print(f"❌ No Chroma databases found in {chroma_path}")
            sys.exit(1)
        print(f"📋 Found {len(collections)} collections to migrate:")
        for col in collections:
            print(f"   • {col}")
    
    print()
    
    # Confirm
    if not dry_run:
        response = input("Continue with migration? (y/n): ")
        if response.lower() != 'y':
            print("❌ Migration cancelled")
            sys.exit(0)
        print()
    
    # Migrate each collection
    success_count = 0
    fail_count = 0
    
    for collection in collections:
        success = migrate_collection(
            collection, 
            embeddings,
            qdrant_config,
            chroma_path, 
            dry_run
        )
        if success:
            success_count += 1
        else:
            fail_count += 1
    
    # Summary
    print()
    print("=" * 60)
    print("  Migration Summary")
    print("=" * 60)
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {fail_count}")
    print()
    
    if not dry_run and success_count > 0:
        print("🎉 Migration complete!")
        print()
        print("Next steps:")
        print("1. Test your application with Qdrant")
        print("2. Verify all data is accessible")
        if use_local:
            print("3. Update your app to connect to local Qdrant")
        print(f"4. (Optional) Remove old Chroma databases:")
        print(f"   rm -rf {chroma_path}")
        print()

if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: python migrate_to_qdrant.py [OPTIONS] [COLLECTION_NAME]")
        print()
        print("Options:")
        print("  --local                Use local Qdrant (default: cloud)")
        print("  --dry-run              Test migration without uploading data")
        print("  --path=PATH            Path to Chroma databases (default: ./vector_db)")
        print("  --url=URL              Custom Qdrant URL")
        print("  COLLECTION_NAME        Migrate specific collection only")
        print()
        print("Examples:")
        print("  # Migrate to LOCAL Qdrant container (dry run)")
        print("  python migrate_to_qdrant.py --local --dry-run")
        print()
        print("  # Migrate all collections to local Qdrant")
        print("  python migrate_to_qdrant.py --local")
        print()
        print("  # Migrate to local Qdrant on custom port")
        print("  python migrate_to_qdrant.py --local --url=http://localhost:6334")
        print()
        print("  # Migrate specific collection to local Qdrant")
        print("  python migrate_to_qdrant.py --local history_andalucia")
        print()
        print("  # Migrate to Qdrant Cloud (requires env vars)")
        print("  python migrate_to_qdrant.py")
        print()
        print("  # Use custom Chroma path")
        print("  python migrate_to_qdrant.py --local --path=/path/to/vector_db")
        print()
        print("Environment variables (for Cloud only):")
        print("  QDRANT_URL      - Your Qdrant Cloud cluster URL")
        print("  QDRANT_API_KEY  - Your Qdrant Cloud API key")
        print()
        print("Local Qdrant Setup:")
        print("  docker-compose up -d qdrant")
        sys.exit(0)
    
    main()
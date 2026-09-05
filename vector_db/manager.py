"""
Vector Database Manager with automatic collection creation
"""
import os
from typing import Optional
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

class QdrantVectorDB:
    """Qdrant Vector Database wrapper with auto-creation"""
    
    def __init__(self, collection_name: str, embeddings):
        self.collection_name = collection_name
        self.embeddings = embeddings
        
        # Get Qdrant configuration
        qdrant_url = os.getenv("QDRANT_URL", "").strip()
        qdrant_host = os.getenv("QDRANT_HOST", "localhost").strip()
        qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        qdrant_api_key = os.getenv("QDRANT_API_KEY", "").strip()
        
        # Accept a full endpoint in either QDRANT_URL or QDRANT_HOST.
        if qdrant_host.startswith(("http://", "https://")) and not qdrant_url:
            qdrant_url = qdrant_host

        # Create Qdrant client - prefer an explicit URL over host:port.
        if qdrant_url:
            print(f"🌐 Connecting to Qdrant at: {qdrant_url}")
            self.client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key if qdrant_api_key else None,
            )
        else:
            print(f"🏠 Connecting to Qdrant at: {qdrant_host}:{qdrant_port}")
            self.client = QdrantClient(
                host=qdrant_host,
                port=qdrant_port,
                api_key=qdrant_api_key if qdrant_api_key else None,
            )
        
        # Check if collection exists, create if not
        self._ensure_collection_exists()
        
        # Initialize vector store
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=collection_name,
            embedding=embeddings,
        )
    
    def _ensure_collection_exists(self):
        """Create collection if it doesn't exist"""
        try:
            # Try to get collection info
            info = self.client.get_collection(self.collection_name)
            print(f"✓ Collection '{self.collection_name}' already exists ({info.points_count} documents)")
        except Exception as e:
            # Collection doesn't exist, create it
            print(f"📦 Creating new collection: {self.collection_name}")
            
            # Get embedding dimension
            sample_embedding = self.embeddings.embed_query("test")
            vector_size = len(sample_embedding)
            
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            print(f"✓ Collection created with vector size: {vector_size}")
    
    def add_documents(self, documents):
        """Add documents to the vector store"""
        return self.vector_store.add_documents(documents)
    
    def similarity_search(self, query, k=4):
        """Search for similar documents"""
        return self.vector_store.similarity_search(query, k=k)
    
    def similarity_search_with_score(self, query, k=4):
        """Search with relevance scores"""
        return self.vector_store.similarity_search_with_score(query, k=k)


def get_vector_store(collection_name: str, embeddings):
    """
    Factory function to get vector store based on configuration
    
    Args:
        collection_name: Name of the collection
        embeddings: Embeddings model instance
        
    Returns:
        Vector store instance
    """
    vector_db_type = os.getenv("VECTOR_DB_TYPE", "qdrant").lower()
    
    if vector_db_type == "qdrant":
        return QdrantVectorDB(collection_name, embeddings)
    elif vector_db_type == "pinecone":
        # TODO: Implement Pinecone support
        raise NotImplementedError("Pinecone support not yet implemented")
    elif vector_db_type == "vertex":
        # TODO: Implement Vertex AI support
        raise NotImplementedError("Vertex AI support not yet implemented")
    else:
        raise ValueError(f"Unsupported vector DB type: {vector_db_type}")
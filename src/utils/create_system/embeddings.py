"""Gemini embeddings client used for both query and document embedding."""

import os
from typing import List, Optional

from google import genai
from langchain_core.embeddings import Embeddings

from src.config.config_loader import config


class GeminiEmbeddings(Embeddings):
    """Query/document embeddings matching those used by ingest.py at ingestion time."""

    def __init__(self, model: str):
        self.model = model
        self.client = genai.Client(
            vertexai=True,
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION"),
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        response = self.client.models.embed_content(
            model=self.model, contents=texts, config={"task_type": "RETRIEVAL_DOCUMENT"}
        )
        return [e.values for e in response.embeddings]

    def embed_query(self, text: str) -> List[float]:
        response = self.client.models.embed_content(
            model=self.model, contents=text, config={"task_type": "RETRIEVAL_QUERY"}
        )
        return response.embeddings[0].values


_embeddings: Optional[GeminiEmbeddings] = None


def get_embeddings() -> GeminiEmbeddings:
    """Return a process-wide cached embeddings client, built on first use."""
    global _embeddings
    if _embeddings is None:
        model = config("EMBEDDING_MODEL", default="text-embedding-004")
        _embeddings = GeminiEmbeddings(model=model)
    return _embeddings

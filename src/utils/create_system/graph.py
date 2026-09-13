"""Builds the per-subject/community retrieval-augmented LangGraph used by chat.

The retrieval step queries the Qdrant collection that ingest.py populated for
that subject (see vector_db/manager.py, which already points at the migrated
Google Cloud Qdrant server via QDRANT_URL). Query embeddings are produced with
the same Gemini embeddings client/model used at ingestion time so query and
document vectors live in the same space.
"""

import logging

from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph

from src.config.config_loader import config
from src.utils.chat.vertex_vision_endpoint import is_configured as vertex_is_configured
from src.utils.create_system.embeddings import get_embeddings
from src.utils.create_system.prompt_loader import load_system_prompt
from src.utils.create_system.state import GraphState, extract_query_text
from src.utils.create_system.subject_resolver import resolve_collection
from src.utils.create_system.vertex_chat_llm import VertexSelfDeployedLLM
from vector_db.manager import get_vector_store

logger = logging.getLogger(__name__)


def _build_llm():
    """Use the self-deployed Vertex endpoint when configured, otherwise Gemini."""
    if vertex_is_configured():
        logger.info("[CREATE_SYSTEM] Using self-deployed Vertex endpoint as the chat LLM")
        return VertexSelfDeployedLLM()

    llm_model = config("LLM_MODEL", default="gemini-2.5-flash-lite")
    return ChatGoogleGenerativeAI(model=llm_model, google_api_key=config("GCP_API_KEY", default=None))


def create_system(subject: str, community: str):
    """Build and compile a retrieval-augmented LangGraph for a subject/community pair."""
    collection = resolve_collection(subject)
    system_prompt = load_system_prompt(subject, community, collection)

    logger.info(f"[CREATE_SYSTEM] Connecting retrieval to Qdrant collection '{collection}'")
    vector_store = get_vector_store(collection_name=collection, embeddings=get_embeddings())

    llm = _build_llm()

    def retrieve(state: GraphState):
        last_human = next(
            (m for m in reversed(state["messages"]) if getattr(m, "type", None) == "human"),
            None,
        )
        query = extract_query_text(last_human).strip()
        documents = vector_store.similarity_search(query, k=4) if query else []
        logger.info(f"[RETRIEVE] {len(documents)} chunk(s) retrieved for query: {query[:80]!r}")
        return {"documents": documents}

    def generate(state: GraphState):
        documents = state.get("documents", [])
        if documents:
            context = "\n\n---\n\n".join(doc.page_content for doc in documents)
        else:
            context = "No se encontró contexto relevante en el material de la asignatura."

        context_message = SystemMessage(
            content=f"{system_prompt}\n\nContexto recuperado del material de estudio:\n{context}"
        )
        response = llm.invoke([context_message, *state["messages"]])
        return {"messages": [response]}

    graph_builder = StateGraph(GraphState)
    graph_builder.add_node("retrieve", retrieve)
    graph_builder.add_node("generate", generate)
    graph_builder.add_edge(START, "retrieve")
    graph_builder.add_edge("retrieve", "generate")
    graph_builder.add_edge("generate", END)

    return graph_builder.compile()

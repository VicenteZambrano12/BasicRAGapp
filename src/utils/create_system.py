import logging
import os
from typing import List, Any, Dict

# LangChain & LangGraph imports
from langchain_openai import AzureChatOpenAI
from langgraph.graph import MessagesState, StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
# Import Google Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Config & Utils
from src.config.config_loader import config
from src.utils.read_prompt import read_text_file
from src.utils.change_names import (
    community_rename_for_folder,
    join_path_subject,
    subject_rename,
)
from src.utils.vector_db_manager import get_vector_store
from src.utils.token_counter import get_token_counter

logger = logging.getLogger(__name__)

# --- DEFINICIÓN DEL ESTADO ---
class AgentState(MessagesState):
    documents: List[Any]

# --- SINGLETON PARA EMBEDDINGS ---
_embeddings_model = None

def get_embeddings():
    global _embeddings_model
    if _embeddings_model is None:
        try:
            api_key = config("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in config")
                
            _embeddings_model = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=api_key,
                task_type="retrieval_document"
            )
        except Exception as e:
            logger.error(f"Error loading Gemini embeddings model: {e}")
            raise e
    return _embeddings_model

# --- FUNCIÓN PRINCIPAL ---
def create_system(subject, community):
    # Configuración de claves
    os.environ["AZURE_OPENAI_API_KEY"] = config("AZURE_OPENAI_API_KEY")
    os.environ["GOOGLE_API_KEY"] = config("GOOGLE_API_KEY")

    token_counter = get_token_counter()

    llm = AzureChatOpenAI(
        azure_endpoint=config("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=config("DEPLOYMENT_NAME"),
        openai_api_version=config("API_version"),
        temperature=0.1,
        max_tokens=1000,
    )

    embeddings = get_embeddings()
    community_renamed = community_rename_for_folder(community)
    subject_renamed = subject_rename(subject)

    if not community_renamed or not subject_renamed:
        raise ValueError(f"Invalid community '{community}' or subject '{subject}'")

    vector_store = get_vector_store(
        collection_name=subject_renamed,
        embeddings=embeddings
    )

    # --- NODO 1: RECUPERACIÓN OBLIGATORIA ---
    def retrieve_node(state: AgentState):
        messages = state["messages"]
        last_human_message = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
        
        query = ""
        
        # 1. Estrategia A: Texto explícito del usuario
        if last_human_message:
            content = last_human_message.content
            if isinstance(content, str):
                query = content
            elif isinstance(content, list):
                text_parts = [
                    item.get("text", "") 
                    for item in content 
                    if isinstance(item, dict) and item.get("type") == "text"
                ]
                query = " ".join(text_parts)

        # 2. Estrategia B (FALLBACK): Si no hay texto, usar la descripción de la imagen
        # Tu 'main.py' inyecta un SystemMessage con "Visual context extracted: ..."
        if not query.strip():
            for m in reversed(messages):
                if isinstance(m, SystemMessage) and "Visual context extracted:" in str(m.content):
                    # Usamos la descripción generada por OCR/Visión como query
                    clean_desc = str(m.content).replace("Visual context extracted:", "").strip()
                    
                    # Limpieza extra si viene con etiquetas "Image:" o "Q:"
                    if "Image:" in clean_desc:
                        clean_desc = clean_desc.split("Image:", 1)[1]
                    if "Q:" in clean_desc:
                        clean_desc = clean_desc.split("Q:", 1)[0]
                        
                    query = clean_desc.strip()
                    logger.info(f"[RETRIEVE] Usando descripción de imagen como búsqueda: '{query[:50]}...'")
                    break

        # 3. Si sigue vacío, salimos silenciosamente (sin Warning feo)
        if not query.strip():
            logger.info("[RETRIEVE] No hay texto ni imagen descriptible para buscar. Saltando RAG.")
            return {"documents": []}

        # 4. Búsqueda Vectorial
        try:
            # Buscamos en la BD usando la pregunta O la descripción de la imagen
            retrieved_docs = vector_store.similarity_search(query, k=3)
            logger.info(f"[RETRIEVE] Found {len(retrieved_docs)} docs for query: '{query[:30]}...'")
            return {"documents": retrieved_docs}
        except Exception as e:
            logger.error(f"[RETRIEVE] Error querying vector store: {e}")
            return {"documents": []}
        
    # --- NODO 2: GENERACIÓN ROBUSTA (TEXTO + VISIÓN) ---
    def generate_node(state: AgentState):
        docs = state.get("documents", [])
        messages = state["messages"]

        # 1. Procesar contexto
        MAX_CHARS_PER_DOC = 1000
        context_parts = []
        for i, doc in enumerate(docs):
            content = doc.page_content
            if len(content) > MAX_CHARS_PER_DOC:
                content = content[:MAX_CHARS_PER_DOC] + "...[truncated]"
            source = doc.metadata.get("source", "unknown")
            context_parts.append(f"Document {i+1} (Source: {source}):\n{content}")

        docs_content = "\n\n".join(context_parts) if context_parts else "No relevant context found."

        # 2. Cargar Prompt
        path_folder_prompt = os.path.join(os.path.dirname(__file__), "..", f"prompts/{community_renamed}/")
        final_path = join_path_subject(path=path_folder_prompt, subject_raw=subject, community=community_renamed, prompt=True)
        base_prompt = read_text_file(final_path) or "You are a helpful assistant."

        # 3. Construir Prompt del Sistema
        system_message_content = (
            f"{base_prompt}\n\n"
            f"--- RELEVANT CONTEXT FROM DATABASE ---\n"
            f"{docs_content}\n"
            f"--------------------------------------\n"
            f"Use the context above to answer the user's question."
        )

        # 4. Procesar historial (HÍBRIDO: TEXTO vs MULTIMODAL)
        conversation_messages = []
        for m in messages:
            if isinstance(m, (HumanMessage, AIMessage)):
                msg_content = m.content
                
                # Verificamos si es una lista (formato potencial multimodal)
                if isinstance(msg_content, list):
                    # Comprobamos si REALMENTE tiene una imagen
                    has_image = any(item.get("type") == "image_url" for item in msg_content if isinstance(item, dict))
                    
                    if has_image:
                        # CASO A: Tiene imagen -> Dejar como lista para GPT-4o-mini
                        pass 
                    else:
                        # CASO B: Es una lista pero solo tiene texto -> APLANAR A STRING
                        # Esto evita el error "finish_reason: length" en Azure cuando no hay fotos
                        text_parts = [
                            item.get("text", "") 
                            for item in msg_content 
                            if isinstance(item, dict) and item.get("type") == "text"
                        ]
                        msg_content = " ".join(text_parts)
                        
                        # Reconstruimos el mensaje con contenido string
                        if isinstance(m, HumanMessage):
                            m = HumanMessage(content=msg_content)
                        elif isinstance(m, AIMessage):
                            m = AIMessage(content=msg_content)
                
                conversation_messages.append(m)
        
        conversation_messages = conversation_messages[-8:]

        # 5. Invocar al LLM
        prompt_messages = [SystemMessage(content=system_message_content)] + conversation_messages
        
        # Usamos try/except por si Azure falla a nivel de red
        try:
            response = llm.invoke(prompt_messages)
        except Exception as e:
            logger.error(f"[AZURE ERROR] Invocation failed: {e}")
            return {"messages": [AIMessage(content="Lo siento, hubo un error técnico al contactar con el modelo de IA.")]}

        # 6. Verificación de seguridad y errores
        finish_reason = response.response_metadata.get("finish_reason", "unknown")
        logger.info(f"[AZURE DEBUG] Finish Reason: {finish_reason}")

        if finish_reason == "content_filter":
            response.content = "Lo siento, la respuesta fue bloqueada por las políticas de seguridad de contenido."
        
        elif finish_reason == "length" and not response.content:
            # El caso específico que te ocurrió: length + vacío
            logger.warning("[AZURE] Finish reason 'length' with empty content detected. Possible format issue.")
            response.content = "Lo siento, la respuesta se cortó inesperadamente. Intenta simplificar la pregunta"

        elif not response.content:
            response.content = "No se generó ninguna respuesta."

        # Log
        resp_tokens = token_counter.count_text(str(response.content))
        logger.info(f"[TOKEN] Generated response: {resp_tokens} tokens")

        return {"messages": [response]}

    # --- CONSTRUCCIÓN DEL GRAFO ---
    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("retrieve", retrieve_node)
    graph_builder.add_node("generate", generate_node)
    graph_builder.set_entry_point("retrieve")
    graph_builder.add_edge("retrieve", "generate")
    graph_builder.add_edge("generate", END)

    graph = graph_builder.compile()
    return graph
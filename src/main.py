import os
import logging
import numpy as np
from config.config_loader import config
from utils.create_system import create_system
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# --- Setup ---
os.environ["AZURE_OPENAI_API_KEY"] = config("AZURE_OPENAI_API_KEY")
os.environ["GOOGLE_API_KEY"] = config("GOOGLE_API_KEY")

# --- 1. Inicializar modelo de Embeddings Globalmente ---
print("🔌 Loading Gemini Embeddings Model...")
try:
    global_embeddings_model = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=config("GOOGLE_API_KEY"),
        task_type="retrieval_query" 
    )
    print("✅ Gemini Embeddings Model Loaded (models/text-embedding-004)")
except Exception as e:
    print(f"❌ Error loading embeddings model: {e}")
    global_embeddings_model = None

def inspect_query_embedding(query_text, embeddings_model):
    """Muestra visualmente el vector numérico de entrada"""
    if embeddings_model is None:
        return None

    print(f"\n🧬 GENERATING EMBEDDING VECTOR FOR INPUT: '{query_text}'")
    
    query_vector = embeddings_model.embed_query(query_text)
    query_vector_np = np.array(query_vector)
    dim = query_vector_np.shape[0]
    
    print(f"   ┌─────────────────────────────────────────────────────────────┐")
    print(f"   │ Model: models/text-embedding-004                            │")
    print(f"   │ Dimension: {dim:<45}│")
    print(f"   ├─────────────────────────────────────────────────────────────┤")
    # Mostramos solo un preview numérico para no saturar la consola
    start_vals = ", ".join([f"{x:.4f}" for x in query_vector_np[:5]])
    end_vals = ", ".join([f"{x:.4f}" for x in query_vector_np[-5:]])
    print(f"   │ [{start_vals} ... {end_vals}] │")
    print(f"   └─────────────────────────────────────────────────────────────┘\n")
    
    return query_vector

# Initialize the RAG system
print("⚙️ Initializing RAG system...")
graph = create_system("Lengua y literatura", "Andalucía")

# --- Terminal Chat Loop ---
print("\n📖 RAG Chatbot Ready! (Full Context Display)")
print("Commands:")
print("  - Type to chat")
print("  - Type 'exit' to quit\n")

chat_state = {"messages": []}

while True:
    user_input = input("You: ")
    
    if user_input.lower() in ["exit", "quit"]:
        print("👋 Goodbye!")
        break
    
    # 1. Ver vector numérico de entrada
    if global_embeddings_model:
        inspect_query_embedding(user_input, global_embeddings_model)

    # Añadir mensaje al estado
    chat_state["messages"].append(HumanMessage(content=user_input))
    
    print("-" * 50)
    print(f"**Starting stream...**")
    print("-" * 50)

    try:
        # Usamos stream_mode="updates" para interceptar el nodo de retrieval
        for update in graph.stream(chat_state, stream_mode="updates"):
            
            for node_name, node_state in update.items():
                print(f"➡️ STEP COMPLETED: {node_name}")
                
                # --- VISUALIZACIÓN COMPLETA DE DOCUMENTOS RECUPERADOS ---
                if node_name == "retrieve":
                    docs = node_state.get("documents", [])
                    print(f"\n   🧲 [RETRIEVAL RESULT] Found {len(docs)} full documents:")
                    print(f"   {'='*80}")
                    
                    for i, doc in enumerate(docs, 1):
                        source = doc.metadata.get("source", "Unknown")
                        # ⚠️ CAMBIO: Sin slicing ([:]) y sin replace de saltos de línea
                        full_content = doc.page_content 
                        
                        print(f"   📄 DOCUMENT {i}")
                        print(f"   🔗 Source: {source}")
                        print(f"   {'-'*80}")
                        print(f"{full_content}") # Imprime el texto completo tal cual viene de la BD
                        print(f"   {'-'*80}\n")
                        
                    print(f"   {'='*80}\n")

                if "messages" in node_state and node_state["messages"]:
                    last_msg = node_state["messages"][-1]
                    if isinstance(last_msg, AIMessage):
                         print(f"   🧠 AI generating response based on the context above...")

                print("-" * 15)
        
        # Obtener respuesta final
        final_state = graph.invoke(chat_state)
        chat_state = final_state
        
        final_msg = chat_state["messages"][-1]
        if isinstance(final_msg, AIMessage):
            print("\n✅ **FINAL ANSWER**")
            print(f"AI: {final_msg.content}\n")
            
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()
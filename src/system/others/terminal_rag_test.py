"""Terminal script to manually test the RAG graph flow outside the API."""

import os
import argparse
import numpy as np
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from src.config.config_loader import config
from src.utils.create_system import create_system

def load_embeddings_model():
    """Initialize the query embeddings model for debug visualization."""
    print("Loading Gemini Embeddings Model...")
    try:
        embedding_model = config("EMBEDDING_MODEL", default="models/text-embedding-001")
        model = GoogleGenerativeAIEmbeddings(
            model=embedding_model,
            google_api_key=config("GOOGLE_API_KEY"),
            task_type="retrieval_query",
        )
        print(f"Gemini Embeddings Model loaded ({embedding_model})")
        return model
    except Exception as exc:
        print(f"Error loading embeddings model: {exc}")
        return None

def inspect_query_embedding(query_text, embeddings_model):
    """Print a compact numeric preview of the query embedding vector."""
    if embeddings_model is None:
        return None

    print(f"\nGenerating embedding vector for input: '{query_text}'")
    
    query_vector = embeddings_model.embed_query(query_text)
    query_vector_np = np.array(query_vector)
    dim = query_vector_np.shape[0]
    
    print(f"   ┌─────────────────────────────────────────────────────────────┐")
    print(f"   │ Model: models/text-embedding-001                         │")
    print(f"   │ Dimension: {dim:<45}│")
    print(f"   ├─────────────────────────────────────────────────────────────┤")
    # Mostramos solo un preview numérico para no saturar la consola
    start_vals = ", ".join([f"{x:.4f}" for x in query_vector_np[:5]])
    end_vals = ", ".join([f"{x:.4f}" for x in query_vector_np[-5:]])
    print(f"   │ [{start_vals} ... {end_vals}] │")
    print(f"   └─────────────────────────────────────────────────────────────┘\n")
    
    return query_vector

def run_terminal_chat(subject: str, community: str) -> None:
    """Run an interactive terminal loop against the compiled graph."""
    embeddings_model = load_embeddings_model()

    print("Initializing RAG system...")
    graph = create_system(subject, community)

    print("\nRAG Chatbot Ready (full context display)")
    print("Commands:")
    print("  - Type to chat")
    print("  - Type 'exit' to quit\n")

    chat_state = {"messages": []}

    while True:
        user_input = input("You: ")

        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        if embeddings_model:
            inspect_query_embedding(user_input, embeddings_model)

        chat_state["messages"].append(HumanMessage(content=user_input))

        print("-" * 50)
        print("Starting stream...")
        print("-" * 50)

        try:
            for update in graph.stream(chat_state, stream_mode="updates"):
                for node_name, node_state in update.items():
                    print(f"Step completed: {node_name}")

                    if node_name == "retrieve":
                        docs = node_state.get("documents", [])
                        print(f"\n[RETRIEVAL RESULT] Found {len(docs)} full documents:")
                        print(f"{'=' * 80}")

                        for i, doc in enumerate(docs, 1):
                            source = doc.metadata.get("source", "Unknown")
                            full_content = doc.page_content
                            print(f"Document {i}")
                            print(f"Source: {source}")
                            print(f"{'-' * 80}")
                            print(full_content)
                            print(f"{'-' * 80}\n")

                        print(f"{'=' * 80}\n")

                    if "messages" in node_state and node_state["messages"]:
                        last_msg = node_state["messages"][-1]
                        if isinstance(last_msg, AIMessage):
                            print("AI generating response based on the context above...")

                    print("-" * 15)

            final_state = graph.invoke(chat_state)
            chat_state = final_state

            final_msg = chat_state["messages"][-1]
            if isinstance(final_msg, AIMessage):
                print("\nFINAL ANSWER")
                print(f"AI: {final_msg.content}\n")

        except Exception as exc:
            print(f"\nError during execution: {exc}")
            import traceback
            traceback.print_exc()


def main() -> None:
    """Parse CLI arguments and launch the interactive RAG tester."""
    parser = argparse.ArgumentParser(description="Interactive terminal test for the RAG graph")
    parser.add_argument("--subject", default="Lengua y literatura", help="Subject to load")
    parser.add_argument("--community", default="Andalucía", help="Community to load")
    args = parser.parse_args()

    run_terminal_chat(subject=args.subject, community=args.community)


if __name__ == "__main__":
    main()
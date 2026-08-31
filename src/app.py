import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
from src.utils.redis_funcs import (
    get_cache_key,
    save_graph_config_to_cache,
    load_graph_config_from_cache,
    get_or_create_graph,
    graph_config_cache,
    graph_instance_cache,
    get_str_field_from_cache,
    save_str_field_to_cache,
    REDIS_ENABLED,
)
from src.config.config_loader import config
from src.utils.summary_func import summary_func, update_conversation_memory
from src.utils.image_read import image_read
from src.utils.token_counter import get_token_counter, log_token_usage
from qdrant_client import QdrantClient
from src.utils.create_system import get_embeddings, create_system
from contextlib import asynccontextmanager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources at startup and cleanup at shutdown."""
    # Startup
    logger.info("[STARTUP] ========== INITIALIZING APPLICATION ==========")
    
    # Load embeddings model
    logger.info("[STARTUP] Loading embeddings model...")
    try:
        get_embeddings()
        logger.info("[STARTUP] ✓ Embeddings model loaded successfully")
    except Exception as e:
        logger.error(f"[STARTUP] ✗ Failed to load embeddings model: {e}", exc_info=True)
    
    # Test Qdrant connection
    logger.info("[STARTUP] Testing Qdrant connection...")
    try:
        qdrant_host = config("QDRANT_HOST") if config("QDRANT_HOST") else "qdrant"
        qdrant_port = int(config("QDRANT_PORT")) if config("QDRANT_PORT") else 6333
        
        test_client = QdrantClient(
            host=qdrant_host,
            port=qdrant_port,
            timeout=5
        )
        collections = test_client.get_collections()
        logger.info(f"[STARTUP] ✓ Qdrant connected successfully ({len(collections.collections)} collections)")
    except Exception as e:
        logger.error(f"[STARTUP] ✗ Failed to connect to Qdrant: {e}", exc_info=True)
    
    logger.info("[STARTUP] ========== APPLICATION READY ==========")
    
    yield
    
    # Shutdown
    logger.info("[SHUTDOWN] Cleaning up resources...")
    graph_instance_cache.clear()
    graph_config_cache.clear()

# --- FastAPI Setup ---
app = FastAPI(
    title="PAUHelper",
    description="PAUHelper web API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuration & Global State ---
os.environ["AZURE_OPENAI_API_KEY"] = config("AZURE_OPENAI_API_KEY")

# --- Pydantic Models ---
class CreateSystemRequest(BaseModel):
    session_id: str = Field(..., description="Unique identifier for the session.")
    category: str = Field("Community", description="Category for the system/database.")
    subject: str = Field("General", description="Subject within the category.")

class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Unique identifier for the session.")
    query: str = Field("", description="User's text query.")
    image: Optional[str] = Field(
        None,
        description="""
        Image data. Can be:
        - HTTPS URL: 'https://example.com/image.jpg'
        - Data URL: 'data:image/jpeg;base64,/9j/4AAQ...'
        - Raw base64: '/9j/4AAQ...' (will auto-detect MIME type)
        """,
    )
    image_type: str = Field(
        "url",
        description="Type of image data: 'url' for HTTPS URLs or 'base64' for base64 data",
    )
    category: str = Field("Community", description="Category for the system/database.")
    subject: str = Field("General", description="Subject within the category.")

# --- Endpoints ---
@app.get("/", response_model=Dict[str, Any])
async def home():
    return {
        "message": "PAUHelper is running",
        "redis_enabled": REDIS_ENABLED,
        "cached_configs": len(graph_config_cache),
        "cached_instances": len(graph_instance_cache),
    }

@app.post("/create_system", response_model=Dict[str, str])
async def create_system_endpoint(data: CreateSystemRequest):
    """
    Initialize the system and EAGERLY create the graph instance.
    """
    session_id, category, subject = data.session_id, data.category, data.subject
    cache_key = get_cache_key(session_id, category, subject)
    
    logger.info(f"[CREATE_SYSTEM] ========== Request for: {cache_key} ==========")
    
    # Check if configuration already exists
    config = load_graph_config_from_cache(cache_key)
    
    if not config:
        logger.info(f"[CREATE_SYSTEM] Creating new system for {category}-{subject}")
        try:
            # FIX HERE: Pass the 'create_system' function to your utility
            # We map 'category' to 'community' and 'subject' to 'subject'
            logger.info(f"[CREATE_SYSTEM] Initializing graph...")
            
            # OPTION A: If your get_or_create_graph supports a factory function:
            # graph = get_or_create_graph(cache_key, create_system, subject=subject, community=category)
            
            # OPTION B (Clearer): Call create_system directly first, then handle caching
            graph = create_system(subject=subject, community=category)
            
            # Manually inject into your cache (assuming you have a set_graph function or similar in redis_funcs)
            # If get_or_create_graph handles the logic, you must ensure it calls the function:
            from src.utils.redis_funcs import graph_instance_cache
            graph_instance_cache[cache_key] = graph
            
            logger.info(f"[CREATE_SYSTEM] ✓ Graph initialized successfully")
            
            # Save configuration to persistent cache
            save_graph_config_to_cache(cache_key, category, subject)
            
        except Exception as e:
            # ... error handling ...
            logger.error(f"[CREATE_SYSTEM] Error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    else:
        # If config exists, ensure graph is loaded
        # Here we also need to pass create_system in case the memory cache was cleared but redis config remains
        graph = get_or_create_graph(cache_key, category, subject)

    return {
        "response": f"¡Hola! ¿Cómo puedo ayudarte a estudiar tu examen de {subject}?"
    }

@app.post("/chat", response_model=Dict[str, Optional[str]])
async def chat(data: ChatRequest):
    session_id, category, subject = data.session_id, data.category, data.subject
    cache_key = get_cache_key(session_id, category, subject)
    token_counter = get_token_counter()
    
    logger.info(f"[CHAT] ========== Request for: {cache_key} ==========")
    
    # Load graph config
    config = load_graph_config_from_cache(cache_key)
    if not config:
        logger.error(f"[CHAT] ✗ System not initialized for '{category}-{subject}'")
        raise HTTPException(
            status_code=400,
            detail=f"System not initialized for '{category}-{subject}'. Call /create_system first.",
        )
    
    # Get graph (should already be in cache from /create_system)
    try:
        logger.info(f"[CHAT] Loading graph from cache...")
        graph = get_or_create_graph(cache_key, category, subject)
        logger.info(f"[CHAT] ✓ Graph loaded successfully")
    except Exception as e:
        logger.error(f"[CHAT] ✗ Failed to initialize graph: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to initialize graph: {e}")
    
    # Build message content
    message_content = []
    intermediate_memory = ""
    
    # Handle text query
    if data.query:
        message_content.append({"type": "text", "text": data.query})
        intermediate_memory = f"Q: {data.query[:100]}"
    
    # Handle image
    if data.image and data.image_type:
        try:
            if data.image_type == "base64":
                base64_data = data.image
                mime_type = "image/jpeg"
                
                if base64_data.startswith("data:"):
                    header_part = base64_data.split(",")[0]
                    mime_part = header_part.split(";")[0].replace("data:", "")
                    if mime_part.startswith("image/"):
                        mime_type = mime_part
                    base64_data = base64_data.split(",")[1]
                    logger.info(f"[CHAT] Extracted MIME type: {mime_type}")
                else:
                    if base64_data.startswith("iVBORw0KGgo"):
                        mime_type = "image/png"
                    elif base64_data.startswith("/9j/"):
                        mime_type = "image/jpeg"
                    elif base64_data.startswith("R0lGODlh"):
                        mime_type = "image/gif"
                    elif base64_data.startswith("UklGR"):
                        mime_type = "image/webp"
                    logger.info(f"[CHAT] Detected MIME type: {mime_type}")
                
                image_url = f"data:{mime_type};base64,{base64_data}"
                
            elif data.image_type == "url":
                if not (data.image.startswith("http://") or data.image.startswith("https://")):
                    raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
                image_url = data.image
            else:
                raise HTTPException(status_code=400, detail=f"Unknown image_type: {data.image_type}")
            
            # Add image to message content
            message_content.append({"type": "image_url", "image_url": {"url": image_url, "detail": "low"}})
            
            # Extract description
            try:
                logger.info(f"[CHAT] Extracting image description...")
                img_desc = image_read(image_url)
                # 🔧 FIX: If we have both query and image, combine them
                if data.query:
                    intermediate_memory = f"Image: {img_desc[:150]}\nQ: {data.query[:100]}"
                else:
                    intermediate_memory = f"Image: {img_desc[:150]}"
                logger.info(f"[CHAT] ✓ Image description extracted")
            except Exception as e:
                logger.warning(f"[CHAT] image_read() failed: {e}")
                if data.query:
                    intermediate_memory = f"Image: [processed]\nQ: {data.query[:100]}"
                else:
                    intermediate_memory = "Image: [processed]"
                
        except Exception as e:
            logger.error(f"[CHAT] ✗ Failed to process image: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to process image: {e}")
    
    if not message_content:
        raise HTTPException(
            status_code=400,
            detail="Either query or image (with image_type) must be provided",
        )
    
    # Load memory
    memory_json = get_str_field_from_cache(cache_key)
    memory_summary = ""
    recent_turns = []
    
    if memory_json:
        try:
            memory_data = json.loads(memory_json)
            memory_summary = memory_data.get("summary", "")
            recent_turns = memory_data.get("recent", [])
            logger.info(f"[CHAT] Loaded memory: {len(recent_turns)} recent turns")
        except json.JSONDecodeError:
            logger.warning(f"[CHAT] Failed to parse memory JSON")
            pass
    
    
    # ==== BUILD CHAT STATE ====
    chat_state = {"messages": []}
    
    # Include visual context first
    if intermediate_memory:
        chat_state["messages"].append({
            "role": "system",
            "content": f"Visual context extracted: {intermediate_memory}"
        })
    
    # Include previous memory summary
    if memory_summary:
        chat_state["messages"].append({
            "role": "system",
            "content": f"Previous context summary: {memory_summary}"
        })
    
    # Include recent conversation
    for turn in recent_turns:
        chat_state["messages"].append({"role": "user", "content": turn["user"]})
        chat_state["messages"].append({"role": "assistant", "content": turn["ai"]})
    
    # Add current user message
    chat_state["messages"].append({"role": "user", "content": message_content})
    
    # ===== TOKEN COUNT =====
    initial_counts = token_counter.count_messages(chat_state["messages"])
    logger.info(f"[TOKEN COUNT] Initial input: {initial_counts['total']} tokens")
    
    try:
        logger.info(f"[CHAT] Processing request through graph...")
        response_text = None
        total_steps = 0
        
        for step in graph.stream(chat_state, stream_mode="values"):
            total_steps += 1
            step_messages = step.get("messages", [])
            
            if step_messages:
                step_dicts = [
                    {"role": msg.type, "content": msg.content}
                    for msg in step_messages if hasattr(msg, "type") and hasattr(msg, "content")
                ]
                step_counts = token_counter.count_messages(step_dicts)
            
            last_msg = step["messages"][-1]
            if last_msg.type == "ai":
                response_text = last_msg.content
        
        # 🔧 FIX: Check if response was actually generated
        if not response_text:
            logger.error(f"[CHAT] ✗ No response generated from graph")
            raise HTTPException(status_code=500, detail="No response generated")
        
        logger.info(f"[CHAT] ✓ Response generated successfully ({len(response_text)} chars)")
        
        # ===== SAVE TO MEMORY INCLUDING IMAGE DESC =====
        # 🔧 FIX: Build memory_user_content more cleanly
        memory_user_content = ""
        
        if data.image and intermediate_memory:
            # If there's an image, use the intermediate_memory (includes image desc)
            memory_user_content = intermediate_memory
        elif data.query:
            # If only text query
            memory_user_content = data.query
        else:
            logger.warning(f"[CHAT] No user content to save to memory")
        
        # Only update memory if we have both user content and AI response
        if memory_user_content and response_text:
            try:
                update_conversation_memory(cache_key, memory_user_content, response_text)
                logger.info(f"[CHAT] ✓ Memory updated")
            except Exception as mem_error:
                # Don't fail the request if memory update fails
                logger.error(f"[CHAT] ✗ Failed to update memory: {mem_error}")
        
        response_tokens = token_counter.count_text(response_text) if response_text else 0
        
        # ===== FINAL TOKEN SUMMARY =====
        logger.info(f"[TOKEN COUNT] ========== REQUEST SUMMARY ==========")
        logger.info(f"[TOKEN COUNT] Initial input: {initial_counts['total']} tokens")
        logger.info(f"[TOKEN COUNT] Total steps: {total_steps}")
        logger.info(f"[TOKEN COUNT] Response: {response_tokens} tokens")
        logger.info(f"[TOKEN COUNT] =====================================")
        
        return {"response": response_text}
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"[CHAT] ✗ Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat error: {e}")
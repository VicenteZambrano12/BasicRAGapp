"""Chat endpoint with text/image handling, memory loading, and graph execution."""

import json
import logging
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException

from src.api.DataClasses.chat_request import ChatRequest
from src.utils.image_read import image_read
from src.utils.redis_funcs import (
    get_cache_key,
    get_or_create_graph,
    get_str_field_from_cache,
    load_graph_config_from_cache,
)
from src.utils.summary_func import update_conversation_memory
from src.utils.token_counter import get_token_counter


logger = logging.getLogger(__name__)
router = APIRouter()


def _build_image_url(image_data: str, image_type: str) -> str:
    """Normalize image input into a URL accepted by the chat model."""

    if image_type == "base64":
        base64_data = image_data
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

        return f"data:{mime_type};base64,{base64_data}"

    if image_type == "url":
        if not (image_data.startswith("http://") or image_data.startswith("https://")):
            raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
        return image_data

    raise HTTPException(status_code=400, detail=f"Unknown image_type: {image_type}")


@router.post("/chat", response_model=Dict[str, Optional[str]])
async def chat(data: ChatRequest):
    """Process a chat turn and return the assistant response text."""

    session_id, category, subject = data.session_id, data.category, data.subject
    cache_key = get_cache_key(session_id, category, subject)
    token_counter = get_token_counter()

    logger.info(f"[CHAT] ========== Request for: {cache_key} ==========")

    cached_config = load_graph_config_from_cache(cache_key)
    if not cached_config:
        logger.error(f"[CHAT] System not initialized for '{category}-{subject}'")
        raise HTTPException(
            status_code=400,
            detail=f"System not initialized for '{category}-{subject}'. Call /create_system first.",
        )

    try:
        logger.info("[CHAT] Loading graph from cache...")
        graph = get_or_create_graph(cache_key, category, subject)
        logger.info("[CHAT] Graph loaded successfully")
    except Exception as exc:
        logger.error(f"[CHAT] Failed to initialize graph: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to initialize graph: {exc}")

    message_content = []
    intermediate_memory = ""

    if data.query:
        message_content.append({"type": "text", "text": data.query})
        intermediate_memory = f"Q: {data.query[:100]}"

    if data.image and data.image_type:
        try:
            image_url = _build_image_url(data.image, data.image_type)
            message_content.append({"type": "image_url", "image_url": {"url": image_url, "detail": "low"}})

            try:
                logger.info("[CHAT] Extracting image description...")
                img_desc = image_read(image_url)
                if data.query:
                    intermediate_memory = f"Image: {img_desc[:150]}\nQ: {data.query[:100]}"
                else:
                    intermediate_memory = f"Image: {img_desc[:150]}"
                logger.info("[CHAT] Image description extracted")
            except Exception as exc:
                logger.warning(f"[CHAT] image_read() failed: {exc}")
                if data.query:
                    intermediate_memory = f"Image: [processed]\nQ: {data.query[:100]}"
                else:
                    intermediate_memory = "Image: [processed]"

        except Exception as exc:
            logger.error(f"[CHAT] Failed to process image: {exc}")
            raise HTTPException(status_code=400, detail=f"Failed to process image: {exc}")

    if not message_content:
        raise HTTPException(
            status_code=400,
            detail="Either query or image (with image_type) must be provided",
        )

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
            logger.warning("[CHAT] Failed to parse memory JSON")

    chat_state = {"messages": []}

    if intermediate_memory:
        chat_state["messages"].append(
            {"role": "system", "content": f"Visual context extracted: {intermediate_memory}"}
        )

    if memory_summary:
        chat_state["messages"].append(
            {"role": "system", "content": f"Previous context summary: {memory_summary}"}
        )

    for turn in recent_turns:
        chat_state["messages"].append({"role": "user", "content": turn["user"]})
        chat_state["messages"].append({"role": "assistant", "content": turn["ai"]})

    chat_state["messages"].append({"role": "user", "content": message_content})

    initial_counts = token_counter.count_messages(chat_state["messages"])
    logger.info(f"[TOKEN COUNT] Initial input: {initial_counts['total']} tokens")

    try:
        logger.info("[CHAT] Processing request through graph...")
        response_text = None
        total_steps = 0

        for step in graph.stream(chat_state, stream_mode="values"):
            total_steps += 1
            last_msg = step["messages"][-1]
            if last_msg.type == "ai":
                response_text = last_msg.content

        if not response_text:
            logger.error("[CHAT] No response generated from graph")
            raise HTTPException(status_code=500, detail="No response generated")

        logger.info(f"[CHAT] Response generated successfully ({len(response_text)} chars)")

        memory_user_content = ""
        if data.image and intermediate_memory:
            memory_user_content = intermediate_memory
        elif data.query:
            memory_user_content = data.query

        if memory_user_content and response_text:
            try:
                update_conversation_memory(cache_key, memory_user_content, response_text)
                logger.info("[CHAT] Memory updated")
            except Exception as mem_error:
                logger.error(f"[CHAT] Failed to update memory: {mem_error}")

        response_tokens = token_counter.count_text(response_text) if response_text else 0

        logger.info("[TOKEN COUNT] ========== REQUEST SUMMARY ==========")
        logger.info(f"[TOKEN COUNT] Initial input: {initial_counts['total']} tokens")
        logger.info(f"[TOKEN COUNT] Total steps: {total_steps}")
        logger.info(f"[TOKEN COUNT] Response: {response_tokens} tokens")
        logger.info("[TOKEN COUNT] =====================================")

        return {"response": response_text}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[CHAT] Error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat error: {exc}")

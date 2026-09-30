"""Root chat orchestration function used by the chat endpoint."""

import logging
from typing import Any, Dict

from fastapi import HTTPException

from src.api.DataClasses.chat_request import ChatRequest
from src.i18n import get_language_instruction
from src.system.chat.build_chat_state import build_chat_state
from src.system.chat.build_image_url import build_image_url
from src.system.chat.build_memory_user_content import build_memory_user_content
from src.system.chat.build_message_content import build_message_content
from src.system.chat.build_sources import build_sources
from src.system.chat.ensure_graph_available import ensure_graph_available
from src.system.chat.load_memory_context import load_memory_context
from src.system.chat.run_graph_stream import run_graph_stream
from src.system.chat.update_memory_and_log import update_memory_and_log
from src.system.others.cache_key import build_cache_key
from src.utils.chat import image_read
from src.utils.observability import get_token_counter


logger = logging.getLogger(__name__)


def execute_chat(data: ChatRequest) -> Dict[str, Any]:
    """Process one chat turn and return the assistant response payload."""
    session_id = data.session_id
    category = data.category
    subject = data.subject
    cache_key = build_cache_key(session_id, category, subject)
    token_counter = get_token_counter()

    logger.info(
        "Chat turn started",
        extra={
            "event": "chat_started",
            "session_id": session_id,
            "category": category,
            "subject": subject,
            "has_image": bool(data.image and data.image_type),
        },
    )

    graph = ensure_graph_available(cache_key, category, subject)

    message_content, intermediate_memory = build_message_content(data.query)

    if data.image and data.image_type:
        try:
            image_url = build_image_url(data.image, data.image_type)
            message_content.append(
                {"type": "image_url", "image_url": {"url": image_url, "detail": "low"}}
            )

            try:
                img_desc = image_read(image_url)
                if data.query:
                    intermediate_memory = f"Image: {img_desc[:150]}\nQ: {data.query[:100]}"
                else:
                    intermediate_memory = f"Image: {img_desc[:150]}"
                logger.info(
                    "Image description extracted",
                    extra={"event": "image_description_extracted", "session_id": session_id},
                )
            except Exception:
                logger.warning(
                    "Image description extraction failed, falling back to placeholder",
                    exc_info=True,
                    extra={"event": "image_description_failed", "session_id": session_id},
                )
                if data.query:
                    intermediate_memory = f"Image: [processed]\nQ: {data.query[:100]}"
                else:
                    intermediate_memory = "Image: [processed]"

        except HTTPException:
            raise
        except Exception as exc:
            logger.error(
                "Failed to process uploaded image",
                exc_info=True,
                extra={
                    "event": "image_processing_failed",
                    "session_id": session_id,
                    "image_type": data.image_type,
                },
            )
            raise HTTPException(status_code=400, detail=f"Failed to process image: {exc}")

    if not message_content:
        raise HTTPException(
            status_code=400,
            detail="Either query or image (with image_type) must be provided",
        )

    memory_summary, recent_turns = load_memory_context(cache_key)

    chat_state = build_chat_state(
        message_content=message_content,
        intermediate_memory=intermediate_memory,
        memory_summary=memory_summary,
        recent_turns=recent_turns,
        language_instruction=get_language_instruction(data.language),
    )

    initial_counts = token_counter.count_messages(chat_state["messages"])
    logger.debug(
        "Chat input token count",
        extra={
            "event": "input_tokens_counted",
            "input_tokens": initial_counts["total"],
            "session_id": session_id,
        },
    )

    try:
        response_text, total_steps, retrieved_documents = run_graph_stream(graph, chat_state)
        sources = build_sources(retrieved_documents)

        memory_user_content = build_memory_user_content(
            query=data.query,
            has_image=bool(data.image),
            intermediate_memory=intermediate_memory,
        )

        update_memory_and_log(
            token_counter=token_counter,
            cache_key=cache_key,
            memory_user_content=memory_user_content,
            response_text=response_text,
            initial_input_tokens=initial_counts["total"],
            total_steps=total_steps,
        )

        return {"response": response_text, "sources": sources}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Chat turn failed",
            exc_info=True,
            extra={
                "event": "chat_failed",
                "session_id": session_id,
                "category": category,
                "subject": subject,
            },
        )
        raise HTTPException(status_code=500, detail=f"Chat error: {exc}")

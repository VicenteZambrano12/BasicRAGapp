import requests
from src.config.config_loader import config
import json
from src.utils.redis_funcs import save_str_field_to_cache, get_str_field_from_cache
import logging

logger = logging.getLogger(__name__)


def summary_func(messages: str) -> str:
    """
    Summarize conversation history using Azure OpenAI.
    
    Args:
        messages: Conversation history as string
    
    Returns:
        Summary string (max 50 tokens)
    """
    endpoint = config("AZURE_OPENAI_ENDPOINT")
    api_key = config("AZURE_OPENAI_API_KEY")
    deployment_name = config("DEPLOYMENT_NAME")
    api_version = config("API_version")
    
    url = f"{endpoint}openai/deployments/{deployment_name}/chat/completions?api-version={api_version}"

    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }

    # Truncate to last 800 chars only
    if len(messages) > 800:
        messages = "..." + messages[-800:]
    
    data = {
        "messages": [
            {
                "role": "system", 
                "content": "Summarize: topic + last question. Max 50 tokens."
            },
            {
                "role": "user", 
                "content": messages
            }
        ],
        "max_tokens": 50,
        "temperature": 0
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            logger.warning(f"Summary API failed: {response.status_code}")
            return ""
    except Exception as e:
        logger.error(f"Summary function error: {e}")
        return ""


def update_conversation_memory(cache_key: str, user_msg: str, ai_msg: str, max_turns: int = 6):
    """
    Maintain rolling memory: summarize older messages, keep recent ones.
    Avoid duplicates or empty AI responses.
    
    Args:
        cache_key: Redis cache key
        user_msg: User's message (can include image descriptions)
        ai_msg: AI's response
        max_turns: Maximum number of recent turns to keep (default 6)
    """
    try:
        # Load existing memory
        memory_json = get_str_field_from_cache(cache_key)
        
        if memory_json:
            try:
                memory_data = json.loads(memory_json)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse memory JSON for {cache_key}, resetting")
                memory_data = {"summary": "", "recent": []}
        else:
            memory_data = {"summary": "", "recent": []}

        # Ensure structure exists
        if "recent" not in memory_data:
            memory_data["recent"] = []
        if "summary" not in memory_data:
            memory_data["summary"] = ""

        # 🧹 Filter out incomplete turns (missing user or ai)
        memory_data["recent"] = [
            t for t in memory_data["recent"] 
            if t.get("user") and t.get("ai")
        ]

        # Clean input
        user_msg_clean = user_msg.strip() if user_msg else ""
        ai_msg_clean = ai_msg.strip() if ai_msg else ""
        
        if not user_msg_clean or not ai_msg_clean:
            logger.warning(f"Skipping memory update - empty user or AI message")
            return

        # 🔍 Check for exact duplicate (prevent re-adding the same turn)
        if memory_data["recent"]:
            last_turn = memory_data["recent"][-1]
            if (last_turn.get("user") == user_msg_clean and 
                last_turn.get("ai") == ai_msg_clean):
                logger.info(f"Duplicate turn detected, skipping memory update")
                return
            
            # Also check if just the user message matches (incomplete save from previous request)
            if last_turn.get("user") == user_msg_clean and not last_turn.get("ai"):
                logger.info(f"Removing incomplete turn before adding new one")
                memory_data["recent"].pop()

        # Add the latest interaction
        new_turn = {"user": user_msg_clean, "ai": ai_msg_clean}
        memory_data["recent"].append(new_turn)
        
        logger.info(f"Added new turn to memory (total turns: {len(memory_data['recent'])})")

        # If too many turns, summarize older ones
        if len(memory_data["recent"]) > max_turns:
            old_turns = memory_data["recent"][:-max_turns]
            old_text = "\n".join(
                [f"User: {t['user'][:100]}\nAssistant: {t['ai'][:100]}" for t in old_turns]
            )
            
            # Combine old summary with old turns
            text_to_summarize = memory_data["summary"]
            if text_to_summarize:
                text_to_summarize += "\n" + old_text
            else:
                text_to_summarize = old_text
            
            # Generate new summary
            new_summary = summary_func(text_to_summarize)
            if new_summary:
                memory_data["summary"] = new_summary
                logger.info(f"Generated new summary for old turns")
            
            # Keep only recent turns
            memory_data["recent"] = memory_data["recent"][-max_turns:]
            logger.info(f"Trimmed memory to {max_turns} recent turns")

        # Save back to cache with UTF-8 encoding
        success = save_str_field_to_cache(
            cache_key, 
            json.dumps(memory_data, ensure_ascii=False)
        )
        
        if success:
            logger.info(f"✓ Memory updated successfully for {cache_key}")
        else:
            logger.warning(f"⚠️ Failed to save memory for {cache_key}")
            
    except Exception as e:
        logger.error(f"❌ Error updating conversation memory: {e}", exc_info=True)


def get_conversation_context(cache_key: str) -> tuple:
    """
    Retrieve conversation context from memory.
    
    Args:
        cache_key: Redis cache key
    
    Returns:
        Tuple of (summary: str, recent_turns: list)
    """
    try:
        memory_json = get_str_field_from_cache(cache_key)
        
        if not memory_json:
            return "", []
        
        memory_data = json.loads(memory_json)
        summary = memory_data.get("summary", "")
        recent_turns = memory_data.get("recent", [])
        
        return summary, recent_turns
        
    except Exception as e:
        logger.error(f"❌ Error retrieving conversation context: {e}", exc_info=True)
        return "", []


def clear_conversation_memory(cache_key: str) -> bool:
    """
    Clear all conversation memory for a session.
    
    Args:
        cache_key: Redis cache key
    
    Returns:
        True if successful
    """
    try:
        empty_memory = json.dumps({"summary": "", "recent": []})
        success = save_str_field_to_cache(cache_key, empty_memory)
        
        if success:
            logger.info(f"✓ Cleared memory for {cache_key}")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Error clearing memory: {e}", exc_info=True)
        return False
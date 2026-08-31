# src/utils/token_counter.py

import tiktoken
from typing import List, Dict, Any, Union
import logging

logger = logging.getLogger(__name__)


class TokenCounter:
    """
    Token counter for tracking context usage in requests.
    Uses tiktoken for accurate GPT-4 token counting.
    """
    
    def __init__(self, model_name: str = "gpt-4"):
        """
        Initialize token counter.
        
        Args:
            model_name: Model name for encoding (default: gpt-4)
        """
        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            # Fallback to cl100k_base encoding (used by gpt-4, gpt-3.5-turbo)
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_text(self, text: str) -> int:
        """Count tokens in a text string."""
        if not text:
            return 0
        return len(self.encoding.encode(text))
    
    def count_messages(self, messages: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Count tokens in a list of messages.
        
        Returns:
            Dict with 'total', 'by_role', and 'by_message' counts
        """
        total_tokens = 0
        by_role = {}
        by_message = []
        
        # Overhead tokens per message (role, formatting, etc.)
        tokens_per_message = 4  # Approximate overhead
        
        for idx, message in enumerate(messages):
            message_tokens = tokens_per_message
            role = message.get("role", "unknown")
            content = message.get("content", "")
            
            # Count role tokens
            message_tokens += self.count_text(role)
            
            # Handle different content types
            if isinstance(content, str):
                message_tokens += self.count_text(content)
            elif isinstance(content, list):
                # Multi-modal content (text + images)
                for item in content:
                    if item.get("type") == "text":
                        message_tokens += self.count_text(item.get("text", ""))
                    elif item.get("type") == "image_url":
                        # Image tokens depend on detail level
                        detail = item.get("image_url", {}).get("detail", "auto")
                        if detail == "low":
                            message_tokens += 85  # Low detail images
                        elif detail == "high":
                            message_tokens += 765  # High detail images (approximate)
                        else:
                            message_tokens += 85  # Default to low
            
            total_tokens += message_tokens
            
            # Track by role
            by_role[role] = by_role.get(role, 0) + message_tokens
            
            # Track by message
            by_message.append({
                "index": idx,
                "role": role,
                "tokens": message_tokens,
                "content_preview": str(content)[:50] + "..." if len(str(content)) > 50 else str(content)
            })
        
        return {
            "total": total_tokens,
            "by_role": by_role,
            "by_message": by_message
        }
    
    def count_graph_state(self, state: Dict[str, Any]) -> Dict[str, int]:
        """
        Count tokens in a LangGraph state.
        
        Args:
            state: Graph state with 'messages' key
            
        Returns:
            Token count breakdown
        """
        messages = state.get("messages", [])
        
        # Convert LangChain message objects to dict format
        message_dicts = []
        for msg in messages:
            if hasattr(msg, "type") and hasattr(msg, "content"):
                message_dicts.append({
                    "role": msg.type,
                    "content": msg.content
                })
            elif isinstance(msg, dict):
                message_dicts.append(msg)
        
        return self.count_messages(message_dicts)
    
    def estimate_response_tokens(self, max_tokens: int = 1000) -> int:
        """Estimate response tokens based on max_tokens setting."""
        return max_tokens
    
    def calculate_total_request(
        self, 
        messages: List[Dict[str, Any]], 
        system_prompt: str = "",
        retrieved_docs: str = "",
        max_response_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Calculate total tokens for a complete request.
        
        Returns:
            Detailed breakdown of token usage
        """
        message_counts = self.count_messages(messages)
        system_tokens = self.count_text(system_prompt)
        docs_tokens = self.count_text(retrieved_docs)
        
        # Function/tool definition overhead (approximate)
        function_tokens = 37  # From your error message
        
        total_input = (
            message_counts["total"] + 
            system_tokens + 
            docs_tokens + 
            function_tokens
        )
        
        total_with_response = total_input + max_response_tokens
        
        return {
            "input_tokens": {
                "messages": message_counts["total"],
                "system_prompt": system_tokens,
                "retrieved_docs": docs_tokens,
                "functions": function_tokens,
                "total": total_input
            },
            "estimated_response_tokens": max_response_tokens,
            "estimated_total": total_with_response,
            "model_limit": 128000,
            "remaining": 128000 - total_with_response,
            "usage_percentage": round((total_with_response / 128000) * 100, 2),
            "breakdown": message_counts
        }


# Global counter instance
_token_counter = None

def get_token_counter() -> TokenCounter:
    """Get or create global token counter instance."""
    global _token_counter
    if _token_counter is None:
        _token_counter = TokenCounter()
    return _token_counter


def log_token_usage(
    logger_instance: logging.Logger,
    messages: List[Dict[str, Any]],
    system_prompt: str = "",
    retrieved_docs: str = "",
    max_response_tokens: int = 1000,
    prefix: str = "[TOKEN COUNT]"
):
    """
    Log detailed token usage.
    
    Args:
        logger_instance: Logger to use
        messages: List of messages
        system_prompt: System prompt text
        retrieved_docs: Retrieved document text
        max_response_tokens: Max tokens for response
        prefix: Log message prefix
    """
    counter = get_token_counter()
    stats = counter.calculate_total_request(
        messages=messages,
        system_prompt=system_prompt,
        retrieved_docs=retrieved_docs,
        max_response_tokens=max_response_tokens
    )
    
    logger_instance.info(f"{prefix} Input Breakdown:")
    logger_instance.info(f"  Messages: {stats['input_tokens']['messages']} tokens")
    logger_instance.info(f"  System Prompt: {stats['input_tokens']['system_prompt']} tokens")
    logger_instance.info(f"  Retrieved Docs: {stats['input_tokens']['retrieved_docs']} tokens")
    logger_instance.info(f"  Functions: {stats['input_tokens']['functions']} tokens")
    logger_instance.info(f"  Total Input: {stats['input_tokens']['total']} tokens")
    logger_instance.info(f"{prefix} Estimated Response: {stats['estimated_response_tokens']} tokens")
    logger_instance.info(f"{prefix} Estimated Total: {stats['estimated_total']} tokens ({stats['usage_percentage']}% of limit)")
    logger_instance.info(f"{prefix} Remaining: {stats['remaining']} tokens")
    
    if stats['estimated_total'] > 128000:
        logger_instance.error(f"{prefix} ⚠️  EXCEEDS MODEL LIMIT!")
    elif stats['usage_percentage'] > 80:
        logger_instance.warning(f"{prefix} ⚠️  High token usage (>80%)")
    
    return stats
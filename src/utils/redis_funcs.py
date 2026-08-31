from src.config.config_loader import config
import redis
import os
from src.utils.create_system import create_system
import logging
from typing import Optional, Dict, Any, List
import json


graph_config_cache: Dict[str, Dict[str, str]] = {}

# Store actual graph instances in memory (not serializable)
graph_instance_cache: Dict[str, Any] = {}
# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Redis Setup ---
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_ENABLED = False

try:
    r = redis.Redis(
        host=REDIS_HOST, 
        port=REDIS_PORT, 
        db=0, 
        socket_timeout=5,
        socket_connect_timeout=5,
        decode_responses=True,  # Changed to True for automatic UTF-8 decoding
        encoding='utf-8',       # Explicit UTF-8 encoding
        encoding_errors='strict'
    )
    r.ping()
    REDIS_ENABLED = True
except Exception as e:
    logger.warning(f"⚠️ Redis connection failed: {e}. Using in-memory cache only.")
    r = None

# --- Helper Functions ---
def normalize_string(s: str) -> str:
    """Normalize string by removing accents and converting to ASCII-safe format."""
    import unicodedata
    # Decompose unicode characters (é -> e + accent)
    nfd = unicodedata.normalize('NFD', s)
    # Filter out accent marks (category Mn = Nonspacing_Mark)
    ascii_str = ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
    # Replace spaces with underscores and convert to lowercase for consistency
    return ascii_str.replace(' ', '_').lower()

def get_cache_key(session_id: str, category: str, subject: str) -> str:
    """Generate a unique cache key using URL-safe separator and normalized strings."""
    # Normalize to avoid encoding issues with accents
    norm_category = normalize_string(category)
    norm_subject = normalize_string(subject)
    return f"{session_id}::{norm_category}::{norm_subject}"

def get_memory_key(session_id: str, category: str, subject: str) -> str:
    """Generate a separate key for memory storage to avoid type conflicts."""
    return f"{session_id}::{category}::{subject}::memory"

def save_graph_config_to_cache(key: str, category: str, subject: str) -> bool:
    """Save graph configuration (not the graph object itself) to Redis."""
    success = False
    config_data = {"category": category, "subject": subject}
    
    logger.info(f"🔄 Saving graph config to cache: {key}")
    
    # Try Redis first
    if REDIS_ENABLED and r:
        try:
            # Store as JSON string
            config_json = json.dumps(config_data)
            r.set(key, config_json, ex=2*60*60)  # 2 hour expiry
            success = True
        except Exception as e:
            logger.error(f"❌ Redis save error for {key}: {e}")
    else:
        logger.warning(f"⚠️ Redis not available, using in-memory only")
    
    # Always save to in-memory cache as backup
    graph_config_cache[key] = config_data
    success = True
    
    return success

def load_graph_config_from_cache(key: str) -> Optional[Dict[str, str]]:
    """Load graph configuration from Redis with in-memory fallback."""
    
    # Try Redis first
    if REDIS_ENABLED and r:
        try:
            cached = r.get(key)
            if cached:
                config_data = json.loads(cached)
                # Update in-memory cache
                graph_config_cache[key] = config_data
                return config_data
        except Exception as e:
            logger.error(f"❌ Redis read error for {key}: {e}")
    
    # Fallback to in-memory
    if key in graph_config_cache:
        return graph_config_cache[key]
    
    logger.info(f"ℹ️ Config not found in any cache: {key}")
    return None

def get_or_create_graph(key: str, category: str, subject: str):
    """Get graph from instance cache or create new one."""
    
    # Check if graph instance already exists in memory
    if key in graph_instance_cache:
        return graph_instance_cache[key]
    
    # Create new graph
    logger.info(f"🔄 Creating new graph instance: {key}")
    graph = create_system(community=category, subject=subject)
    
    # Cache the instance in memory
    graph_instance_cache[key] = graph
    
    return graph

def get_str_field_from_cache(key: str) -> Optional[str]:
    """Load a string field from Redis with in-memory fallback."""
    
    # Use a separate key for memory to avoid type conflicts
    memory_key = f"{key}::memory"
    
    # Try Redis first
    if REDIS_ENABLED and r:
        try:
            # GET now returns string directly (decode_responses=True)
            cached = r.get(memory_key)
            if cached:
                # Update in-memory cache
                if key not in graph_config_cache:
                    graph_config_cache[key] = {}
                graph_config_cache[key]["memory"] = cached
                return cached
        except Exception as e:
            logger.error(f"❌ Redis read error for {memory_key}: {e}")

    # Fallback to in-memory
    if key in graph_config_cache and "memory" in graph_config_cache[key]:
        return graph_config_cache[key]["memory"]

    logger.info(f"ℹ️ Field 'memory' not found in any cache: {memory_key}")
    return None

def save_str_field_to_cache(key: str, field_value: str) -> bool:
    """Save a string field to Redis with in-memory backup."""
    success = False
    
    # Use a separate key for memory to avoid type conflicts
    memory_key = f"{key}::memory"
    
    logger.info(f"🔄 Saving string field 'memory' to cache: {memory_key}")
    
    # Try Redis first
    if REDIS_ENABLED and r:
        try:
            # Use SET for string values (not HSET)
            r.set(memory_key, field_value, ex=2*60*60)  # 2 hour expiry
            success = True
        except Exception as e:
            logger.error(f"❌ Redis save error for {memory_key}: {e}")
    else:
        logger.warning(f"⚠️ Redis not available, using in-memory only")
    
    # Always save to in-memory cache as backup
    if key not in graph_config_cache:
        graph_config_cache[key] = {}
    graph_config_cache[key]["memory"] = field_value
    success = True
    
    return success
import os
from pathlib import Path
from decouple import Config as DecoupleConfig, RepositoryEnv

class Config:
    """
    Unified configuration loader.
    - Uses .env file locally if it exists.
    - Uses environment variables in Cloud Run (or production).
    - Callable interface: config("KEY")
    """

    def __init__(self):
        # Try to load .env file from root
        env_path = Path(__file__).resolve().parents[2] / ".env"  # two levels up from src/config

        if env_path.exists():
            # Local development: use .env
            self._config = DecoupleConfig(RepositoryEnv(str(env_path)))
        else:
            # Cloud Run / production: use os.environ
            self._config = None  # fallback to environment variables

    def __call__(self, key: str, default=None):
        # Try Decouple first
        if self._config:
            try:
                return self._config(key)
            except Exception:
                if default is not None:
                    return default
                raise RuntimeError(f"Environment variable '{key}' not set in .env")
        # Fallback to os.environ
        value = os.environ.get(key, default)
        if value is None:
            raise RuntimeError(f"Environment variable '{key}' not set")
        return value

# Instantiate a global config object
config = Config()

prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts')
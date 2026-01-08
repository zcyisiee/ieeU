import json
import os
from typing import Optional
from .constants import (
    DEFAULT_CONFIG_DIR,
    DEFAULT_CONFIG_FILE,
    DEFAULT_TIMEOUT,
    DEFAULT_RETRIES,
    DEFAULT_MAX_CONCURRENCY
)


class Config:
    def __init__(self):
        self.endpoint: Optional[str] = None
        self.key: Optional[str] = None
        self.model_name: Optional[str] = None
        self.timeout: int = DEFAULT_TIMEOUT
        self.retries: int = DEFAULT_RETRIES
        self.max_concurrency: int = DEFAULT_MAX_CONCURRENCY
    
    @classmethod
    def load(cls) -> 'Config':
        config = cls()
        
        config_path = os.path.join(
            DEFAULT_CONFIG_DIR, 
            DEFAULT_CONFIG_FILE
        )
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                config.endpoint = data.get('endpoint')
                config.key = data.get('key')
                config.model_name = data.get('modelName')
                config.timeout = data.get('timeout', DEFAULT_TIMEOUT)
                config.retries = data.get('retries', DEFAULT_RETRIES)
                config.max_concurrency = data.get(
                    'maxConcurrency', 
                    DEFAULT_MAX_CONCURRENCY
                )
        
        config._apply_env_overrides()
        
        return config
    
    def _apply_env_overrides(self):
        if 'IEEU_ENDPOINT' in os.environ:
            self.endpoint = os.environ['IEEU_ENDPOINT']
        if 'IEEU_KEY' in os.environ:
            self.key = os.environ['IEEU_KEY']
        if 'IEEU_MODEL' in os.environ:
            self.model_name = os.environ['IEEU_MODEL']
    
    def validate(self) -> bool:
        if not self.endpoint:
            raise ValueError("Missing required config: endpoint")
        if not self.key:
            raise ValueError("Missing required config: key")
        if not self.model_name:
            raise ValueError("Missing required config: modelName")
        return True
    
    def __repr__(self):
        return (
            f"Config(endpoint={self.endpoint}, "
            f"model_name={self.model_name}, "
            f"timeout={self.timeout}, "
            f"retries={self.retries}, "
            f"max_concurrency={self.max_concurrency})"
        )

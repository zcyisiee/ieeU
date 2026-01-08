import base64
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Optional
import requests

from .config import Config
from .constants import PROMPT_TEMPLATE
from .logger import Logger


class VLMClient:
    def __init__(self, config: Config, logger: Logger):
        self.config = config
        self.logger = logger
    
    def _encode_image(self, image_path: str) -> Optional[str]:
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
                return base64.b64encode(image_data).decode('utf-8')
        except Exception as e:
            self.logger.log_error(image_path, f"Failed to read image: {e}")
            return None
    
    def _call_api(self, image_path: str, base64_image: str) -> Optional[str]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.key}"
        }
        
        payload = {
            "model": self.config.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": PROMPT_TEMPLATE
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 4096
        }
        
        for attempt in range(self.config.retries):
            try:
                response = requests.post(
                    str(self.config.endpoint),
                    headers=headers,
                    json=payload,
                    timeout=self.config.timeout
                )
                
                response.raise_for_status()
                
                data = response.json()
                content = data['choices'][0]['message']['content']
                
                return content
            
            except requests.exceptions.Timeout:
                if attempt < self.config.retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise
            
            except requests.exceptions.RequestException as e:
                if attempt < self.config.retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise
        
        return None
    
    def _parse_response(self, response_text: str) -> Optional[str]:
        pattern = r'```figure\n([\s\S]*?)\n```'
        match = re.search(pattern, response_text)
        
        if match:
            return match.group(1).strip()
        
        return response_text.strip() if response_text else None
    
    def describe_image(self, image_path: str) -> Optional[str]:
        base64_image = self._encode_image(image_path)
        
        if not base64_image:
            return None
        
        try:
            response = self._call_api(image_path, base64_image)
            
            if response:
                return self._parse_response(response)
            
            return None
        
        except Exception as e:
            self.logger.log_error(image_path, str(e))
            return None
    
    def describe_images_batch(
        self, 
        image_paths: Dict[str, str]
    ) -> Dict[str, str]:
        results = {}
        total = len(image_paths)
        current = 0
        
        items = list(image_paths.items())
        
        with ThreadPoolExecutor(
            max_workers=self.config.max_concurrency
        ) as executor:
            futures = {
                executor.submit(
                    self.describe_image, 
                    full_path
                ): (rel_path, full_path) 
                for rel_path, full_path in items
            }
            
            for future in as_completed(futures):
                rel_path, full_path = futures[future]
                current += 1
                
                try:
                    description = future.result()
                    
                    if description:
                        results[rel_path] = description
                        self.logger.log_progress(
                            current, 
                            total, 
                            rel_path, 
                            True
                        )
                    else:
                        self.logger.log_progress(
                            current, 
                            total, 
                            rel_path, 
                            False
                        )
                
                except Exception as e:
                    self.logger.log_progress(
                        current, 
                        total, 
                        rel_path, 
                        False
                    )
                    self.logger.log_error(rel_path, str(e))
        
        return results

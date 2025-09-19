from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
import time
import logging

logger = logging.getLogger(__name__)

@dataclass
class APIResponse:
    platform: str
    model: str
    prompt: str
    response: str
    usage: Dict[str, int]
    latency: float
    success: bool
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

class BaseAPIClient(ABC):
    def __init__(self, platform_config):
        self.config = platform_config
        self.platform_name = platform_config.name
    
    @abstractmethod
    def call_api(self, prompt: str, model_config) -> APIResponse:
        pass
    
    def test_model(self, prompt: str, model_config) -> APIResponse:
        start_time = time.time()
        try:
            response = self.call_api(prompt, model_config)
            response.latency = time.time() - start_time
            return response
        except Exception as e:
            logger.error(f"调用{self.platform_name} {model_config.name}失败: {str(e)}")
            return APIResponse(
                platform=self.platform_name,
                model=model_config.name,
                prompt=prompt,
                response="",
                usage={},
                latency=time.time() - start_time,
                success=False,
                error=str(e)
            )
    
    def format_messages(self, prompt: str) -> list:
        return [
            {"role": "user", "content": prompt}
        ]
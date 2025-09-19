from anthropic import Anthropic
from .base_client import BaseAPIClient, APIResponse
import logging

logger = logging.getLogger(__name__)

class AnthropicClient(BaseAPIClient):
    def __init__(self, platform_config):
        super().__init__(platform_config)
        self.client = Anthropic(
            api_key=platform_config.api_key
        )
    
    def call_api(self, prompt: str, model_config) -> APIResponse:
        try:
            message = self.client.messages.create(
                model=model_config.name,
                max_tokens=model_config.max_tokens,
                temperature=model_config.temperature,
                messages=self.format_messages(prompt)
            )
            
            response_text = message.content[0].text
            usage = {
                "prompt_tokens": message.usage.input_tokens,
                "completion_tokens": message.usage.output_tokens,
                "total_tokens": message.usage.input_tokens + message.usage.output_tokens
            }
            
            return APIResponse(
                platform=self.platform_name,
                model=model_config.name,
                prompt=prompt,
                response=response_text,
                usage=usage,
                latency=0,
                success=True,
                raw_response=message.model_dump()
            )
        except Exception as e:
            logger.error(f"Anthropic API调用失败: {str(e)}")
            raise
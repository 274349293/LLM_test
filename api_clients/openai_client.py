from openai import OpenAI
from .base_client import BaseAPIClient, APIResponse
import logging

logger = logging.getLogger(__name__)

class OpenAIClient(BaseAPIClient):
    def __init__(self, platform_config):
        super().__init__(platform_config)
        self.client = OpenAI(
            api_key=platform_config.api_key,
            base_url=platform_config.base_url if platform_config.base_url else None
        )
    
    def call_api(self, prompt: str, model_config) -> APIResponse:
        try:
            completion = self.client.chat.completions.create(
                model=model_config.name,
                messages=self.format_messages(prompt),
                max_tokens=model_config.max_tokens,
                temperature=model_config.temperature,
                top_p=model_config.top_p if model_config.top_p else 1.0,
                frequency_penalty=model_config.frequency_penalty if model_config.frequency_penalty else 0,
                presence_penalty=model_config.presence_penalty if model_config.presence_penalty else 0
            )
            
            response_text = completion.choices[0].message.content
            usage = {
                "prompt_tokens": completion.usage.prompt_tokens,
                "completion_tokens": completion.usage.completion_tokens,
                "total_tokens": completion.usage.total_tokens
            }
            
            return APIResponse(
                platform=self.platform_name,
                model=model_config.name,
                prompt=prompt,
                response=response_text,
                usage=usage,
                latency=0,
                success=True,
                raw_response=completion.model_dump()
            )
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {str(e)}")
            raise
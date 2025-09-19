from .base_client import BaseAPIClient, APIResponse
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient
from .generic_client import BaiduClient, ZhipuClient, AlibabaClient
import logging

logger = logging.getLogger(__name__)

class APIClientFactory:
    """工厂类，用于创建不同平台的API客户端"""
    
    client_mapping = {
        'openai': OpenAIClient,
        'anthropic': AnthropicClient,
        'baidu': BaiduClient,
        'zhipu': ZhipuClient,
        'alibaba': AlibabaClient
    }
    
    @classmethod
    def create_client(cls, platform_name: str, platform_config) -> BaseAPIClient:
        """根据平台名称创建对应的API客户端"""
        client_class = cls.client_mapping.get(platform_name)
        
        if client_class:
            return client_class(platform_config)
        else:
            logger.warning(f"未找到{platform_name}的客户端实现，使用默认客户端")
            return None

__all__ = ['BaseAPIClient', 'APIResponse', 'APIClientFactory']
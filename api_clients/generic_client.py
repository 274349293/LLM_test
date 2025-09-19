import requests
import json
import time
from .base_client import BaseAPIClient, APIResponse
import logging
import hashlib
import hmac

logger = logging.getLogger(__name__)

class GenericHTTPClient(BaseAPIClient):
    """通用HTTP客户端，用于处理基于HTTP请求的LLM API"""
    
    def __init__(self, platform_config):
        super().__init__(platform_config)
        self.api_key = platform_config.api_key
        self.secret_key = platform_config.secret_key
        self.base_url = platform_config.base_url
    
    def call_api(self, prompt: str, model_config) -> APIResponse:
        """子类应该重写此方法以实现具体的API调用"""
        raise NotImplementedError("子类必须实现call_api方法")

class BaiduClient(GenericHTTPClient):
    """百度文心一言API客户端"""
    
    def __init__(self, platform_config):
        super().__init__(platform_config)
        self.access_token = None
        self.token_expire_time = 0
    
    def get_access_token(self):
        """获取百度API的access token"""
        if self.access_token and time.time() < self.token_expire_time:
            return self.access_token
        
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }
        
        response = requests.get(url, params=params)
        result = response.json()
        
        if "access_token" in result:
            self.access_token = result["access_token"]
            self.token_expire_time = time.time() + result.get("expires_in", 3600) - 60
            return self.access_token
        else:
            raise Exception(f"获取百度access token失败: {result}")
    
    def call_api(self, prompt: str, model_config) -> APIResponse:
        try:
            access_token = self.get_access_token()
            
            # 根据模型名称构建URL
            model_endpoints = {
                "ERNIE-Bot-4": "completions_pro",
                "ERNIE-Bot": "completions",
                "ERNIE-Bot-turbo": "eb-instant"
            }
            endpoint = model_endpoints.get(model_config.name, "completions")
            
            url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{endpoint}"
            
            headers = {"Content-Type": "application/json"}
            params = {"access_token": access_token}
            
            data = {
                "messages": self.format_messages(prompt),
                "temperature": model_config.temperature,
                "max_output_tokens": model_config.max_tokens
            }
            
            response = requests.post(url, headers=headers, params=params, json=data)
            result = response.json()
            
            if "error_code" in result:
                raise Exception(f"百度API错误: {result}")
            
            response_text = result.get("result", "")
            usage = result.get("usage", {})
            
            return APIResponse(
                platform=self.platform_name,
                model=model_config.name,
                prompt=prompt,
                response=response_text,
                usage={
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0)
                },
                latency=0,
                success=True,
                raw_response=result
            )
        except Exception as e:
            logger.error(f"百度API调用失败: {str(e)}")
            raise

class ZhipuClient(GenericHTTPClient):
    """智谱AI API客户端"""
    
    def call_api(self, prompt: str, model_config) -> APIResponse:
        try:
            import zhipuai
            
            zhipuai.api_key = self.api_key
            
            response = zhipuai.ChatCompletion.create(
                model=model_config.name,
                messages=self.format_messages(prompt),
                temperature=model_config.temperature,
                max_tokens=model_config.max_tokens
            )
            
            response_text = response.choices[0].message.content
            usage = response.usage
            
            return APIResponse(
                platform=self.platform_name,
                model=model_config.name,
                prompt=prompt,
                response=response_text,
                usage={
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens
                },
                latency=0,
                success=True,
                raw_response=response
            )
        except Exception as e:
            logger.error(f"智谱API调用失败: {str(e)}")
            raise

class AlibabaClient(GenericHTTPClient):
    """阿里云通义千问API客户端"""
    
    def call_api(self, prompt: str, model_config) -> APIResponse:
        try:
            import dashscope
            from dashscope import Generation
            
            dashscope.api_key = self.api_key
            
            response = Generation.call(
                model=model_config.name,
                messages=self.format_messages(prompt),
                temperature=model_config.temperature,
                max_tokens=model_config.max_tokens,
                result_format='message'
            )
            
            if response.status_code == 200:
                response_text = response.output.choices[0].message.content
                usage = response.usage
                
                return APIResponse(
                    platform=self.platform_name,
                    model=model_config.name,
                    prompt=prompt,
                    response=response_text,
                    usage={
                        "prompt_tokens": usage.input_tokens,
                        "completion_tokens": usage.output_tokens,
                        "total_tokens": usage.total_tokens
                    },
                    latency=0,
                    success=True,
                    raw_response=response
                )
            else:
                raise Exception(f"阿里云API错误: {response}")
        except Exception as e:
            logger.error(f"阿里云API调用失败: {str(e)}")
            raise
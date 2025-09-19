import yaml
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    name: str
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None

@dataclass
class PlatformConfig:
    name: str
    enabled: bool
    api_key: str
    models: list[ModelConfig]
    base_url: Optional[str] = None
    secret_key: Optional[str] = None
    
class ConfigManager:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = None
        self.platforms = {}
        self.load_config()
    
    def load_config(self):
        if not os.path.exists(self.config_path):
            logger.warning(f"配置文件{self.config_path}不存在，请从config_template.yaml复制并配置")
            return
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self._parse_platforms()
        logger.info(f"成功加载配置文件: {self.config_path}")
    
    def _parse_platforms(self):
        platforms_config = self.config.get('platforms', {})
        
        for platform_name, platform_data in platforms_config.items():
            if not platform_data.get('enabled', False):
                continue
                
            models = []
            for model_data in platform_data.get('models', []):
                models.append(ModelConfig(
                    name=model_data['name'],
                    max_tokens=model_data.get('max_tokens', 1000),
                    temperature=model_data.get('temperature', 0.7),
                    top_p=model_data.get('top_p'),
                    frequency_penalty=model_data.get('frequency_penalty'),
                    presence_penalty=model_data.get('presence_penalty')
                ))
            
            self.platforms[platform_name] = PlatformConfig(
                name=platform_name,
                enabled=True,
                api_key=platform_data.get('api_key', ''),
                models=models,
                base_url=platform_data.get('base_url'),
                secret_key=platform_data.get('secret_key')
            )
    
    def get_platform_config(self, platform: str) -> Optional[PlatformConfig]:
        return self.platforms.get(platform)
    
    def get_enabled_platforms(self) -> list[str]:
        return list(self.platforms.keys())
    
    def get_test_prompts(self) -> list[Dict[str, Any]]:
        return self.config.get('test_settings', {}).get('test_prompts', [])
    
    def get_test_settings(self) -> Dict[str, Any]:
        return self.config.get('test_settings', {})

if __name__ == "__main__":
    config = ConfigManager()
    print(f"启用的平台: {config.get_enabled_platforms()}")
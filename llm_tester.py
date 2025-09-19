import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import print as rprint
import logging

from config_manager import ConfigManager
from api_clients import APIClientFactory, APIResponse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LLMTester:
    def __init__(self, config_path: str = "config.yaml"):
        self.console = Console()
        self.config_manager = ConfigManager(config_path)
        self.clients = {}
        self.results = []
        self._initialize_clients()
    
    def _initialize_clients(self):
        """初始化所有启用的平台客户端"""
        for platform_name in self.config_manager.get_enabled_platforms():
            platform_config = self.config_manager.get_platform_config(platform_name)
            client = APIClientFactory.create_client(platform_name, platform_config)
            if client:
                self.clients[platform_name] = client
                self.console.print(f"[green]✓[/green] 初始化{platform_name}客户端成功")
            else:
                self.console.print(f"[red]✗[/red] 初始化{platform_name}客户端失败")
    
    def test_single_model(self, platform_name: str, model_config, prompt: str) -> APIResponse:
        """测试单个模型"""
        client = self.clients.get(platform_name)
        if not client:
            logger.error(f"未找到{platform_name}客户端")
            return None
        
        return client.test_model(prompt, model_config)
    
    def run_tests(self, test_specific_platform: str = None, test_specific_model: str = None):
        """运行所有测试"""
        test_prompts = self.config_manager.get_test_prompts()
        
        if not test_prompts:
            self.console.print("[red]未找到测试提示词[/red]")
            return
        
        total_tests = 0
        platforms_to_test = [test_specific_platform] if test_specific_platform else self.clients.keys()
        
        for platform_name in platforms_to_test:
            platform_config = self.config_manager.get_platform_config(platform_name)
            if not platform_config:
                continue
            
            models_to_test = platform_config.models
            if test_specific_model:
                models_to_test = [m for m in models_to_test if m.name == test_specific_model]
            
            total_tests += len(models_to_test) * len(test_prompts)
        
        self.console.print(f"\n[bold]开始测试 - 总计{total_tests}个测试[/bold]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            for platform_name in platforms_to_test:
                platform_config = self.config_manager.get_platform_config(platform_name)
                if not platform_config:
                    continue
                
                models_to_test = platform_config.models
                if test_specific_model:
                    models_to_test = [m for m in models_to_test if m.name == test_specific_model]
                
                for model_config in models_to_test:
                    for prompt_data in test_prompts:
                        prompt = prompt_data['prompt']
                        category = prompt_data.get('category', 'general')
                        
                        task_desc = f"测试 {platform_name} - {model_config.name}"
                        task = progress.add_task(task_desc, total=1)
                        
                        result = self.test_single_model(platform_name, model_config, prompt)
                        
                        if result:
                            result.category = category
                            self.results.append(result)
                            
                            if result.success:
                                self.console.print(
                                    f"[green]✓[/green] {platform_name} - {model_config.name} - "
                                    f"响应时间: {result.latency:.2f}s"
                                )
                            else:
                                self.console.print(
                                    f"[red]✗[/red] {platform_name} - {model_config.name} - "
                                    f"错误: {result.error}"
                                )
                        
                        progress.update(task, advance=1)
        
        self.console.print(f"\n[bold green]测试完成![/bold green]")
    
    def save_results(self):
        """保存测试结果"""
        if not self.results:
            self.console.print("[yellow]没有测试结果需要保存[/yellow]")
            return
        
        results_dir = self.config_manager.get_test_settings().get('results_path', 'results/')
        os.makedirs(results_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存JSON格式
        json_file = os.path.join(results_dir, f'test_results_{timestamp}.json')
        results_data = []
        for r in self.results:
            result_dict = {
                'platform': r.platform,
                'model': r.model,
                'prompt': r.prompt,
                'response': r.response[:500],  # 仅保存前500个字符
                'usage': r.usage,
                'latency': r.latency,
                'success': r.success,
                'error': r.error,
                'category': getattr(r, 'category', 'general')
            }
            results_data.append(result_dict)
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)
        
        # 保存CSV格式
        csv_file = os.path.join(results_dir, f'test_results_{timestamp}.csv')
        df = pd.DataFrame(results_data)
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        self.console.print(f"\n[green]结果已保存:[/green]")
        self.console.print(f"  - JSON: {json_file}")
        self.console.print(f"  - CSV: {csv_file}")
    
    def display_summary(self):
        """显示测试摘要"""
        if not self.results:
            return
        
        # 创建摘要表格
        table = Table(title="测试结果摘要")
        table.add_column("平台", style="cyan")
        table.add_column("模型", style="magenta")
        table.add_column("成功率", justify="center")
        table.add_column("平均响应时间(s)", justify="right")
        table.add_column("平均Token消耗", justify="right")
        
        # 按平台和模型分组统计
        from collections import defaultdict
        stats = defaultdict(lambda: {'success': 0, 'total': 0, 'latency': [], 'tokens': []})
        
        for result in self.results:
            key = (result.platform, result.model)
            stats[key]['total'] += 1
            if result.success:
                stats[key]['success'] += 1
                stats[key]['latency'].append(result.latency)
                if result.usage and 'total_tokens' in result.usage:
                    stats[key]['tokens'].append(result.usage['total_tokens'])
        
        for (platform, model), data in stats.items():
            success_rate = f"{(data['success'] / data['total']) * 100:.1f}%"
            avg_latency = sum(data['latency']) / len(data['latency']) if data['latency'] else 0
            avg_tokens = sum(data['tokens']) / len(data['tokens']) if data['tokens'] else 0
            
            table.add_row(
                platform,
                model,
                success_rate,
                f"{avg_latency:.2f}",
                f"{avg_tokens:.0f}"
            )
        
        self.console.print("\n")
        self.console.print(table)

def main():
    console = Console()
    
    # 显示欢迎信息
    welcome_text = """
    [bold cyan]LLM API 测试工具[/bold cyan]
    
    此工具用于测试多个大语言模型API的性能和响应
    """
    console.print(Panel.fit(welcome_text, border_style="cyan"))
    
    # 检查配置文件
    if not os.path.exists("config.yaml"):
        console.print("[red]错误: 未找到config.yaml文件[/red]")
        console.print("请从config_template.yaml复制并配置您的API密钥")
        return
    
    # 创建测试器
    tester = LLMTester()
    
    # 运行测试
    try:
        tester.run_tests()
        tester.display_summary()
        tester.save_results()
    except KeyboardInterrupt:
        console.print("\n[yellow]测试被用户中断[/yellow]")
    except Exception as e:
        console.print(f"\n[red]测试过程中出现错误: {str(e)}[/red]")
        logger.exception("测试失败")

if __name__ == "__main__":
    main()
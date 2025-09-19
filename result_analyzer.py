import json
import pandas as pd
import os
from typing import List, Dict
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

class ResultAnalyzer:
    def __init__(self, results_dir: str = "results/"):
        self.results_dir = results_dir
        self.console = Console()
        self.data = None
    
    def load_latest_results(self) -> pd.DataFrame:
        """加载最新的测试结果"""
        if not os.path.exists(self.results_dir):
            self.console.print(f"[red]结果目录{self.results_dir}不存在[/red]")
            return None
        
        # 查找最新的JSON文件
        json_files = [f for f in os.listdir(self.results_dir) if f.endswith('.json')]
        if not json_files:
            self.console.print("[red]未找到测试结果文件[/red]")
            return None
        
        latest_file = sorted(json_files)[-1]
        file_path = os.path.join(self.results_dir, latest_file)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.data = pd.DataFrame(data)
        self.console.print(f"[green]已加载: {file_path}[/green]")
        return self.data
    
    def compare_platforms(self):
        """对比不同平台的性能"""
        if self.data is None:
            self.load_latest_results()
        
        if self.data is None or self.data.empty:
            return
        
        # 创建对比表格
        table = Table(title="平台性能对比")
        table.add_column("平台", style="cyan")
        table.add_column("成功率", justify="center")
        table.add_column("平均响应时间(s)", justify="right")
        table.add_column("最小响应时间(s)", justify="right")
        table.add_column("最大响应时间(s)", justify="right")
        table.add_column("平均Token消耗", justify="right")
        
        # 按平台分组统计
        for platform in self.data['platform'].unique():
            platform_data = self.data[self.data['platform'] == platform]
            success_data = platform_data[platform_data['success'] == True]
            
            success_rate = len(success_data) / len(platform_data) * 100
            avg_latency = success_data['latency'].mean() if not success_data.empty else 0
            min_latency = success_data['latency'].min() if not success_data.empty else 0
            max_latency = success_data['latency'].max() if not success_data.empty else 0
            
            # 计算平均token消耗
            tokens = []
            for usage in success_data['usage']:
                if usage and 'total_tokens' in usage:
                    tokens.append(usage['total_tokens'])
            avg_tokens = sum(tokens) / len(tokens) if tokens else 0
            
            table.add_row(
                platform,
                f"{success_rate:.1f}%",
                f"{avg_latency:.2f}",
                f"{min_latency:.2f}",
                f"{max_latency:.2f}",
                f"{avg_tokens:.0f}"
            )
        
        self.console.print("\n")
        self.console.print(table)
    
    def compare_models(self):
        """对比不同模型的性能"""
        if self.data is None:
            self.load_latest_results()
        
        if self.data is None or self.data.empty:
            return
        
        # 创建模型对比表格
        table = Table(title="模型性能对比")
        table.add_column("平台", style="cyan")
        table.add_column("模型", style="magenta")
        table.add_column("成功率", justify="center")
        table.add_column("平均响应时间(s)", justify="right")
        table.add_column("平均Token", justify="right")
        
        # 按平台和模型分组
        grouped = self.data.groupby(['platform', 'model'])
        
        for (platform, model), group in grouped:
            success_data = group[group['success'] == True]
            success_rate = len(success_data) / len(group) * 100
            avg_latency = success_data['latency'].mean() if not success_data.empty else 0
            
            # 计算平均token
            tokens = []
            for usage in success_data['usage']:
                if usage and 'total_tokens' in usage:
                    tokens.append(usage['total_tokens'])
            avg_tokens = sum(tokens) / len(tokens) if tokens else 0
            
            table.add_row(
                platform,
                model,
                f"{success_rate:.1f}%",
                f"{avg_latency:.2f}",
                f"{avg_tokens:.0f}"
            )
        
        self.console.print("\n")
        self.console.print(table)
    
    def analyze_by_category(self):
        """按类别分析测试结果"""
        if self.data is None:
            self.load_latest_results()
        
        if self.data is None or self.data.empty:
            return
        
        if 'category' not in self.data.columns:
            self.console.print("[yellow]测试结果中没有类别信息[/yellow]")
            return
        
        # 创建类别分析表格
        table = Table(title="按类别分析")
        table.add_column("类别", style="cyan")
        table.add_column("平台", style="magenta")
        table.add_column("模型", style="yellow")
        table.add_column("响应时间(s)", justify="right")
        table.add_column("状态", justify="center")
        
        # 按类别分组
        for category in self.data['category'].unique():
            category_data = self.data[self.data['category'] == category]
            
            for _, row in category_data.iterrows():
                status = "[green]✓[/green]" if row['success'] else "[red]✗[/red]"
                table.add_row(
                    category,
                    row['platform'],
                    row['model'],
                    f"{row['latency']:.2f}",
                    status
                )
        
        self.console.print("\n")
        self.console.print(table)
    
    def generate_report(self, output_file: str = None):
        """生成详细的分析报告"""
        if self.data is None:
            self.load_latest_results()
        
        if self.data is None or self.data.empty:
            return
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        report = f"""
# LLM API 测试报告

生成时间: {timestamp}

## 测试概要

- 测试平台数: {len(self.data['platform'].unique())}
- 测试模型数: {len(self.data.groupby(['platform', 'model']))}
- 总测试次数: {len(self.data)}
- 成功率: {(self.data['success'].sum() / len(self.data) * 100):.1f}%

## 最佳性能

### 响应速度最快
"""
        
        # 找出响应最快的模型
        success_data = self.data[self.data['success'] == True]
        if not success_data.empty:
            fastest = success_data.loc[success_data['latency'].idxmin()]
            report += f"- 平台: {fastest['platform']}\n"
            report += f"- 模型: {fastest['model']}\n"
            report += f"- 响应时间: {fastest['latency']:.2f}s\n\n"
        
        # 添加平台对比
        report += "## 平台对比\n\n"
        platform_stats = []
        for platform in self.data['platform'].unique():
            platform_data = self.data[self.data['platform'] == platform]
            success_data = platform_data[platform_data['success'] == True]
            
            stats = {
                '平台': platform,
                '成功率': f"{len(success_data) / len(platform_data) * 100:.1f}%",
                '平均响应时间': f"{success_data['latency'].mean():.2f}s" if not success_data.empty else "N/A"
            }
            platform_stats.append(stats)
        
        df_platforms = pd.DataFrame(platform_stats)
        report += df_platforms.to_markdown(index=False) + "\n\n"
        
        # 保存报告
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            self.console.print(f"[green]报告已保存到: {output_file}[/green]")
        else:
            output_file = os.path.join(self.results_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            self.console.print(f"[green]报告已保存到: {output_file}[/green]")
        
        return report

def main():
    console = Console()
    analyzer = ResultAnalyzer()
    
    console.print("[bold cyan]LLM 测试结果分析器[/bold cyan]\n")
    
    # 加载最新结果
    data = analyzer.load_latest_results()
    if data is None:
        return
    
    # 显示各种分析
    analyzer.compare_platforms()
    analyzer.compare_models()
    analyzer.analyze_by_category()
    
    # 生成报告
    analyzer.generate_report()

if __name__ == "__main__":
    main()
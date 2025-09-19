# LLM API 测试工具

一个用于测试多个大语言模型（LLM）API性能的统一测试框架。

## 支持的平台

- OpenAI (GPT-3.5, GPT-4等)
- Anthropic (Claude系列)
- 百度文心一言 (ERNIE-Bot系列)
- 阿里云通义千问 (Qwen系列)
- 智谱AI (GLM系列)

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API 密钥

复制配置模板并填写您的API密钥：

```bash
cp config_template.yaml config.yaml
```

编辑 `config.yaml` 文件，填入各平台的API密钥和配置。

### 3. 运行测试

```bash
python llm_tester.py
```

### 4. 分析结果

```bash
python result_analyzer.py
```

## 项目结构

```
LLM_test/
├── config_template.yaml  # 配置模板
├── config.yaml          # 实际配置（需要创建）
├── config_manager.py    # 配置管理模块
├── llm_tester.py        # 主测试脚本
├── result_analyzer.py   # 结果分析器
├── api_clients/         # API客户端实现
│   ├── __init__.py
│   ├── base_client.py  # 基础客户端类
│   ├── openai_client.py
│   ├── anthropic_client.py
│   └── generic_client.py # 通用HTTP客户端
└── results/             # 测试结果存储目录
```

## 配置说明

### 添加新的测试提示词

在 `config.yaml` 的 `test_prompts` 部分添加新的测试提示：

```yaml
test_prompts:
  - prompt: "您的测试提示"
    category: "分类名称"
```

### 配置模型参数

每个模型可以配置以下参数：
- `name`: 模型名称
- `max_tokens`: 最大生成token数
- `temperature`: 生成随机度(0-1)
- `top_p`: 核采样参数（可选）

## 使用注意事项

1. **API密钥安全**: 请勿将包含API密钥的 `config.yaml` 文件提交到版本控制系统。

2. **依赖安装**: 部分平台可能需要额外安装其官方SDK：
   ```bash
   pip install zhipuai  # 智谱AI
   pip install dashscope  # 阿里云
   ```

3. **网络访问**: 确保您的网络能够访问各个API端点。

## 扩展新平台

要添加新的LLM平台支持：

1. 在 `api_clients/` 目录下创建新的客户端类
2. 继承 `BaseAPIClient` 并实现 `call_api` 方法
3. 在 `APIClientFactory` 中注册新客户端
4. 在 `config_template.yaml` 中添加配置示例

## 输出格式

测试结果会以以下格式保存：
- JSON格式：完整的测试数据
- CSV格式：便于Excel分析
- Markdown报告：可读性强的分析报告

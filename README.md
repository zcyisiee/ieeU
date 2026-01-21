# ieeU - PDF智能解析工具

[![PyPI Version](https://img.shields.io/pypi/v/ieeU)](https://pypi.org/project/ieeU/)
[![Python Version](https://img.shields.io/pypi/pyversions/ieeU)](https://pypi.org/project/ieeU/)
[![License](https://img.shields.io/pypi/l/ieeU)](https://opensource.org/licenses/MIT/)

一键将PDF文件解析为Markdown，并使用VLM将图片替换为描述性文本。

## 功能特性

- **PDF解析**：调用MinerU云端API将PDF转换为Markdown
- **图片描述**：使用VLM（视觉语言模型）生成图片的文字描述
- **一键处理**：单条命令完成PDF→Markdown→图片描述替换的完整流程

## 安装

```bash
pip install ieeU
```

或从源码安装：

```bash
pip install -e .
```

## 快速开始

### 1. 配置API

在 `~/.ieeU/settings.json` 中配置：

```json
{
    "endpoint": "https://openrouter.ai/api/v1/chat/completions",
    "key": "your-vlm-api-key",
    "modelName": "google/gemini-3-flash-preview",
    "mineruToken": "your-mineru-token"
}
```

获取 MinerU Token：访问 [mineru.net](https://mineru.net) 注册并获取API Token。

### 2. 处理PDF

```bash
ieeU process paper.pdf
```

输出：`paper.md`（与PDF同目录）

## 命令行接口

```bash
ieeU --help                    # 显示帮助信息
ieeU --version                 # 显示版本号

# 主要命令：处理PDF文件
ieeU process paper.pdf              # 处理PDF，输出到同目录
ieeU process paper.pdf -o ./output  # 指定输出目录
ieeU process paper.pdf --verbose    # 详细输出模式

# 向后兼容：处理已有的Markdown文件
ieeU run                       # 处理当前目录的full.md文件
ieeU run --verbose             # 详细输出模式
```

## 配置文件

### 必填项
| 字段 | 说明 |
|------|------|
| `endpoint` | VLM API端点URL |
| `key` | VLM API密钥 |
| `modelName` | VLM模型名称 |
| `mineruToken` | MinerU API Token（`process`命令必需） |

### 可选项
| 字段 | 说明 | 默认值 |
|------|------|--------|
| `timeout` | 请求超时（秒） | 60 |
| `retries` | 重试次数 | 3 |
| `maxConcurrency` | 最大并发数 | 5 |

### 环境变量

可覆盖配置文件：
- `IEEU_ENDPOINT`
- `IEEU_KEY`
- `IEEU_MODEL`
- `IEEU_MINERU_TOKEN`

## 输出示例

处理前（PDF中的图片）：
```markdown
![](images/figure1.jpg)
Figure 1 shows the architecture.
```

处理后：
````markdown
```figure 1
This figure illustrates the overall architecture of the system, 
showing three main components connected by data flow arrows...
```

Figure 1 shows the architecture.
````

## 开发

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest tests/
```

### 构建发布包

```bash
pip install build
python -m build
twine check dist/*
```

## 发布到PyPI

```bash
# 构建
python -m build

# 发布
twine upload dist/*
```

## 支持的VLM

- OpenAI GPT-4V
- Google Gemini (via OpenRouter)
- Anthropic Claude (via OpenRouter)
- 其他OpenAI兼容的API

## License

MIT License

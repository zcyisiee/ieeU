# ieeU - 图片描述替换工具

[![PyPI Version](https://img.shields.io/pypi/v/ieeU)](https://pypi.org/project/ieeU/)
[![Python Version](https://img.shields.io/pypi/pyversions/ieeU)](https://pypi.org/project/ieeU/)
[![License](https://img.shields.io/pypi/l/ieeU)](https://opensource.org/licenses/MIT/)

将MinerU转换后的Markdown文件中的图片链接替换为VLM生成的描述性文本。

## 安装

```bash
pip install ieeU
```

或从源码安装：

```bash
pip install -e .
```

## 使用

### 命令行接口

```bash
ieeU --help          # 显示帮助信息
ieeU --version       # 显示版本号
ieeU run             # 执行图片描述转换
ieeU run --verbose   # 详细输出模式
```

### 配置文件

在 `~/.ieeU/settings.json` 中配置API：

```json
{
    "endpoint": "https://openrouter.ai/api/v1/chat/completions",
    "key": "your-api-key",
    "modelName": "google/gemini-3-flash-preview",
    "timeout": 120,
    "retries": 3,
    "maxConcurrency": 3
}
```

#### 必填项
- `endpoint`: API端点URL
- `key`: API密钥
- `modelName`: 模型名称

#### 可选项
- `timeout`: 请求超时（秒），默认60
- `retries`: 重试次数，默认3
- `maxConcurrency`: 最大并发数，默认5

### 环境变量

可覆盖配置：
- `IEEU_ENDPOINT`
- `IEEU_KEY`
- `IEEU_MODEL`

### 示例

在包含 `full.md` 的目录中运行：

```bash
ieeU run
```

处理前：
```markdown
![](images/figure1.jpg)
Figure 1 shows the architecture.
```

处理后：
````markdown
```figure 1
This figure illustrates the overall architecture of the system...
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

1. 安装构建工具：
   ```bash
   pip install build twine
   ```

2. 构建包：
   ```bash
   python -m build
   ```

3. 发布到Test PyPI（测试）：
   ```bash
   twine upload --repository testpypi dist/*
   ```

4. 发布到PyPI：
   ```bash
   twine upload dist/*
   ```

或使用GitHub Actions自动发布：
1. 创建PyPI API Token
2. 添加到GitHub Secrets: `PYPI_API_TOKEN`
3. 创建Release并发布

## 支持的VLM

- OpenAI GPT-4V
- Google Gemini (via OpenRouter)
- Anthropic Claude (via OpenRouter)
- 其他OpenAI兼容的API

## License

MIT License

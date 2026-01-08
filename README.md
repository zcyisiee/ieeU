# ieeU - 图片描述替换工具

将MinerU转换后的Markdown文件中的图片链接替换为VLM生成的描述性文本。

## 安装

```bash
pip install -e .
```

## 配置

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

### 必填项
- `endpoint`: API端点URL
- `key`: API密钥
- `modelName`: 模型名称

### 可选项
- `timeout`: 请求超时（秒）
- `retries`: 重试次数
- `maxConcurrency`: 最大并发数

## 使用

在包含 `full.md` 的目录中运行：

```bash
ieeU run
```

工具将：
1. 读取 `full.md` 文件
2. 提取所有图片引用
3. 调用VLM生成描述
4. 输出 `full.iee.md` 文件

### 示例

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

## 环境变量

可覆盖配置：
- `IEEU_ENDPOINT`
- `IEEU_KEY`
- `IEEU_MODEL`

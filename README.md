# ieeU

ieeU is a command-line tool that replaces image links in Markdown files with VLM-generated descriptive text.

## Installation

```bash
pip install -e .
```

## Configuration

Create a configuration file at `~/.ieeU/settings.json`:

```json
{
    "endpoint": "https://api.openai.com/v1",
    "key": "your-api-key",
    "modelName": "gpt-4-vision-preview",
    "timeout": 60,
    "retries": 3,
    "maxConcurrency": 5
}
```

### Required fields:
- `endpoint`: API endpoint URL
- `key`: API key
- `modelName`: Model name (e.g., `gpt-4-vision-preview`)

### Optional fields:
- `timeout`: Request timeout in seconds (default: 60)
- `retries`: Number of retry attempts (default: 3)
- `maxConcurrency`: Maximum concurrent API calls (default: 5)

## Usage

Navigate to a directory containing MinerU-processed Markdown files and run:

```bash
ieeU run
```

The tool will:
1. Find all Markdown files in the current directory
2. Extract image references from each file
3. Generate descriptions for each image using VLM
4. Create new files with `.iee.md` suffix

## Example

Before:
```markdown
![](/path/to/image.jpg)
Figure 1 shows the architecture.
```

After:
```markdown
```figure 1
This figure illustrates the overall architecture of the system...
```
Figure 1 shows the architecture.
```

## Environment Variables

Override configuration using environment variables:
- `IEEU_ENDPOINT`
- `IEEU_KEY`
- `IEEU_MODEL`

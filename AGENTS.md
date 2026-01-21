# PROJECT KNOWLEDGE BASE

**Generated:** 2026-01-21
**Commit:** e613866
**Branch:** main

## OVERVIEW

CLI tool replacing Markdown image links with VLM-generated descriptions. Python 3.8+, OpenAI-compatible API.

## STRUCTURE

```
ieeU/
├── ieeU/           # Core package (CLI, processing, VLM client)
├── tests/          # pytest tests
├── examples/       # Usage examples
└── pyproject.toml  # Build config, entry point: ieeU.cli:main
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| CLI entry point | `ieeU/cli.py` | argparse, `run` subcommand |
| Image processing | `ieeU/processor.py` | Orchestrates extraction → VLM → replacement |
| VLM API calls | `ieeU/vlm.py` | OpenAI-compatible, concurrent requests |
| Image extraction | `ieeU/extractor.py` | Regex-based MD image parsing |
| Configuration | `ieeU/config.py` | JSON config + env overrides |
| Constants/prompts | `ieeU/constants.py` | VLM prompt template, defaults |

## CODE MAP

| Symbol | Type | Location | Role |
|--------|------|----------|------|
| `Processor` | class | processor.py | Main orchestrator |
| `VLMClient` | class | vlm.py | API client with retry/concurrency |
| `ImageExtractor` | class | extractor.py | Static methods for MD parsing |
| `ImageReference` | class | extractor.py | Data class for image refs |
| `Config` | class | config.py | Settings with validation |

## CONVENTIONS

- Config file: `~/.ieeU/settings.json` (endpoint, key, modelName required)
- Env overrides: `IEEU_ENDPOINT`, `IEEU_KEY`, `IEEU_MODEL`
- Output files: `{filename}_ie.md` suffix
- Only processes `full.md` files in target directory
- Chinese CLI messages, English code/logs

## ANTI-PATTERNS

- **NEVER** hardcode API keys - always use config/env
- **NEVER** modify original `full.md` - always output to `_ie.md`
- **NEVER** skip image if VLM fails - log error, continue batch

## COMMANDS

```bash
# Install
pip install -e .

# Run (in directory with full.md)
ieeU run
ieeU run --verbose

# Test
pytest tests/

# Build
python -m build
```

## NOTES

- VLM response must be wrapped in ```figure\n...\n``` block
- Concurrent API calls limited by `maxConcurrency` config (default: 5)
- Retry with exponential backoff on API failures
- Figure numbering is sequential per file (1, 2, 3...)

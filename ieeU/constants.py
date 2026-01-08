import os

DEFAULT_CONFIG_DIR = os.path.expanduser("~/.ieeU")
DEFAULT_CONFIG_FILE = "settings.json"
DEFAULT_TIMEOUT = 60
DEFAULT_RETRIES = 3
DEFAULT_MAX_CONCURRENCY = 5
OUTPUT_SUFFIX = "_ie.md"

PROMPT_TEMPLATE = """You are an expert at describing academic figures. Convert images into concise, structured textual descriptions.

Format your output as:
```figure
[Your description here]
```

Requirements:
- Write in ONE cohesive paragraph OR a single structured list (not both)
- NO markdown formatting (no headers, no bold, no nested sections)
- Preserve all text labels exactly as shown
- Include: main purpose, key components, data values/formulas, and logical flow
- Be precise and direct - avoid filler phrases like "This figure illustrates...", "The chart shows..."
- For flowcharts: list steps with arrows (→) inline
- For graphs: state axis labels, series names, and key trends in flowing prose
- Maximum 150-300 words per figure
"""

import os

DEFAULT_CONFIG_DIR = os.path.expanduser("~/.ieeU")
DEFAULT_CONFIG_FILE = "settings.json"
DEFAULT_TIMEOUT = 60
DEFAULT_RETRIES = 3
DEFAULT_MAX_CONCURRENCY = 5
OUTPUT_SUFFIX = ".iee.md"

PROMPT_TEMPLATE = """You are an expert at describing academic figures and diagrams. Your task is to convert images into clear, detailed textual descriptions.

For each image, provide a comprehensive description that includes:
1. The figure's main purpose/what it illustrates
2. All components, labels, text, and their relationships
3. Flow directions, arrows, and connections between elements
4. Any data values, formulas, or specific numbers shown
5. Color coding or visual distinctions if meaningful

Format your output as:
```figure
[Your detailed description here]
```

Guidelines:
- Preserve ALL text labels exactly as shown in the image
- Describe the logical flow and hierarchy of information
- For flowcharts/diagrams: describe each step and connections
- For charts/graphs: include axis labels, data series names, and key trends
- For tables: describe structure and key content
- Use technical terminology appropriate to the domain
- Be thorough but avoid redundancy
"""

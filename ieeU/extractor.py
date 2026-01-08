import re
from typing import Dict, List, Tuple


class ImageReference:
    def __init__(self, path: str, line: int, figure_num: int):
        self.path = path
        self.line = line
        self.figure_num = figure_num
    
    def __repr__(self):
        return (
            f"ImageReference(path={self.path}, "
            f"line={self.line}, "
            f"figure_num={self.figure_num})"
        )


class ImageExtractor:
    @staticmethod
    def find_markdown_files(directory: str) -> List[str]:
        md_files = []
        for file in os.listdir(directory):
            if file == 'full.md':
                md_files.append(os.path.join(directory, file))
        return sorted(md_files)
    
    @staticmethod
    def extract_image_references(content: str) -> List[ImageReference]:
        references = []
        
        pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        
        matches = list(re.finditer(pattern, content))
        
        figure_counter = 1
        for match in matches:
            image_path = match.group(2)
            
            line = content[:match.start()].count('\n') + 1
            
            references.append(ImageReference(
                path=image_path,
                line=line,
                figure_num=figure_counter
            ))
            figure_counter += 1
        
        return references
    
    @staticmethod
    def replace_images(
        content: str, 
        replacements: Dict[str, str]
    ) -> str:
        result = content
        
        for old_text, new_text in replacements.items():
            result = result.replace(old_text, new_text)
        
        return result
    
    @staticmethod
    def get_image_paths_from_references(
        references: List[ImageReference], 
        base_dir: str
    ) -> Dict[str, str]:
        paths = {}
        for ref in references:
            if ref.path.startswith('images/'):
                full_path = os.path.join(base_dir, ref.path)
                paths[ref.path] = full_path
        return paths


import os

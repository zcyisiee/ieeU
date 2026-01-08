import os
from typing import Dict, List
from .config import Config
from .constants import OUTPUT_SUFFIX
from .extractor import ImageExtractor, ImageReference
from .logger import Logger
from .vlm import VLMClient


class Processor:
    def __init__(self, config: Config, verbose: bool = False):
        self.config = config
        self.logger = Logger(verbose)
        self.vlm_client = VLMClient(config, self.logger)
    
    def _build_replacement(
        self, 
        ref: ImageReference, 
        description: str
    ) -> str:
        return f"```figure {ref.figure_num}\n{description}\n```"
    
    def _process_single_file(
        self, 
        file_path: str
    ) -> bool:
        filename = os.path.basename(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        references = ImageExtractor.extract_image_references(content)
        
        if not references:
            print(f"No images found in {filename}")
            return True
        
        self.logger.log_file_info(filename, len(references))
        
        image_paths = ImageExtractor.get_image_paths_from_references(
            references, 
            os.path.dirname(file_path)
        )
        
        descriptions = self.vlm_client.describe_images_batch(image_paths)
        
        replacements = {}
        for ref in references:
            if ref.path in descriptions:
                new_text = self._build_replacement(ref, descriptions[ref.path])
                old_text = f"![]({ref.path})"
                replacements[old_text] = new_text
            else:
                self.logger.log_error(
                    ref.path, 
                    "No description generated"
                )
        
        if replacements:
            new_content = ImageExtractor.replace_images(
                content, 
                replacements
            )
            
            base_name = os.path.splitext(filename)[0]
            output_filename = f"{base_name}{OUTPUT_SUFFIX}"
            output_path = os.path.join(
                os.path.dirname(file_path), 
                output_filename
            )
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            self.logger.log_output(output_filename)
        
        return True
    
    def process_directory(self, directory: str = "."):
        self.logger.log_start()
        
        self.config.validate()
        
        md_files = ImageExtractor.find_markdown_files(directory)
        
        if not md_files:
            print("No markdown files found in the current directory.")
            return
        
        print(f"Found {len(md_files)} markdown file(s).\n")
        
        for file_path in md_files:
            try:
                self._process_single_file(file_path)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                continue
        
        self.logger.log_summary()

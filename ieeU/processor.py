import os
import shutil
import tempfile
from typing import Dict, List, Optional, Tuple
from .config import Config
from .constants import OUTPUT_SUFFIX
from .extractor import ImageExtractor, ImageReference
from .logger import Logger
from .mineru import MinerUClient
from .vlm import VLMClient, BatchResult


class ProcessResult:
    def __init__(self):
        self.success: bool = True
        self.output_path: Optional[str] = None
        self.images_dir: Optional[str] = None
        self.fallback_md_path: Optional[str] = None
        self.api_failed: bool = False
        self.failed_images: List[str] = []


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
        return f"```figure {ref.figure_num}\n{description}\n```\n"
    
    def _copy_fallback_output(
        self,
        md_path: str,
        images_dir: str,
        output_dir: str,
        pdf_name: str
    ) -> Tuple[str, str]:
        fallback_md = os.path.join(output_dir, f"{pdf_name}_full.md")
        shutil.copy2(md_path, fallback_md)
        
        fallback_images = os.path.join(output_dir, f"{pdf_name}_images")
        if os.path.exists(images_dir):
            if os.path.exists(fallback_images):
                shutil.rmtree(fallback_images)
            shutil.copytree(images_dir, fallback_images)
        
        return fallback_md, fallback_images
    
    def _process_markdown_content(
        self,
        content: str,
        base_dir: str,
        filename: str
    ) -> Tuple[str, BatchResult]:
        references = ImageExtractor.extract_image_references(content)
        
        if not references:
            print(f"No images found in {filename}")
            return content, BatchResult()
        
        self.logger.log_file_info(filename, len(references))
        
        image_paths = ImageExtractor.get_image_paths_from_references(
            references, 
            base_dir
        )
        
        if not image_paths:
            print(f"No valid image paths found")
            return content, BatchResult()
        
        batch_result = self.vlm_client.describe_images_batch(image_paths)
        
        replacements = {}
        for ref in references:
            if ref.path in batch_result.results:
                new_text = self._build_replacement(ref, batch_result.results[ref.path])
                old_text = f"![]({ref.path})"
                replacements[old_text] = new_text
            else:
                self.logger.log_error(
                    ref.path, 
                    "No description generated"
                )
        
        if replacements:
            return ImageExtractor.replace_images(content, replacements), batch_result
        
        return content, batch_result
    
    def process_pdf(self, pdf_path: str, output_dir: str) -> ProcessResult:
        self.logger.log_start()
        result = ProcessResult()
        
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        
        mineru_client = MinerUClient(self.config.mineru_token or "", self.logger)
        
        temp_dir = tempfile.mkdtemp(prefix="ieeu_")
        
        try:
            md_path, images_dir = mineru_client.parse_pdf(pdf_path, temp_dir)
            
            if not md_path:
                print("MinerU 解析失败")
                result.success = False
                return result
            
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            md_dir = os.path.dirname(md_path)
            processed_content, batch_result = self._process_markdown_content(
                content,
                md_dir,
                os.path.basename(md_path)
            )
            
            if batch_result.api_completely_failed:
                print("\n⚠️ VLM API无法使用，输出MinerU原始结果")
                fallback_md, fallback_images = self._copy_fallback_output(
                    md_path, images_dir or "", output_dir, pdf_name
                )
                result.api_failed = True
                result.fallback_md_path = fallback_md
                result.images_dir = fallback_images
                print(f"\n输出文件: {fallback_md}")
                print(f"图片目录: {fallback_images}")
                return result
            
            output_path = os.path.join(output_dir, f"{pdf_name}.md")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(processed_content)
            
            result.output_path = output_path
            result.failed_images = batch_result.failed_paths
            
            print(f"\n输出文件: {output_path}")
            
            if batch_result.failed_paths:
                print(f"⚠️ {len(batch_result.failed_paths)} 张图片处理失败")
            
            self.logger.log_summary()
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        return result
    
    def _process_single_file(
        self, 
        file_path: str
    ) -> ProcessResult:
        result = ProcessResult()
        filename = os.path.basename(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        references = ImageExtractor.extract_image_references(content)
        
        if not references:
            print(f"No images found in {filename}")
            result.success = True
            return result
        
        self.logger.log_file_info(filename, len(references))
        
        image_paths = ImageExtractor.get_image_paths_from_references(
            references, 
            os.path.dirname(file_path)
        )
        
        batch_result = self.vlm_client.describe_images_batch(image_paths)
        
        if batch_result.api_completely_failed:
            print(f"\n⚠️ VLM API无法使用，跳过文件 {filename}")
            result.api_failed = True
            return result
        
        replacements = {}
        for ref in references:
            if ref.path in batch_result.results:
                new_text = self._build_replacement(ref, batch_result.results[ref.path])
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
            
            result.output_path = output_path
            self.logger.log_output(output_filename)
        
        result.failed_images = batch_result.failed_paths
        
        if batch_result.failed_paths:
            print(f"⚠️ {len(batch_result.failed_paths)} 张图片处理失败")
        
        return result
    
    def process_directory(self, directory: str = "."):
        self.logger.log_start()
        
        self.config.validate()
        
        md_files = ImageExtractor.find_markdown_files(directory)
        
        if not md_files:
            print("No markdown files found in the current directory.")
            return
        
        print(f"Found {len(md_files)} markdown file(s).\n")
        
        total_failed = 0
        api_failed = False
        
        for file_path in md_files:
            try:
                result = self._process_single_file(file_path)
                if result.api_failed:
                    api_failed = True
                    break
                total_failed += len(result.failed_images)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                continue
        
        if api_failed:
            print("\n❌ API认证失败，请检查配置后重试")
        elif total_failed > 0:
            print(f"\n⚠️ 共 {total_failed} 张图片处理失败")
        
        self.logger.log_summary()

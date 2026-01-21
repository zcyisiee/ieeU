"""MinerU API client for PDF parsing."""

import io
import os
import time
import zipfile
from typing import Optional, Tuple

import requests

from .logger import Logger


class MinerUClient:
    """Client for MinerU cloud API."""
    
    BASE_URL = "https://mineru.net/api/v4"
    
    def __init__(self, token: str, logger: Logger):
        self.token = token
        self.logger = logger
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    
    def _upload_file(self, pdf_path: str) -> Optional[str]:
        """
        Upload PDF file and get batch_id.
        
        Returns:
            batch_id if successful, None otherwise
        """
        filename = os.path.basename(pdf_path)
        
        # Step 1: Get upload URL
        url = f"{self.BASE_URL}/file-urls/batch"
        data = {
            "files": [{"name": filename}],
            "model_version": "vlm"
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 0:
                self.logger.log_error(
                    pdf_path, 
                    f"MinerU API error: {result.get('msg', 'Unknown error')}"
                )
                return None
            
            batch_id = result["data"]["batch_id"]
            file_urls = result["data"]["file_urls"]
            
            if not file_urls:
                self.logger.log_error(pdf_path, "No upload URL returned")
                return None
            
            upload_url = file_urls[0]
            
            # Step 2: Upload file
            with open(pdf_path, 'rb') as f:
                upload_response = requests.put(upload_url, data=f)
                
                if upload_response.status_code != 200:
                    self.logger.log_error(
                        pdf_path, 
                        f"Upload failed: {upload_response.status_code}"
                    )
                    return None
            
            print(f"文件上传成功: {filename}")
            return batch_id
            
        except requests.exceptions.RequestException as e:
            self.logger.log_error(pdf_path, f"Request failed: {e}")
            return None
    
    def _poll_result(
        self, 
        batch_id: str, 
        timeout: int = 300,
        poll_interval: int = 5
    ) -> Optional[str]:
        """
        Poll for extraction result.
        
        Args:
            batch_id: Batch ID from upload
            timeout: Max wait time in seconds
            poll_interval: Seconds between polls
            
        Returns:
            full_zip_url if successful, None otherwise
        """
        url = f"{self.BASE_URL}/extract-results/batch/{batch_id}"
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                result = response.json()
                
                if result.get("code") != 0:
                    print(f"查询失败: {result.get('msg', 'Unknown error')}")
                    return None
                
                extract_results = result["data"].get("extract_result", [])
                
                if not extract_results:
                    time.sleep(poll_interval)
                    continue
                
                task = extract_results[0]
                state = task.get("state", "")
                
                if state == "done":
                    print("解析完成!")
                    return task.get("full_zip_url")
                
                elif state == "failed":
                    err_msg = task.get("err_msg", "Unknown error")
                    print(f"解析失败: {err_msg}")
                    return None
                
                elif state == "running":
                    progress = task.get("extract_progress", {})
                    extracted = progress.get("extracted_pages", 0)
                    total = progress.get("total_pages", 0)
                    print(f"解析中: {extracted}/{total} 页...")
                
                elif state in ("pending", "waiting-file", "converting"):
                    print(f"状态: {state}...")
                
                time.sleep(poll_interval)
                
            except requests.exceptions.RequestException as e:
                print(f"查询请求失败: {e}")
                time.sleep(poll_interval)
        
        print(f"超时: 等待超过 {timeout} 秒")
        return None
    
    def _download_and_extract(
        self, 
        zip_url: str, 
        extract_dir: str
    ) -> Optional[str]:
        """
        Download zip and extract to directory.
        
        Returns:
            Path to extracted markdown file, None if failed
        """
        try:
            print(f"下载结果文件...")
            response = requests.get(zip_url, timeout=120)
            response.raise_for_status()
            
            # Extract zip in memory
            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                zf.extractall(extract_dir)
            
            # Find markdown file
            for root, dirs, files in os.walk(extract_dir):
                for f in files:
                    if f.endswith('.md'):
                        md_path = os.path.join(root, f)
                        print(f"找到 Markdown: {f}")
                        return md_path
            
            print("未找到 Markdown 文件")
            return None
            
        except Exception as e:
            print(f"下载/解压失败: {e}")
            return None
    
    def parse_pdf(
        self, 
        pdf_path: str, 
        work_dir: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse PDF using MinerU API.
        
        Args:
            pdf_path: Path to PDF file
            work_dir: Directory to extract results
            
        Returns:
            Tuple of (markdown_path, images_dir) or (None, None) if failed
        """
        print(f"\n正在使用 MinerU 解析 PDF: {os.path.basename(pdf_path)}")
        
        # Upload
        batch_id = self._upload_file(pdf_path)
        if not batch_id:
            return None, None
        
        # Poll for result
        zip_url = self._poll_result(batch_id)
        if not zip_url:
            return None, None
        
        # Download and extract
        md_path = self._download_and_extract(zip_url, work_dir)
        if not md_path:
            return None, None
        
        # Find images directory
        md_dir = os.path.dirname(md_path)
        images_dir = os.path.join(md_dir, "images")
        
        if not os.path.isdir(images_dir):
            images_dir = None
        
        return md_path, images_dir

import base64
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
from typing import Dict, List, Optional, Tuple
import requests

from .config import Config
from .constants import PROMPT_TEMPLATE, DEFAULT_BATCH_SIZE
from .logger import Logger


class APIErrorType(Enum):
    """API错误类型枚举"""
    SUCCESS = "success"
    AUTH_ERROR = "auth_error"          # API密钥问题 (401, 403)
    RATE_LIMIT = "rate_limit"          # 并发限制 (429)
    CONCURRENCY_ERROR = "concurrency"  # 并发相关错误
    SERVER_ERROR = "server_error"      # 服务器错误 (5xx)
    TIMEOUT = "timeout"                # 超时
    NETWORK_ERROR = "network_error"    # 网络错误
    UNKNOWN = "unknown"                # 未知错误


class BatchResult:
    """批次处理结果"""
    def __init__(self):
        self.results: Dict[str, str] = {}
        self.failed_paths: List[str] = []
        self.error_type: Optional[APIErrorType] = None
        self.should_fallback_sequential: bool = False
        self.api_completely_failed: bool = False


class VLMClient:
    def __init__(self, config: Config, logger: Logger):
        self.config = config
        self.logger = logger
        self._consecutive_failures = 0
        self._max_consecutive_failures = 3
        self._concurrency_failed = False
    
    def _encode_image(self, image_path: str) -> Optional[str]:
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
                return base64.b64encode(image_data).decode('utf-8')
        except Exception as e:
            self.logger.log_error(image_path, f"Failed to read image: {e}")
            return None
    
    def _classify_error(self, error: Exception, response: Optional[requests.Response] = None) -> APIErrorType:
        """根据异常和响应分类错误类型"""
        if isinstance(error, requests.exceptions.Timeout):
            return APIErrorType.TIMEOUT
        
        if isinstance(error, requests.exceptions.ConnectionError):
            return APIErrorType.NETWORK_ERROR
        
        if response is not None:
            status_code = response.status_code
            if status_code in (401, 403):
                return APIErrorType.AUTH_ERROR
            elif status_code == 429:
                return APIErrorType.RATE_LIMIT
            elif status_code >= 500:
                return APIErrorType.SERVER_ERROR
        
        if isinstance(error, requests.exceptions.HTTPError):
            if hasattr(error, 'response') and error.response is not None:
                status_code = error.response.status_code
                if status_code in (401, 403):
                    return APIErrorType.AUTH_ERROR
                elif status_code == 429:
                    return APIErrorType.RATE_LIMIT
                elif status_code >= 500:
                    return APIErrorType.SERVER_ERROR
        
        # 检查错误消息中的并发相关关键词
        error_msg = str(error).lower()
        concurrency_keywords = ['concurrent', 'rate limit', 'too many', 'throttl', 'quota']
        if any(kw in error_msg for kw in concurrency_keywords):
            return APIErrorType.CONCURRENCY_ERROR
        
        return APIErrorType.UNKNOWN
    
    def _call_api(self, image_path: str, base64_image: str) -> Tuple[Optional[str], APIErrorType]:
        """调用API，返回结果和错误类型"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.key}"
        }
        
        payload = {
            "model": self.config.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": PROMPT_TEMPLATE
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 4096
        }
        
        last_error_type = APIErrorType.UNKNOWN
        
        for attempt in range(self.config.retries):
            response = None
            try:
                response = requests.post(
                    str(self.config.endpoint),
                    headers=headers,
                    json=payload,
                    timeout=self.config.timeout
                )
                
                response.raise_for_status()
                
                data = response.json()
                content = data['choices'][0]['message']['content']
                
                return content, APIErrorType.SUCCESS
            
            except requests.exceptions.Timeout as e:
                last_error_type = APIErrorType.TIMEOUT
                if attempt < self.config.retries - 1:
                    time.sleep(2 ** attempt)
                    continue
            
            except requests.exceptions.HTTPError as e:
                last_error_type = self._classify_error(e, response)
                if last_error_type == APIErrorType.AUTH_ERROR:
                    return None, last_error_type
                if last_error_type == APIErrorType.RATE_LIMIT:
                    if attempt < self.config.retries - 1:
                        time.sleep(5 * (attempt + 1))
                        continue
                if attempt < self.config.retries - 1:
                    time.sleep(2 ** attempt)
                    continue
            
            except requests.exceptions.RequestException as e:
                last_error_type = self._classify_error(e, response)
                if attempt < self.config.retries - 1:
                    time.sleep(2 ** attempt)
                    continue
            
            except Exception as e:
                last_error_type = self._classify_error(e, response)
                if attempt < self.config.retries - 1:
                    time.sleep(2 ** attempt)
                    continue
        
        return None, last_error_type
    
    def _parse_response(self, response_text: str) -> Optional[str]:
        pattern = r'```figure\n([\s\S]*?)\n```'
        match = re.search(pattern, response_text)
        
        if match:
            return match.group(1).strip()
        
        return response_text.strip() if response_text else None
    
    def describe_image(self, image_path: str) -> Tuple[Optional[str], APIErrorType]:
        """描述单张图片，返回描述和错误类型"""
        base64_image = self._encode_image(image_path)
        
        if not base64_image:
            return None, APIErrorType.UNKNOWN
        
        try:
            response, error_type = self._call_api(image_path, base64_image)
            
            if response:
                return self._parse_response(response), APIErrorType.SUCCESS
            
            return None, error_type
        
        except Exception as e:
            self.logger.log_error(image_path, str(e))
            return None, self._classify_error(e)
    
    def _process_batch_concurrent(
        self, 
        batch_items: List[Tuple[str, str]]
    ) -> Tuple[Dict[str, str], List[Tuple[str, str, APIErrorType]]]:
        """并发处理一批图片"""
        results = {}
        failures = []
        
        with ThreadPoolExecutor(max_workers=min(len(batch_items), self.config.max_concurrency)) as executor:
            futures = {
                executor.submit(self.describe_image, full_path): (rel_path, full_path)
                for rel_path, full_path in batch_items
            }
            
            for future in as_completed(futures):
                rel_path, full_path = futures[future]
                
                try:
                    description, error_type = future.result()
                    
                    if description:
                        results[rel_path] = description
                    else:
                        failures.append((rel_path, full_path, error_type))
                
                except Exception as e:
                    error_type = self._classify_error(e)
                    failures.append((rel_path, full_path, error_type))
        
        return results, failures
    
    def _process_sequential(
        self, 
        items: List[Tuple[str, str]],
        progress_offset: int = 0,
        total: int = 0
    ) -> Tuple[Dict[str, str], List[Tuple[str, str, APIErrorType]]]:
        """顺序处理图片（降级模式）"""
        results = {}
        failures = []
        
        for i, (rel_path, full_path) in enumerate(items):
            current = progress_offset + i + 1
            
            description, error_type = self.describe_image(full_path)
            
            if description:
                results[rel_path] = description
                self.logger.log_progress(current, total or len(items), rel_path, True)
            else:
                failures.append((rel_path, full_path, error_type))
                self.logger.log_progress(current, total or len(items), rel_path, False)
                
                # 检查是否是认证错误
                if error_type == APIErrorType.AUTH_ERROR:
                    print("\n❌ API认证失败，请检查API密钥配置")
                    return results, failures
        
        return results, failures
    
    def _should_fallback_to_sequential(self, failures: List[Tuple[str, str, APIErrorType]]) -> bool:
        """判断是否应该降级到顺序处理"""
        if not failures:
            return False
        
        error_types = [f[2] for f in failures]
        
        # 如果大部分是速率限制或并发错误，则降级
        concurrency_errors = sum(1 for e in error_types if e in (
            APIErrorType.RATE_LIMIT, 
            APIErrorType.CONCURRENCY_ERROR
        ))
        
        return concurrency_errors >= len(failures) * 0.5
    
    def _is_api_completely_failed(self, failures: List[Tuple[str, str, APIErrorType]]) -> bool:
        """判断API是否完全无法使用"""
        if not failures:
            return False
        
        error_types = [f[2] for f in failures]
        
        # 所有请求都是认证错误
        auth_errors = sum(1 for e in error_types if e == APIErrorType.AUTH_ERROR)
        return auth_errors == len(failures)
    
    def describe_images_batch(
        self, 
        image_paths: Dict[str, str]
    ) -> BatchResult:
        """
        批量处理图片，每批10张
        
        返回BatchResult包含:
        - results: 成功处理的描述
        - failed_paths: 处理失败的路径
        - should_fallback_sequential: 是否应降级为顺序处理
        - api_completely_failed: API是否完全失败
        """
        batch_result = BatchResult()
        total = len(image_paths)
        
        if total == 0:
            return batch_result
        
        items = list(image_paths.items())
        batch_size = DEFAULT_BATCH_SIZE
        processed = 0
        
        # 第一批尝试并发
        first_batch = items[:min(batch_size, len(items))]
        print(f"\n🚀 尝试并发处理 (批次大小: {len(first_batch)})")
        
        results, failures = self._process_batch_concurrent(first_batch)
        batch_result.results.update(results)
        processed += len(first_batch)
        
        # 更新进度
        for rel_path in results:
            self.logger.log_progress(
                len(batch_result.results), 
                total, 
                rel_path, 
                True
            )
        
        # 分析第一批结果
        if self._is_api_completely_failed(failures):
            print("\n❌ API完全无法使用，将输出原始MinerU结果")
            batch_result.api_completely_failed = True
            batch_result.failed_paths = [f[0] for f in failures]
            return batch_result
        
        if self._should_fallback_to_sequential(failures):
            print("\n⚠️ 检测到并发限制，降级为顺序处理模式")
            batch_result.should_fallback_sequential = True
            
            # 重试失败的图片（顺序模式）
            retry_items = [(f[0], f[1]) for f in failures]
            retry_results, retry_failures = self._process_sequential(
                retry_items, 
                len(batch_result.results), 
                total
            )
            batch_result.results.update(retry_results)
            
            # 处理剩余图片（顺序模式）
            remaining_items = items[processed:]
            if remaining_items:
                print(f"\n📝 顺序处理剩余 {len(remaining_items)} 张图片")
                remaining_results, remaining_failures = self._process_sequential(
                    remaining_items,
                    len(batch_result.results),
                    total
                )
                batch_result.results.update(remaining_results)
                batch_result.failed_paths.extend([f[0] for f in remaining_failures])
            
            batch_result.failed_paths.extend([f[0] for f in retry_failures])
            return batch_result
        
        # 处理第一批的失败项
        if failures:
            # 重试失败的项
            retry_items = [(f[0], f[1]) for f in failures]
            retry_results, retry_failures = self._process_sequential(
                retry_items,
                len(batch_result.results),
                total
            )
            batch_result.results.update(retry_results)
            batch_result.failed_paths.extend([f[0] for f in retry_failures])
        
        # 继续并发处理剩余批次
        while processed < len(items):
            batch_start = processed
            batch_end = min(processed + batch_size, len(items))
            batch_items = items[batch_start:batch_end]
            
            print(f"\n🚀 处理批次 {batch_start // batch_size + 2} ({len(batch_items)} 张)")
            
            results, failures = self._process_batch_concurrent(batch_items)
            batch_result.results.update(results)
            processed = batch_end
            
            # 更新进度
            for rel_path in results:
                self.logger.log_progress(
                    len(batch_result.results), 
                    total, 
                    rel_path, 
                    True
                )
            
            # 检查是否需要降级
            if self._should_fallback_to_sequential(failures):
                print("\n⚠️ 检测到并发限制，降级为顺序处理模式")
                batch_result.should_fallback_sequential = True
                
                # 重试失败的
                retry_items = [(f[0], f[1]) for f in failures]
                retry_results, retry_failures = self._process_sequential(
                    retry_items,
                    len(batch_result.results),
                    total
                )
                batch_result.results.update(retry_results)
                
                # 顺序处理剩余
                remaining_items = items[processed:]
                if remaining_items:
                    print(f"\n📝 顺序处理剩余 {len(remaining_items)} 张图片")
                    remaining_results, remaining_failures = self._process_sequential(
                        remaining_items,
                        len(batch_result.results),
                        total
                    )
                    batch_result.results.update(remaining_results)
                    batch_result.failed_paths.extend([f[0] for f in remaining_failures])
                
                batch_result.failed_paths.extend([f[0] for f in retry_failures])
                break
            
            # 重试失败的项
            if failures:
                retry_items = [(f[0], f[1]) for f in failures]
                retry_results, retry_failures = self._process_sequential(
                    retry_items,
                    len(batch_result.results),
                    total
                )
                batch_result.results.update(retry_results)
                batch_result.failed_paths.extend([f[0] for f in retry_failures])
        
        return batch_result
    
    # 保持向后兼容的简单接口
    def describe_images_batch_simple(
        self, 
        image_paths: Dict[str, str]
    ) -> Dict[str, str]:
        """简单的批量处理接口（向后兼容）"""
        result = self.describe_images_batch(image_paths)
        return result.results

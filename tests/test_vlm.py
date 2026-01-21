import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ieeU.vlm import VLMClient, APIErrorType, BatchResult
from ieeU.config import Config
from ieeU.logger import Logger


class TestAPIErrorType:
    
    def test_error_types_exist(self):
        assert APIErrorType.SUCCESS.value == "success"
        assert APIErrorType.AUTH_ERROR.value == "auth_error"
        assert APIErrorType.RATE_LIMIT.value == "rate_limit"
        assert APIErrorType.CONCURRENCY_ERROR.value == "concurrency"
        assert APIErrorType.SERVER_ERROR.value == "server_error"
        assert APIErrorType.TIMEOUT.value == "timeout"
        assert APIErrorType.NETWORK_ERROR.value == "network_error"
        assert APIErrorType.UNKNOWN.value == "unknown"


class TestBatchResult:
    
    def test_batch_result_init(self):
        result = BatchResult()
        assert result.results == {}
        assert result.failed_paths == []
        assert result.error_type is None
        assert result.should_fallback_sequential is False
        assert result.api_completely_failed is False


class TestVLMClientErrorClassification:
    
    @pytest.fixture
    def vlm_client(self):
        config = Config()
        config.endpoint = "https://api.example.com/v1/chat/completions"
        config.key = "test-key"
        config.model_name = "test-model"
        logger = Logger(verbose=False)
        return VLMClient(config, logger)
    
    def test_classify_timeout_error(self, vlm_client):
        error = requests.exceptions.Timeout()
        result = vlm_client._classify_error(error)
        assert result == APIErrorType.TIMEOUT
    
    def test_classify_connection_error(self, vlm_client):
        error = requests.exceptions.ConnectionError()
        result = vlm_client._classify_error(error)
        assert result == APIErrorType.NETWORK_ERROR
    
    def test_classify_auth_error_from_response(self, vlm_client):
        response = Mock()
        response.status_code = 401
        error = Exception("Auth failed")
        result = vlm_client._classify_error(error, response)
        assert result == APIErrorType.AUTH_ERROR
    
    def test_classify_rate_limit_from_response(self, vlm_client):
        response = Mock()
        response.status_code = 429
        error = Exception("Rate limited")
        result = vlm_client._classify_error(error, response)
        assert result == APIErrorType.RATE_LIMIT
    
    def test_classify_server_error_from_response(self, vlm_client):
        response = Mock()
        response.status_code = 500
        error = Exception("Server error")
        result = vlm_client._classify_error(error, response)
        assert result == APIErrorType.SERVER_ERROR
    
    def test_classify_concurrency_keywords(self, vlm_client):
        error = Exception("Too many concurrent requests")
        result = vlm_client._classify_error(error)
        assert result == APIErrorType.CONCURRENCY_ERROR
    
    def test_classify_unknown_error(self, vlm_client):
        error = Exception("Some random error")
        result = vlm_client._classify_error(error)
        assert result == APIErrorType.UNKNOWN


class TestVLMClientFallbackLogic:
    
    @pytest.fixture
    def vlm_client(self):
        config = Config()
        config.endpoint = "https://api.example.com/v1/chat/completions"
        config.key = "test-key"
        config.model_name = "test-model"
        logger = Logger(verbose=False)
        return VLMClient(config, logger)
    
    def test_should_fallback_empty_failures(self, vlm_client):
        result = vlm_client._should_fallback_to_sequential([])
        assert result is False
    
    def test_should_fallback_with_rate_limit_errors(self, vlm_client):
        failures = [
            ("path1", "/full/path1", APIErrorType.RATE_LIMIT),
            ("path2", "/full/path2", APIErrorType.RATE_LIMIT),
        ]
        result = vlm_client._should_fallback_to_sequential(failures)
        assert result is True
    
    def test_should_fallback_with_concurrency_errors(self, vlm_client):
        failures = [
            ("path1", "/full/path1", APIErrorType.CONCURRENCY_ERROR),
            ("path2", "/full/path2", APIErrorType.CONCURRENCY_ERROR),
        ]
        result = vlm_client._should_fallback_to_sequential(failures)
        assert result is True
    
    def test_should_not_fallback_with_auth_errors(self, vlm_client):
        failures = [
            ("path1", "/full/path1", APIErrorType.AUTH_ERROR),
            ("path2", "/full/path2", APIErrorType.AUTH_ERROR),
        ]
        result = vlm_client._should_fallback_to_sequential(failures)
        assert result is False
    
    def test_is_api_completely_failed_all_auth(self, vlm_client):
        failures = [
            ("path1", "/full/path1", APIErrorType.AUTH_ERROR),
            ("path2", "/full/path2", APIErrorType.AUTH_ERROR),
        ]
        result = vlm_client._is_api_completely_failed(failures)
        assert result is True
    
    def test_is_api_not_completely_failed_mixed(self, vlm_client):
        failures = [
            ("path1", "/full/path1", APIErrorType.AUTH_ERROR),
            ("path2", "/full/path2", APIErrorType.TIMEOUT),
        ]
        result = vlm_client._is_api_completely_failed(failures)
        assert result is False
    
    def test_is_api_not_completely_failed_empty(self, vlm_client):
        result = vlm_client._is_api_completely_failed([])
        assert result is False


class TestVLMClientBatchProcessing:
    
    @pytest.fixture
    def vlm_client(self):
        config = Config()
        config.endpoint = "https://api.example.com/v1/chat/completions"
        config.key = "test-key"
        config.model_name = "test-model"
        config.max_concurrency = 5
        config.retries = 1
        logger = Logger(verbose=False)
        return VLMClient(config, logger)
    
    def test_batch_empty_paths(self, vlm_client):
        result = vlm_client.describe_images_batch({})
        assert result.results == {}
        assert result.failed_paths == []
        assert result.api_completely_failed is False
    
    @patch.object(VLMClient, 'describe_image')
    def test_batch_all_success(self, mock_describe, vlm_client):
        mock_describe.return_value = ("Description", APIErrorType.SUCCESS)
        
        image_paths = {
            "img1.jpg": "/path/img1.jpg",
            "img2.jpg": "/path/img2.jpg",
        }
        
        result = vlm_client.describe_images_batch(image_paths)
        
        assert len(result.results) == 2
        assert result.api_completely_failed is False
        assert result.failed_paths == []
    
    @patch.object(VLMClient, 'describe_image')
    def test_batch_api_auth_failure(self, mock_describe, vlm_client):
        mock_describe.return_value = (None, APIErrorType.AUTH_ERROR)
        
        image_paths = {
            "img1.jpg": "/path/img1.jpg",
            "img2.jpg": "/path/img2.jpg",
        }
        
        result = vlm_client.describe_images_batch(image_paths)
        
        assert result.api_completely_failed is True
        assert len(result.failed_paths) == 2
    
    @patch.object(VLMClient, 'describe_image')
    def test_batch_rate_limit_fallback(self, mock_describe, vlm_client):
        call_count = [0]
        
        def side_effect(path):
            call_count[0] += 1
            if call_count[0] <= 2:
                return (None, APIErrorType.RATE_LIMIT)
            return ("Description", APIErrorType.SUCCESS)
        
        mock_describe.side_effect = side_effect
        
        image_paths = {
            "img1.jpg": "/path/img1.jpg",
            "img2.jpg": "/path/img2.jpg",
        }
        
        result = vlm_client.describe_images_batch(image_paths)
        
        assert result.should_fallback_sequential is True


class TestVLMClientSimpleInterface:
    
    @pytest.fixture
    def vlm_client(self):
        config = Config()
        config.endpoint = "https://api.example.com/v1/chat/completions"
        config.key = "test-key"
        config.model_name = "test-model"
        logger = Logger(verbose=False)
        return VLMClient(config, logger)
    
    @patch.object(VLMClient, 'describe_images_batch')
    def test_simple_interface_returns_dict(self, mock_batch, vlm_client):
        batch_result = BatchResult()
        batch_result.results = {"img.jpg": "Description"}
        mock_batch.return_value = batch_result
        
        result = vlm_client.describe_images_batch_simple({"img.jpg": "/path/img.jpg"})
        
        assert result == {"img.jpg": "Description"}

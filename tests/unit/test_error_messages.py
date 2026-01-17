"""
Unit tests for error message improvements.
"""

import pytest
from unittest.mock import Mock, patch
import httpx

from src.orchestration.model_manager import ModelManager


class TestErrorMessageImprovements:
    """Test that error messages provide helpful guidance."""
    
    @patch('src.orchestration.model_manager.httpx.Client')
    def test_model_loading_404_error_message(self, mock_client):
        """Test that 404 errors include helpful guidance."""
        # Setup mock to return 404
        mock_response = Mock()
        mock_response.status_code = 404
        
        mock_http_instance = Mock()
        mock_http_instance.post.return_value = mock_response
        mock_client.return_value = mock_http_instance
        
        manager = ModelManager(max_retries=1)  # Only 1 retry for faster test
        
        # Attempt to load a model (should fail)
        with pytest.raises(RuntimeError) as exc_info:
            manager.load_model(
                model_name="test_model",
                vram_mb=5000,
                agent_name="test_agent"
            )
        
        error_message = str(exc_info.value)
        
        # Verify error message contains helpful guidance
        assert "docker-compose up -d" in error_message
        assert "bash scripts/pull_models.sh" in error_message
        assert "Failed to load model test_model" in error_message
    
    @patch('src.orchestration.model_manager.httpx.Client')
    def test_connection_error_message(self, mock_client):
        """Test that connection errors include helpful guidance."""
        # Setup mock to raise ConnectError
        mock_http_instance = Mock()
        mock_http_instance.post.side_effect = httpx.ConnectError("Connection refused")
        mock_client.return_value = mock_http_instance
        
        manager = ModelManager(max_retries=1)  # Only 1 retry for faster test
        
        # Attempt to load a model (should fail)
        with pytest.raises(RuntimeError) as exc_info:
            manager.load_model(
                model_name="test_model",
                vram_mb=5000,
                agent_name="test_agent"
            )
        
        error_message = str(exc_info.value)
        
        # Verify error message contains helpful guidance
        assert "docker-compose up -d" in error_message
        assert "bash scripts/pull_models.sh" in error_message

"""
Unit tests for ModelManager - VRAM locking and model lifecycle.
"""

import pytest
import threading
import time
from unittest.mock import Mock, patch, MagicMock

from src.orchestration.model_manager import ModelManager, ModelInfo


class TestModelManager:
    """Test the ModelManager class."""
    
    def test_initialization(self):
        """Test ModelManager initialization."""
        manager = ModelManager(
            ollama_base_url="http://localhost:11434",
            max_concurrent_models=1,
            model_swap_timeout=30
        )
        
        assert manager.max_concurrent_models == 1
        assert manager.model_swap_timeout == 30
        assert manager.get_current_model() is None
    
    def test_max_concurrent_models_validation(self):
        """Test that max_concurrent_models must be 1."""
        with pytest.raises(ValueError):
            ModelManager(max_concurrent_models=2)
    
    def test_lock_mechanism(self):
        """Test that the lock prevents concurrent model loading."""
        manager = ModelManager()
        
        results = []
        
        def load_model_task(model_name: str):
            """Simulate loading a model."""
            try:
                # This would normally call manager.load_model()
                # For testing, we just check the lock
                with manager._lock:
                    results.append(f"start_{model_name}")
                    time.sleep(0.1)  # Simulate work
                    results.append(f"end_{model_name}")
            except Exception as e:
                results.append(f"error_{model_name}")
        
        # Start two threads trying to load models
        thread1 = threading.Thread(target=load_model_task, args=("model1",))
        thread2 = threading.Thread(target=load_model_task, args=("model2",))
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        # Verify that models were loaded sequentially (not concurrently)
        # One model should complete before the other starts
        assert len(results) == 4
        
        # Check that we don't have interleaved starts/ends
        # Either model1 completes first or model2 completes first
        model1_start = results.index("start_model1")
        model1_end = results.index("end_model1")
        model2_start = results.index("start_model2")
        model2_end = results.index("end_model2")
        
        # Ensure sequential execution
        assert (model1_end < model2_start) or (model2_end < model1_start)
    
    @patch('src.orchestration.model_manager.httpx.Client')
    def test_model_loading(self, mock_client):
        """Test model loading with mocked HTTP client."""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "test"}
        
        mock_http_instance = Mock()
        mock_http_instance.post.return_value = mock_response
        mock_client.return_value = mock_http_instance
        
        manager = ModelManager()
        
        # Load a model
        success = manager.load_model(
            model_name="test_model",
            vram_mb=5000,
            agent_name="test_agent"
        )
        
        assert success == True
        assert manager.is_model_loaded("test_model")
        assert manager.get_current_model() == "test_model"
    
    @patch('src.orchestration.model_manager.httpx.Client')
    def test_model_swap(self, mock_client):
        """Test swapping between models."""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "test"}
        
        mock_http_instance = Mock()
        mock_http_instance.post.return_value = mock_response
        mock_client.return_value = mock_http_instance
        
        manager = ModelManager()
        
        # Load first model
        manager.load_model("model1", 5000, "agent1")
        assert manager.get_current_model() == "model1"
        
        # Load second model (should unload first)
        manager.load_model("model2", 4500, "agent2")
        assert manager.get_current_model() == "model2"
        
        # Verify unload was called
        assert mock_http_instance.post.call_count >= 3  # Load1, unload1, load2
    
    def test_context_manager(self):
        """Test ModelManager as context manager."""
        with ModelManager() as manager:
            assert manager is not None
            assert manager.get_current_model() is None
        
        # After exiting context, cleanup should have been called
        # (we can't easily test this without mocking, but the structure is there)


class TestModelInfo:
    """Test the ModelInfo dataclass."""
    
    def test_model_info_creation(self):
        """Test creating ModelInfo."""
        from datetime import datetime
        
        info = ModelInfo(
            name="llama3.1:8b",
            vram_mb=5000,
            loaded_at=datetime.now(),
            agent_name="interpreter"
        )
        
        assert info.name == "llama3.1:8b"
        assert info.vram_mb == 5000
        assert info.agent_name == "interpreter"

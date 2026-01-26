"""
Model Manager - Handles VRAM locking and model lifecycle.

This module ensures only one LLM model is loaded at a time to respect
hardware constraints (6GB VRAM limit on RTX 3050).

Supports SINGLE_MODEL mode to avoid model swapping entirely.
"""

import os
import threading
import time
from typing import Optional, Dict, Any
import httpx
import logging
from dataclasses import dataclass
from datetime import datetime


logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Information about a loaded model."""
    name: str
    vram_mb: int
    loaded_at: datetime
    agent_name: str


class ModelManager:
    """
    Manages LLM model loading/unloading with strict VRAM constraints.
    
    Critical constraints:
    - Only ONE model can be loaded at a time
    - OLLAMA_KEEP_ALIVE=0 must be enforced
    - Uses threading.Lock for synchronization (not asyncio.Lock)
    
    SINGLE_MODEL mode:
    - Set SINGLE_MODEL env var to use one model for ALL agents
    - Example: SINGLE_MODEL=qwen2.5:7b-instruct-q4_K_M
    - This eliminates model swapping entirely for faster execution
    """
    
    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434",
        max_concurrent_models: int = 1,
        model_swap_timeout: int = 60,
        max_retries: int = 3
    ):
        """
        Initialize the ModelManager.
        
        Args:
            ollama_base_url: Base URL for Ollama API
            max_concurrent_models: Maximum models to load (must be 1)
            model_swap_timeout: Timeout for model swaps in seconds
            max_retries: Maximum retries for model loading
        """
        if max_concurrent_models != 1:
            raise ValueError("max_concurrent_models must be 1 for this hardware")
        
        self.ollama_base_url = ollama_base_url.rstrip('/')
        self.max_concurrent_models = max_concurrent_models
        self.model_swap_timeout = model_swap_timeout
        self.max_retries = max_retries
        
        # SINGLE_MODEL mode - use one model for all agents
        self.single_model = os.environ.get('SINGLE_MODEL', '').strip()
        self.single_model_vram = int(os.environ.get('SINGLE_MODEL_VRAM', '5000'))
        
        if self.single_model:
            logger.info(f"SINGLE_MODEL mode enabled: {self.single_model}")
            print(f"\nSINGLE MODEL MODE: {self.single_model}")
            print("   All agents will use this model - NO swapping required!")
        
        # Critical: Only one model at a time
        self._lock = threading.Lock()
        self._current_model: Optional[ModelInfo] = None
        
        # Enforce OLLAMA_KEEP_ALIVE=0
        os.environ['OLLAMA_KEEP_ALIVE'] = '0'
        
        self._client = httpx.Client(timeout=httpx.Timeout(300.0))
        
        logger.info("ModelManager initialized with max_concurrent_models=1")
    
    def is_model_loaded(self, model_name: str) -> bool:
        """
        Check if a specific model is currently loaded.
        
        Args:
            model_name: Name of the model to check
        
        Returns:
            True if the model is loaded
        """
        with self._lock:
            return (
                self._current_model is not None 
                and self._current_model.name == model_name
            )
    
    def get_current_model(self) -> Optional[str]:
        """Get the name of the currently loaded model."""
        with self._lock:
            return self._current_model.name if self._current_model else None
    
    def unload_model(self, force: bool = False) -> bool:
        """
        Unload the currently loaded model.
        
        Args:
            force: Force unload even if it fails
        
        Returns:
            True if successful
        """
        with self._lock:
            if self._current_model is None:
                logger.debug("No model currently loaded")
                return True
            
            model_name = self._current_model.name
            logger.info(f"Unloading model: {model_name}")
            
            try:
                # Tell Ollama to unload the model
                # With OLLAMA_KEEP_ALIVE=0, this happens automatically,
                # but we can be explicit
                response = self._client.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": "",
                        "keep_alive": 0
                    }
                )
                
                if response.status_code == 200 or force:
                    self._current_model = None
                    logger.info(f"Model {model_name} unloaded successfully")
                    return True
                else:
                    logger.warning(
                        f"Failed to unload model {model_name}: "
                        f"Status {response.status_code}"
                    )
                    if force:
                        self._current_model = None
                    return force
                    
            except Exception as e:
                logger.error(f"Error unloading model {model_name}: {e}")
                if force:
                    self._current_model = None
                    return True
                return False
    
    def load_model(
        self,
        model_name: str,
        vram_mb: int,
        agent_name: str
    ) -> bool:
        """
        Load a model, unloading any existing model first.
        
        Args:
            model_name: Name of the model to load (e.g., 'llama3.1:8b-instruct-q4_K_M')
            vram_mb: Expected VRAM usage in MB
            agent_name: Name of the agent requesting the model
        
        Returns:
            True if successful
        
        Raises:
            TimeoutError: If model swap takes too long
            RuntimeError: If model loading fails after retries
        """
        with self._lock:
            # If the same model is already loaded, we're done
            if (
                self._current_model is not None 
                and self._current_model.name == model_name
            ):
                logger.debug(f"Model {model_name} already loaded")
                return True
            
            # Unload current model if any
            if self._current_model is not None:
                logger.info(
                    f"Swapping model: {self._current_model.name} -> {model_name}"
                )
                if not self.unload_model(force=True):
                    logger.warning("Failed to cleanly unload previous model")
                
                # Give Ollama time to free VRAM
                print("   [*] Step 1/3: Freeing VRAM...")
                time.sleep(2)
                print("   [OK] VRAM freed")
            
            # Load the new model
            logger.info(f"Loading model: {model_name} for agent: {agent_name}")
            print(f"\n[>>] Loading Model: {model_name}")
            print(f"   Agent: {agent_name}")
            
            for attempt in range(self.max_retries):
                try:
                    print(f"   [*] Step 2/3: Allocating resources (attempt {attempt + 1})...")
                    start_time = time.time()
                    
                    # Make a test request to load the model
                    print("   [*] Step 3/3: Initializing model...")
                    response = self._client.post(
                        f"{self.ollama_base_url}/api/generate",
                        json={
                            "model": model_name,
                            "prompt": "test",
                            "stream": False,
                            "keep_alive": 0
                        },
                        timeout=httpx.Timeout(self.model_swap_timeout * 2)
                    )
                    
                    elapsed = time.time() - start_time
                    
                    if response.status_code == 200:
                        self._current_model = ModelInfo(
                            name=model_name,
                            vram_mb=vram_mb,
                            loaded_at=datetime.now(),
                            agent_name=agent_name
                        )
                        print(f"   [OK] Model loaded successfully in {elapsed:.1f}s!")
                        logger.info(
                            f"Model {model_name} loaded successfully "
                            f"in {elapsed:.1f}s (attempt {attempt + 1})"
                        )
                        return True
                    else:
                        error_msg = (
                            f"Failed to load model {model_name}: "
                            f"Status {response.status_code} (attempt {attempt + 1})"
                        )
                        if response.status_code == 404:
                            error_msg += (
                                f"\n  → Model not found. This usually means:"
                                f"\n    1. Ollama service is not running - run: docker-compose up -d"
                                f"\n    2. Model '{model_name}' is not downloaded - run: bash scripts/pull_models.sh"
                            )
                        logger.warning(error_msg)
                        
                except httpx.TimeoutException:
                    logger.warning(
                        f"Timeout loading model {model_name} (attempt {attempt + 1})"
                        f"\n  → Check if Ollama service is running: docker-compose up -d"
                    )
                    
                except httpx.ConnectError as e:
                    logger.error(
                        f"Cannot connect to Ollama at {self.ollama_base_url} (attempt {attempt + 1})"
                        f"\n  → Ollama service is not running. Start it with: docker-compose up -d"
                    )
                    
                except Exception as e:
                    logger.error(
                        f"Error loading model {model_name}: {e} (attempt {attempt + 1})"
                    )
                
                # Wait before retrying
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
            
            raise RuntimeError(
                f"Failed to load model {model_name} after {self.max_retries} attempts. "
                f"Please check:\n"
                f"  1. Is Ollama running? → docker-compose up -d\n"
                f"  2. Is model downloaded? → bash scripts/pull_models.sh\n"
                f"  3. Can you access {self.ollama_base_url}?"
            )
    
    def generate(
        self,
        model_name: str,
        prompt: str,
        vram_mb: int,
        agent_name: str,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate text with a model, handling loading/unloading.
        
        Args:
            model_name: Name of the model (may be overridden by SINGLE_MODEL)
            prompt: Prompt to send to the model
            vram_mb: Expected VRAM usage
            agent_name: Name of the requesting agent
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            Generated text
        """
        # SINGLE_MODEL mode: override the requested model
        if self.single_model:
            effective_model = self.single_model
            effective_vram = self.single_model_vram
            if model_name != effective_model:
                logger.debug(
                    f"SINGLE_MODEL mode: Using {effective_model} instead of {model_name}"
                )
        else:
            effective_model = model_name
            effective_vram = vram_mb
        
        # Ensure model is loaded
        self.load_model(effective_model, effective_vram, agent_name)
        
        logger.debug(f"Generating with model {effective_model}")
        
        try:
            # Realistic tokens for quality responses
            # Balance depth with feasibility for 7B-14B models
            effective_max_tokens = max_tokens if max_tokens else 4096
            
            request_data = {
                "model": effective_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": min(effective_max_tokens, 4096),  # Cap at 4K for reliability
                    "num_ctx": 16384,  # Balanced context window
                    "repeat_penalty": 1.15,  # Stronger penalty against repetition
                    "top_k": 40,  # Diverse vocabulary selection
                    "top_p": 0.95,  # Nucleus sampling for quality
                }
            }
            
            # Use longer timeout for detailed generation (30 min)
            response = self._client.post(
                f"{self.ollama_base_url}/api/generate",
                json=request_data,
                timeout=httpx.Timeout(1800.0)  # 30 min timeout for detailed content
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result.get("response", "")
            
        except Exception as e:
            logger.error(f"Error generating with model {effective_model}: {e}")
            raise
    
    def cleanup(self):
        """Cleanup resources and unload models."""
        logger.info("Cleaning up ModelManager")
        self.unload_model(force=True)
        self._client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()

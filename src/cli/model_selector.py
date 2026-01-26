"""
Model Selector - Interactive model selection for single-model mode.
"""

import urllib.request
import urllib.error
import json
from typing import Optional, List, Dict, Any


def get_available_models(ollama_url: str = "http://localhost:11434") -> List[Dict[str, Any]]:
    """
    Fetch available models from Ollama.
    
    Args:
        ollama_url: Ollama base URL
    
    Returns:
        List of model dictionaries
    """
    try:
        req = urllib.request.Request(f"{ollama_url}/api/tags", method='GET')
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read())
            return data.get('models', [])
    except Exception as e:
        print(f"Error fetching models: {e}")
        return []


def format_model_size(size_bytes: int) -> str:
    """
    Format model size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        Formatted size string
    """
    gb = size_bytes / (1024 ** 3)
    return f"{gb:.1f} GB"


def display_model_menu(models: List[Dict[str, Any]]) -> None:
    """
    Display interactive model selection menu.
    
    Args:
        models: List of available models
    """
    print("\n" + "=" * 70)
    print("  SINGLE MODEL MODE - Model Selection")
    print("=" * 70)
    print("\nAvailable models:")
    print()
    
    # Filter and sort models by size
    sorted_models = sorted(models, key=lambda m: m.get('size', 0))
    
    for idx, model in enumerate(sorted_models, 1):
        name = model.get('name', 'unknown')
        size = format_model_size(model.get('size', 0))
        
        # Add quality indicator based on size
        if 'size' in model:
            size_gb = model['size'] / (1024 ** 3)
            if size_gb < 3:
                quality = "⭐⭐ (Fast, Basic)"
            elif size_gb < 6:
                quality = "⭐⭐⭐ (Balanced)"
            elif size_gb < 8:
                quality = "⭐⭐⭐⭐ (High Quality)"
            else:
                quality = "⭐⭐⭐⭐⭐ (Best Quality)"
        else:
            quality = ""
        
        print(f"  [{idx}] {name}")
        print(f"      Size: {size} | {quality}")
        print()
    
    print("=" * 70)


def select_model_interactive(ollama_url: str = "http://localhost:11434") -> Optional[str]:
    """
    Interactively select a model for single-model mode.
    
    Args:
        ollama_url: Ollama base URL
    
    Returns:
        Selected model name or None if cancelled
    """
    models = get_available_models(ollama_url)
    
    if not models:
        print("\n⚠ No models found in Ollama.")
        print("Please download models first using: bash scripts/pull_models.sh")
        return None
    
    # Display menu
    display_model_menu(models)
    
    print("\n💡 Recommendation: Choose a 7B model (balanced speed/quality)")
    print("   Examples: qwen2.5:7b, mistral:7b, llama3.1:8b")
    print()
    
    # Get user selection
    while True:
        try:
            selection = input("Enter model number (or 'q' to quit): ").strip()
            
            if selection.lower() == 'q':
                print("Cancelled.")
                return None
            
            idx = int(selection)
            
            if 1 <= idx <= len(models):
                selected_model = models[idx - 1]['name']
                
                # Confirm selection
                print(f"\n✓ Selected: {selected_model}")
                confirm = input("Continue with this model? [Y/n]: ").strip().lower()
                
                if confirm in ['', 'y', 'yes']:
                    return selected_model
                else:
                    continue
            else:
                print(f"Invalid selection. Please enter 1-{len(models)}")
                
        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\n\nCancelled.")
            return None


def get_recommended_models() -> List[str]:
    """
    Get list of recommended models for single-model mode.
    
    Returns:
        List of recommended model names
    """
    return [
        "qwen2.5:7b-instruct-q4_K_M",  # Balanced, good quality
        "mistral:7b-instruct",          # Fast, good reasoning
        "llama3.1:8b-instruct-q4_K_M",  # Good overall performance
        "phi3.5:3.8b-mini-instruct-q4_K_M",  # Fastest, smaller
    ]

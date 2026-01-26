#!/usr/bin/env python3
"""
ZenKnowledgeForge Diagnostic Script

Checks system prerequisites and identifies configuration issues.
Run this before executing the main application to catch problems early.
"""

import subprocess
import sys
import json
from pathlib import Path
import urllib.request
import urllib.error

def print_header(text):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print('=' * 60)

def print_status(label, status, message=""):
    """Print a status line with color."""
    if status == "OK":
        status_text = "✓ OK"
    elif status == "WARNING":
        status_text = "⚠ WARNING"
    else:
        status_text = "✗ FAIL"
    
    print(f"{label:.<40} {status_text}")
    if message:
        print(f"  → {message}")

def check_docker():
    """Check if Docker is running."""
    print_header("Docker Service Check")
    
    try:
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print_status("Docker service", "OK")
            return True
        else:
            print_status("Docker service", "FAIL", "Docker is not running")
            return False
            
    except FileNotFoundError:
        print_status("Docker installation", "FAIL", "Docker not found in PATH")
        return False
    except subprocess.TimeoutExpired:
        print_status("Docker service", "FAIL", "Docker command timeout")
        return False
    except Exception as e:
        print_status("Docker service", "FAIL", str(e))
        return False

def check_docker_compose():
    """Check if docker-compose services are running."""
    print_header("Docker Compose Services")
    
    try:
        result = subprocess.run(
            ["docker-compose", "ps"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if "ollama" in result.stdout:
            if "Up" in result.stdout:
                print_status("Ollama container", "OK")
            else:
                print_status("Ollama container", "WARNING", "Container exists but may not be running")
        else:
            print_status("Ollama container", "FAIL", "Not found - run 'docker-compose up -d'")
        
        if "neo4j" in result.stdout:
            if "Up" in result.stdout:
                print_status("Neo4j container", "OK")
            else:
                print_status("Neo4j container", "WARNING", "Container exists but may not be running")
        else:
            print_status("Neo4j container", "WARNING", "Not found (optional for v0.1.0)")
            
    except Exception as e:
        print_status("Docker Compose", "FAIL", str(e))

def check_ollama():
    """Check if Ollama is accessible."""
    print_header("Ollama Service Check")
    
    ollama_url = "http://localhost:11434/api/tags"
    
    try:
        req = urllib.request.Request(ollama_url, method='GET')
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read())
            
            print_status("Ollama API", "OK", f"Connected to {ollama_url}")
            
            if 'models' in data:
                models = data['models']
                print(f"\n  Downloaded models: {len(models)}")
                
                # Check for required models
                required_models = [
                    "llama3.1:8b-instruct-q4_K_M",
                    "mistral:7b-instruct",
                    "qwen2.5:7b-instruct-q4_K_M",
                    "gemma2:9b-instruct-q4_K_M",
                    "phi3.5:3.8b-mini-instruct-q4_K_M"
                ]
                
                model_names = [m['name'] for m in models]
                
                for req_model in required_models:
                    if req_model in model_names:
                        print(f"    ✓ {req_model}")
                    else:
                        print(f"    ✗ {req_model} - MISSING")
                
                return True
            else:
                print_status("Ollama models", "WARNING", "No models found")
                return False
                
    except urllib.error.URLError as e:
        print_status("Ollama API", "FAIL", f"Cannot connect - {e.reason}")
        print("  → Make sure Ollama is running: docker-compose up -d")
        return False
    except Exception as e:
        print_status("Ollama API", "FAIL", str(e))
        return False

def check_vram_config():
    """Check VRAM configuration."""
    print_header("Hardware Configuration Check")
    
    config_file = Path("config/agents.yaml")
    
    if not config_file.exists():
        print_status("agents.yaml", "FAIL", "Configuration file not found")
        return False
    
    try:
        import yaml
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        agents = config.get('agents', {})
        max_vram = 6000  # RTX 3050 limit
        
        issues = []
        
        for agent_name, agent_config in agents.items():
            vram_mb = agent_config.get('vram_mb', 0)
            model = agent_config.get('model', 'unknown')
            
            status = "OK" if vram_mb <= max_vram else "FAIL"
            print_status(
                f"{agent_name} ({vram_mb}MB)",
                status,
                model if status == "OK" else f"{model} - EXCEEDS 6GB LIMIT!"
            )
            
            if vram_mb > max_vram:
                issues.append(f"{agent_name}: {vram_mb}MB > {max_vram}MB")
        
        if issues:
            print("\n  ⚠ VRAM CONSTRAINT VIOLATIONS:")
            for issue in issues:
                print(f"    • {issue}")
            print("\n  Fix: Edit config/agents.yaml to use smaller models")
            return False
        else:
            print("\n  ✓ All agents fit within 6GB VRAM limit")
            return True
            
    except ImportError:
        print_status("PyYAML", "WARNING", "Install with: pip install pyyaml")
        return True
    except Exception as e:
        print_status("Config validation", "FAIL", str(e))
        return False

def check_python_deps():
    """Check if required Python packages are installed."""
    print_header("Python Dependencies")
    
    required = [
        "pydantic",
        "yaml",
        "httpx",
        "rich",
        "jinja2",
        "dotenv"
    ]
    
    all_ok = True
    
    for package in required:
        try:
            if package == "yaml":
                __import__("yaml")
            elif package == "dotenv":
                __import__("dotenv")
            else:
                __import__(package)
            print_status(package, "OK")
        except ImportError:
            print_status(package, "FAIL", "Not installed")
            all_ok = False
    
    if not all_ok:
        print("\n  Fix: pip install pydantic pyyaml httpx rich jinja2 python-dotenv")
    
    return all_ok

def main():
    """Run all diagnostic checks."""
    print("""
╔══════════════════════════════════════════════════════════╗
║  ZenKnowledgeForge - System Diagnostic                   ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    checks = [
        ("Python Dependencies", check_python_deps),
        ("Docker", check_docker),
        ("Docker Compose", check_docker_compose),
        ("Ollama", check_ollama),
        ("VRAM Config", check_vram_config)
    ]
    
    results = {}
    
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n✗ {name} check failed: {e}")
            results[name] = False
    
    # Summary
    print_header("Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    
    if all(results.values()):
        print("\n✓ All checks passed! Ready to run ZenKnowledgeForge.")
        return 0
    else:
        print("\n✗ Some checks failed. Fix the issues above before running.")
        print("\nQuick fix commands:")
        
        if not results.get("Docker", True):
            print("  • Start Docker Desktop")
        
        if not results.get("Ollama", True):
            print("  • docker-compose up -d")
            print("  • bash scripts/pull_models.sh  (download models)")
        
        if not results.get("VRAM Config", True):
            print("  • Edit config/agents.yaml - replace 14B models with 7B")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())

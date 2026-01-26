"""Test web search directly"""
import sys
import logging
sys.path.insert(0, '.')

# Enable DEBUG logging to see what's happening
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')

from src.tools.web_search import CachedWebSearch

print("Initializing web search...")
web_search = CachedWebSearch()

print("\nSearching for 'What is machine learning?'...")
try:
    results = web_search.search("What is machine learning?", max_results=5)
    print(f"\n[OK] Found {len(results)} results")
    
    for idx, result in enumerate(results, 1):
        print(f"\n[{idx}] {result.get('title', 'No title')}")
        print(f"    URL: {result.get('url', 'No URL')}")
        print(f"    Snippet: {result.get('snippet', 'No snippet')[:100]}...")
        if result.get('content'):
            print(f"    Content length: {len(result.get('content', ''))} chars")
except Exception as e:
    print(f"\n[ERROR] Search failed: {e}")
    import traceback
    traceback.print_exc()
try:
    results = web_search.search("What is machine learning?", max_results=5)
    print(f"\n[OK] Found {len(results)} results")
    
    for idx, result in enumerate(results, 1):
        print(f"\n[{idx}] {result.get('title', 'No title')}")
        print(f"    URL: {result.get('url', 'No URL')}")
        print(f"    Snippet: {result.get('snippet', 'No snippet')[:100]}...")
        if result.get('content'):
            print(f"    Content length: {len(result.get('content', ''))} chars")
except Exception as e:
    print(f"\n[ERROR] Search failed: {e}")
    import traceback
    traceback.print_exc()

"""
Test script to verify evidence retrieval works
"""
import sys
sys.path.insert(0, '.')

from src.agents.grounder import GrounderAgent
from src.orchestration.state import SharedState, ExecutionMode

# Create a minimal state
state = SharedState(
    user_brief="Test query: What is machine learning?",
    execution_mode=ExecutionMode.RESEARCH
)
state.plan = {
    "research_questions": [
        {
            "id": "RQ1",
            "question": "What is machine learning?",
            "type": "definition"
        }
    ]
}

# Initialize grounder
print("Initializing Grounder...")
grounder = GrounderAgent()

# Test evidence retrieval
print("\nTesting _retrieve_evidence()...")
try:
    evidence = grounder._retrieve_evidence(state.plan["research_questions"])
    print(f"\n[OK] Evidence retrieval successful!")
    print(f"Retrieved evidence for {len(evidence)} questions")
    
    for rq_id, sources in evidence.items():
        print(f"\n{rq_id}: {len(sources)} sources")
        for idx, source in enumerate(sources[:3], 1):  # Show first 3
            print(f"  [{idx}] {source.get('title', 'No title')[:60]}")
            if source.get('url'):
                print(f"      URL: {source['url']}")
            if source.get('content'):
                print(f"      Content: {source['content'][:100]}...")
except Exception as e:
    print(f"\n[ERROR] Evidence retrieval failed: {e}")
    import traceback
    traceback.print_exc()

print("\n[OK] Test complete!")

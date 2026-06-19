import os
import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Any

# Ensure project path is accessible
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src import config

def contains_sensitive_keywords(query: str) -> bool:
    """Checks if the query contains any of the preconfigured sensitive keywords."""
    query_lower = query.lower()
    for kw in config.SENSITIVE_KEYWORDS:
        # Use word boundary matching to avoid matching substrings (e.g., 'sue' in 'issue')
        pattern = r'\b' + re.escape(kw) + r'\b'
        if re.search(pattern, query_lower):
            return True
    return False

def contains_human_agent_request(query: str) -> bool:
    """Checks if the user is explicitly requesting a human agent."""
    query_lower = query.lower()
    phrases = [
        "human support", "live agent", "real person", "talk to human", "speak to human",
        "live representative", "customer service representative", "talk to a manager",
        "speak to a manager", "transfer to human", "connect to human", "talk to a person",
        "operator", "chat with a person", "connect me to a representative"
    ]
    for phrase in phrases:
        if phrase in query_lower:
            return True
    return False

def check_consecutive_frustration(conversation_history: List[Dict[str, str]]) -> bool:
    """Checks if the user has been classified as Frustrated across multiple turns.
    
    If the conversation history contains metadata about detected personas, we can check them.
    Otherwise, we can run a quick heuristic check on the message contents in history.
    """
    if not conversation_history:
        return False
        
    frustrated_turns = 0
    # Search backwards through user turns
    user_turns = [turn for turn in conversation_history if turn.get("role") == "user"]
    
    for turn in reversed(user_turns):
        content = turn.get("content", "").lower()
        # Heuristics for negative sentiment/frustration
        is_frustrated = (
            turn.get("persona") == "Frustrated User" or
            "!" in content or
            "not working" in content or
            "broken" in content or
            "useless" in content or
            "terrible" in content or
            "still" in content or  # e.g., "still not working"
            "tried that" in content or
            "already done" in content
        )
        if is_frustrated:
            frustrated_turns += 1
        else:
            # Reset if there's a non-frustrated turn
            break
            
    return frustrated_turns >= config.MAX_CONVERSATION_TURNS

def check_escalation(
    user_query: str,
    persona: str,
    conversation_history: List[Dict[str, str]],
    retrieved_chunks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Analyzes the current interaction and conversation history to determine if human handoff is needed.
    
    Returns:
        dict: {
            "escalate": bool,
            "reason": str or None,
            "handoff_summary": str or None
        }
    """
    # Trigger 1: Explicit request for a human
    if contains_human_agent_request(user_query):
        summary = generate_handoff_report(
            user_query, persona, conversation_history, retrieved_chunks, 
            reason="User explicitly requested a human support agent."
        )
        return {
            "escalate": True,
            "reason": "Direct human support request",
            "handoff_summary": summary
        }
        
    # Trigger 2: Sensitive keywords (billing, legal, refunds, account deletion)
    if contains_sensitive_keywords(user_query):
        summary = generate_handoff_report(
            user_query, persona, conversation_history, retrieved_chunks, 
            reason="Query contains billing, financial, legal, or account-sensitive keywords."
        )
        return {
            "escalate": True,
            "reason": "Sensitive account or billing issue",
            "handoff_summary": summary
        }
        
    # Trigger 3: Low retrieval confidence (cosine similarity below threshold)
    best_score = max([chunk["score"] for chunk in retrieved_chunks]) if retrieved_chunks else 0.0
    if best_score < config.SIMILARITY_THRESHOLD or len(retrieved_chunks) == 0:
        summary = generate_handoff_report(
            user_query, persona, conversation_history, retrieved_chunks, 
            reason=f"Retrieval confidence ({best_score}) is below threshold ({config.SIMILARITY_THRESHOLD}) or zero context was found."
        )
        return {
            "escalate": True,
            "reason": "Unresolved issue (Low documentation similarity)",
            "handoff_summary": summary
        }
        
    # Trigger 4: Persistent frustration over multiple turns
    if check_consecutive_frustration(conversation_history):
        summary = generate_handoff_report(
            user_query, persona, conversation_history, retrieved_chunks, 
            reason=f"User has expressed unresolved frustration across {config.MAX_CONVERSATION_TURNS}+ consecutive messages."
        )
        return {
            "escalate": True,
            "reason": "Persistent user frustration",
            "handoff_summary": summary
        }
        
    return {
        "escalate": False,
        "reason": None,
        "handoff_summary": None
    }

def generate_handoff_report(
    user_query: str,
    persona: str,
    conversation_history: List[Dict[str, str]],
    retrieved_chunks: List[Dict[str, Any]],
    reason: str
) -> str:
    """Compiles a clean, structured JSON and markdown handoff summary report."""
    
    # Extract actions attempted from history
    attempted = []
    if conversation_history:
        for turn in conversation_history:
            if turn.get("role") == "user":
                content = turn["content"].lower()
                if "tried" in content or "did" in content or "attempted" in content or "done" in content:
                    attempted.append(turn["content"])
                    
    if not attempted:
        attempted = ["Described issue in chat, but no specific troubleshooting actions were logged."]
        
    # Build clean history transcription
    transcript = []
    if conversation_history:
        for turn in conversation_history:
            role = "Customer" if turn.get("role") == "user" else "AI Agent"
            transcript.append(f"{role}: {turn.get('content')}")
    transcript.append(f"Customer (Current): {user_query}")
    
    handoff_dict = {
        "escalation_reason": reason,
        "customer_persona": persona,
        "core_issue_summary": user_query[:150] + ("..." if len(user_query) > 150 else ""),
        "retrieved_documents_used": list(set([c["source"] for c in retrieved_chunks])) if retrieved_chunks else [],
        "highest_retrieved_similarity": max([c["score"] for c in retrieved_chunks]) if retrieved_chunks else 0.0,
        "actions_attempted_by_user": attempted,
        "recommended_next_steps": [
            "Review transaction logs, payment method state, or database connections.",
            "Verify customer credentials and account flag states in the administration panel.",
            "Contact user directly to guide them through custom resolution."
        ],
        "conversation_transcript": transcript
    }
    
    return json.dumps(handoff_dict, indent=2)

if __name__ == "__main__":
    # Test cases
    print("Testing Escalator Module:")
    
    # Test Case 1: Sensitive issue
    res1 = check_escalation(
        "I demand an immediate refund for my duplicate charges!",
        "Frustrated User",
        [],
        [{"score": 0.85, "source": "billing_policy.txt", "text": "Refund details..."}]
    )
    print(f"\nDuplicate charges query - Escalate: {res1['escalate']}")
    print(f"Reason: {res1['reason']}")
    print(f"Report:\n{res1['handoff_summary']}")
    
    # Test Case 2: Human support request
    res2 = check_escalation(
        "Can you transfer me to a live agent please?",
        "Business Executive",
        [],
        [{"score": 0.90, "source": "payout_schedules.md", "text": "Payout details..."}]
    )
    print(f"\nLive agent request - Escalate: {res2['escalate']}")
    print(f"Reason: {res2['reason']}")
    
    # Test Case 3: Normal query
    res3 = check_escalation(
        "How do I set my bearer token auth header?",
        "Technical Expert",
        [],
        [{"score": 0.85, "source": "api_troubleshooting.md", "text": "Auth details..."}]
    )
    print(f"\nNormal API query - Escalate: {res3['escalate']}")

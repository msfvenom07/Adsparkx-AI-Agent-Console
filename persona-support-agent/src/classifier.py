import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types

# Ensure project path is accessible
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src import config

def rule_based_classify(user_message: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    """Fallback classifier that uses regex and keyword matching when LLM is unavailable."""
    msg_lower = user_message.lower()
    
    # Keyword scores
    tech_score = 0
    frustrated_score = 0
    exec_score = 0
    
    # 1. Technical Expert indicators (using exact word boundaries)
    tech_keywords = [
        "api", "keys?", "auth", "tokens?", "bearer", "headers?", "parameters?", "curl", 
        "post", "get", "endpoints?", "webhooks?", "signatures?", "payloads?", "json", 
        "tls", "ssl", "status codes?", "401", "403", "429", "500", "errors?", "sdks?", 
        "integrations?", "developers?", "databases?", "latency", "responses?", "requests?", 
        "hosts?", "ports?", "uuid", "configs?", "configurations?"
    ]
    
    for kw in tech_keywords:
        pattern = r'\b' + kw + r'\b'
        if re.search(pattern, msg_lower):
            tech_score += 2
            
    # Check for "log" as a technical term, but exclude general actions like "login"/"log in"/"log out"
    if re.search(r'\blogs?\b', msg_lower):
        if not any(action in msg_lower for action in ["log in", "login", "log out", "logout", "logging in"]):
            tech_score += 2
            
    # 2. Frustrated User indicators (using exact word boundaries)
    frustrated_keywords = [
        "worst", "terrible", "useless", "broken", "nothing works", "down", "freezes?", "locks?", 
        "stolen", "unauthorized", "scams?", "frauds?", "sue", "legal", "courts?", "billing", 
        "refunds?", "chargebacks?", "urgent", "immediate", "asap", "disappointed", "angry", 
        "hate", "fails?", "errors?", "delays?", "waiting", "forever", "locked out", "complaints?",
        "garbage", "horrible", "annoyed", "frustrated"
    ]
    
    for kw in frustrated_keywords:
        pattern = r'\b' + kw + r'\b'
        if re.search(pattern, msg_lower):
            frustrated_score += 2
            
    # Exclamation marks and question marks increase frustration score slightly
    frustrated_score += user_message.count("!") * 2
    frustrated_score += user_message.count("?") * 0.5
    
    # Check for words in all caps (length > 2)
    words = user_message.split()
    caps_words = [w for w in words if w.isupper() and len(w) > 2]
    frustrated_score += len(caps_words) * 3

    # 3. Business Executive indicators (using exact word boundaries)
    exec_keywords = [
        "timelines?", "resolutions?", "sla", "business", "impacts?", "operations?", "costs?", 
        "pricing", "revenues?", "fees?", "enterprise", "agreements?", "contracts?", "uptime", 
        "roi", "volumes?", "sales", "commercial", "loss", "clients?", "customer satisfaction", 
        "payouts?", "settlements?", "operational"
    ]
    
    for kw in exec_keywords:
        pattern = r'\b' + kw + r'\b'
        if re.search(pattern, msg_lower):
            exec_score += 2
            
    # Brevity check (executives prefer concise messages)
    if len(words) < 15 and exec_score > 0:
        exec_score += 2
        
    # 4. Integrate conversation history bias to maintain context continuity
    if conversation_history:
        user_turns = [turn for turn in conversation_history if turn.get("role") == "user"]
        if user_turns:
            last_user_turn = user_turns[-1]
            last_persona = last_user_turn.get("persona")
            if last_persona == "Frustrated User":
                frustrated_score += 1.5
            elif last_persona == "Technical Expert":
                tech_score += 1.0
            elif last_persona == "Business Executive":
                exec_score += 1.0
        
    # Determine the winner
    scores = {
        "Technical Expert": tech_score,
        "Frustrated User": frustrated_score,
        "Business Executive": exec_score
    }
    
    max_persona = max(scores, key=scores.get)
    max_score = scores[max_persona]
    
    # Calculate confidence
    total_score = sum(scores.values())
    if total_score == 0:
        persona = "Business Executive" if len(words) < 12 else "Frustrated User" # Default heuristic
        confidence = 0.50
        reasoning = "Default classification due to neutral query with zero matching keywords."
    else:
        persona = max_persona
        confidence = round(max_score / total_score, 2)
        # Ensure confidence is within a reasonable range (0.5 to 0.85) for rule-based
        confidence = max(0.5, min(0.85, confidence))
        
        reasoning = f"Rule-based classification. Matching scores - Tech: {tech_score}, Frustrated: {frustrated_score}, Exec: {exec_score}."
        
    return {
        "persona": persona,
        "confidence": confidence,
        "reasoning": reasoning
    }

def classify_customer_persona(user_message: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    """Analyzes the user's message and classifies it into one of the three target personas.
    
    If the GEMINI_API_KEY is not set or the API call fails, it falls back to a rule-based classifier.
    """
    api_key = config.GEMINI_API_KEY
    if not api_key:
        return rule_based_classify(user_message, conversation_history)
        
    try:
        # Initialize Gemini Client
        client = genai.Client(api_key=api_key)
        
        system_instruction = (
            "You are an advanced classification engine. Your task is to analyze the "
            "sentiment, vocabulary, and tone of an incoming support message and classify "
            "it into exactly one of three customer personas:\n"
            "1. 'Technical Expert': Uses jargon, asks about APIs/code/configs.\n"
            "2. 'Frustrated User': Uses emotional language, exclamation marks, or mentions urgency.\n"
            "3. 'Business Executive': Focuses on business impact, ROI, timelines, and brevity.\n\n"
            "Provide your evaluation strictly in the requested JSON structure."
        )
        
        response_schema = {
            "type": "OBJECT",
            "properties": {
                "persona": {
                    "type": "STRING",
                    "enum": ["Technical Expert", "Frustrated User", "Business Executive"]
                },
                "confidence": {"type": "NUMBER"},
                "reasoning": {"type": "STRING"}
            },
            "required": ["persona", "confidence", "reasoning"]
        }
        
        # Compile conversation history if present for context-aware classification
        contents_input = []
        if conversation_history:
            for turn in conversation_history:
                role = "Customer" if turn.get("role") == "user" else "Support Agent"
                contents_input.append(f"{role}: {turn.get('content')}")
        contents_input.append(f"Customer (Current Message): {user_message}")
        user_input_compiled = "\n".join(contents_input)
        
        response = client.models.generate_content(
            model=config.DEFAULT_CLASSIFIER_MODEL,
            contents=user_input_compiled,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0.1
            )
        )
        
        return json.loads(response.text)
        
    except Exception as e:
        print(f"Gemini persona classification failed: {e}. Falling back to rule-based classification.")
        return rule_based_classify(user_message, conversation_history)

if __name__ == "__main__":
    # Test cases
    test_queries = [
        "What are the header parameter requirements for your bearer token auth implementation?",
        "Where is the guide to clear cookies? It's been an hour and nothing is loading on your interface!",
        "Our operational uptime is decreasing. We need a timeline of when billing disputes are resolved.",
        "My billing statement has unexpected duplicate charges. I demand an immediate refund!",
        "I cannot log in to my admin profile. How long does the account lockout last?"
    ]
    
    print("Testing Persona Classifier (Rule-based Fallback Active):")
    for q in test_queries:
        result = classify_customer_persona(q)
        print(f"\nQuery: '{q}'")
        print(f"Detected: {result['persona']} (Confidence: {result['confidence']})")
        print(f"Reasoning: {result['reasoning']}")

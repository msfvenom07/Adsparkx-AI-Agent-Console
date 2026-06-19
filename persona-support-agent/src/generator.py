import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types

# Ensure project path is accessible
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src import config

def generate_handoff_summary(user_query: str, persona: str, context_chunks: List[Dict[str, Any]], conversation_history: List[Dict[str, str]] = None) -> str:
    """Compiles detailed, structured JSON handoff data for an escalating support ticket."""
    history = conversation_history or []
    
    # Analyze conversation history to extract actions attempted
    attempted_actions = []
    for turn in history:
        if turn["role"] == "user":
            lower_msg = turn["content"].lower()
            if "tried" in lower_msg or "attempted" in lower_msg or "did" in lower_msg:
                # Simple extraction of what they did
                attempted_actions.append(turn["content"])
                
    if not attempted_actions:
        attempted_actions = ["User described the problem in chat."]
        
    handoff_data = {
        "persona": persona,
        "detected_issue": user_query[:150] + ("..." if len(user_query) > 150 else ""),
        "retrieved_sources": list(set([c["source"] for c in context_chunks])) if context_chunks else [],
        "confidence_score": max([c["score"] for c in context_chunks]) if context_chunks else 0.0,
        "conversation_history_turns": len(history),
        "actions_already_attempted": attempted_actions,
        "recommended_action": (
            "Review API logs, check payment credentials/status, and "
            "contact the client directly via phone/email to resolve."
        )
    }
    return json.dumps(handoff_data, indent=2)

def rule_based_generate(user_query: str, persona: str, context_chunks: List[Dict[str, Any]], conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """Offline fallback response generator that parses context and wraps it in a persona-specific template."""
    best_score = max([chunk["score"] for chunk in context_chunks]) if context_chunks else 0.0
    
    # 1. Check for immediate escalation due to low confidence or empty context
    if best_score < config.SIMILARITY_THRESHOLD or len(context_chunks) == 0:
        return {
            "escalated": True,
            "response": (
                "I apologize, but I am unable to locate the precise solution to your request "
                "in our documentation. I am connecting you with a live human support specialist."
            ),
            "handoff_summary": generate_handoff_summary(user_query, persona, context_chunks, conversation_history)
        }
        
    # Use the best retrieved chunk text
    best_chunk = context_chunks[0]
    source_file = best_chunk["source"]
    chunk_text = best_chunk["text"]
    page_info = f" (Page {best_chunk['page']})" if best_chunk.get("page") else ""
    
    # 2. Select persona-specific template
    if persona == "Technical Expert":
        adapted_text = (
            f"### TECHNICAL DIAGNOSTIC REPORT\n"
            f"**Ref Reference:** KB Source [{source_file}]{page_info}\n"
            f"**System Status:** Documented integration details retrieved.\n\n"
            f"**Root Cause / Context Details:**\n"
            f"```text\n{chunk_text}\n```\n\n"
            f"**Recommended Integration Steps:**\n"
            f"1. Verify that your headers match the specifications in the log above.\n"
            f"2. Ensure HTTP method and endpoint URL parameters match exactly.\n"
            f"3. Check for trailing spaces in environment variable tokens.\n\n"
            f"If issues persist, please capture the HTTP request/response payloads for developer support."
        )
    elif persona == "Frustrated User":
        # Empathetic, simple validation
        adapted_text = (
            f"I completely understand how frustrating it is to deal with this issue, and I apologize "
            f"for the inconvenience it's causing you. Let's get this resolved as quickly as possible.\n\n"
            f"According to our support guides ({source_file}), here are the simple steps to follow:\n\n"
            f"{chunk_text}\n\n"
            f"**Here's what you should do next:**\n"
            f"- Double check that you've followed each step listed above.\n"
            f"- Let me know if you run into any errors or need me to explain any of these steps further!\n\n"
            f"We are here to help, and we'll make sure this is taken care of."
        )
    else:  # Business Executive
        adapted_text = (
            f"Thank you for bringing this operational inquiry to our attention. "
            f"Here is the business summary regarding your request:\n\n"
            f"**Status & Policies Summary:**\n"
            f"According to our policy guide ({source_file}), {chunk_text[:300]}...\n\n"
            f"**Commercial Impact & Resolution Outline:**\n"
            f"- **Action Plan:** System parameters are detailed in the documentation.\n"
            f"- **Estimated Timeline:** Standard resolution protocols are active.\n\n"
            f"If you require a detailed volume adjustment or specific SLA contract reviews, "
            f"please let me know and I will arrange it."
        )
        
    return {
        "escalated": False,
        "response": adapted_text,
        "handoff_summary": None
    }

def generate_adaptive_response(
    user_query: str, 
    persona: str, 
    context_chunks: List[Dict[str, Any]], 
    conversation_history: List[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Generates a personalized response matching the classified user archetype.
    
    If context confidence is too low or no chunks are found, the issue is flagged for escalation.
    Falls back to a rule-based generator if GEMINI_API_KEY is not configured.
    """
    api_key = config.GEMINI_API_KEY
    if not api_key:
        return rule_based_generate(user_query, persona, context_chunks, conversation_history)
        
    try:
        # 1. Establish the Escalation Check
        best_score = max([chunk["score"] for chunk in context_chunks]) if context_chunks else 0.0

        if best_score < config.SIMILARITY_THRESHOLD or len(context_chunks) == 0:
            return {
                "escalated": True,
                "response": (
                    "I apologize, but I am unable to locate the precise solution to your request. "
                    "I am connecting you with a live human support specialist."
                ),
                "handoff_summary": generate_handoff_summary(user_query, persona, context_chunks, conversation_history)
            }
            
        # 2. Select System Prompt instruction set depending on classified persona
        if persona == "Technical Expert":
            persona_instructions = (
                "You are a Senior Systems Engineer. Provide clear root-cause analysis, "
                "configuration specifications, and precise API pathways or code blocks. "
                "Keep technical descriptions exact and structured, formatted in clean Markdown. "
                "Cite the specific document sources and chunk details provided in the context."
            )
        elif persona == "Frustrated User":
            persona_instructions = (
                "You are a deeply empathetic, reassuring Customer Care Specialist. "
                "Begin with a warm, genuine validation of their difficulty. Use straightforward, "
                "reassuring, and simple action-oriented bullet steps. Avoid confusing technical jargon."
            )
        else:  # Business Executive
            persona_instructions = (
                "You are a concise Client Relations Director. Focus on direct business outcomes, "
                "impact summaries, and timelines for resolution. Keep responses extremely "
                "brief, professional, and skip unnecessary configuration details."
            )

        # 3. Assemble complete context-grounded system prompt
        context_text_parts = []
        for c in context_chunks:
            source_info = f"Source [{c['source']}]"
            if c.get("page"):
                source_info += f" Page {c['page']}"
            context_text_parts.append(f"{source_info} (Score: {c['score']}):\n{c['text']}")
            
        context_text = "\n\n".join(context_text_parts)

        full_system_prompt = (
            f"{persona_instructions}\n\n"
            "CRITICAL RULES:\n"
            "- Base your response ONLY on the provided context.\n"
            "- Do not hallucinate or assume facts not found in the documents.\n"
            "- If the provided context does not contain enough information to answer the question, "
            "say exactly: 'I apologize, but I am unable to locate the precise solution to your request. "
            "Connecting you to live human support.' and flag it.\n\n"
            f"FACTUAL CONTEXT DOCUMENTS:\n{context_text}"
        )

        # 4. Compile conversation history if present
        contents_input = []
        if conversation_history:
            for turn in conversation_history:
                contents_input.append(f"{turn['role'].capitalize()}: {turn['content']}")
        contents_input.append(f"User: {user_query}")
        
        user_input_compiled = "\n".join(contents_input)

        # Initialize Gemini Client
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=config.DEFAULT_LLM_MODEL,
            contents=user_input_compiled,
            config=types.GenerateContentConfig(
                system_instruction=full_system_prompt,
                temperature=0.2
            )
        )
        
        response_text = response.text
        
        # Double check if LLM self-escalated
        if "connecting you to live human support" in response_text.lower():
            return {
                "escalated": True,
                "response": response_text,
                "handoff_summary": generate_handoff_summary(user_query, persona, context_chunks, conversation_history)
            }

        return {
            "escalated": False,
            "response": response_text,
            "handoff_summary": None
        }
        
    except Exception as e:
        print(f"Gemini response generation failed: {e}. Falling back to rule-based generator.")
        return rule_based_generate(user_query, persona, context_chunks, conversation_history)

if __name__ == "__main__":
    # Test cases
    test_context = [
        {
            "text": "All Adsparkx AI API requests must be authenticated using a Bearer token. Place sk_live_xxx in the Authorization header. HTTP 401 Unauthorized is returned if no key is provided.",
            "source": "api_troubleshooting.md",
            "page": None,
            "score": 0.85
        }
    ]
    
    print("Testing Generator (Rule-based Fallback Active):")
    
    print("\n--- Technical Expert Response ---")
    res_tech = generate_adaptive_response(
        "How do I authorize the API?", "Technical Expert", test_context
    )
    print(res_tech["response"])
    
    print("\n--- Frustrated User Response ---")
    res_frustrated = generate_adaptive_response(
        "My key is not working!", "Frustrated User", test_context
    )
    print(res_frustrated["response"])
    
    print("\n--- Business Executive Response ---")
    res_exec = generate_adaptive_response(
        "What is the status of the authorization integration?", "Business Executive", test_context
    )
    print(res_exec["response"])
    
    print("\n--- Low Confidence Escalation Check ---")
    low_confidence_context = [
        {
            "text": "Random text about cookies...",
            "source": "cookie_policy.md",
            "page": None,
            "score": 0.25 # below threshold
        }
    ]
    res_escalate = generate_adaptive_response(
        "I demand an immediate refund for unauthorized charge!", "Frustrated User", low_confidence_context
    )
    print(f"Escalated Status: {res_escalate['escalated']}")
    print(f"Response: {res_escalate['response']}")
    print(f"Handoff Summary:\n{res_escalate['handoff_summary']}")

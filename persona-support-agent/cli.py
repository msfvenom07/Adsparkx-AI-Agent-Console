import os
import sys
import json
from pathlib import Path
from colorama import init, Fore, Back, Style

# Initialize colorama
init(autoreset=True)

# Ensure src package is accessible
sys.path.append(str(Path(__file__).resolve().parent))

from src import config
from src.classifier import classify_customer_persona
from src.rag_pipeline import LocalRAGPipeline
from src.generator import generate_adaptive_response
from src.escalator import check_escalation

def print_header():
    """Prints a styled startup banner."""
    print("\n" + "=" * 80)
    print(f" {Fore.CYAN + Style.BRIGHT}Adsparkx AI Persona-Adaptive Customer Support Agent{Style.RESET_ALL} ")
    print(f" {Fore.WHITE}Powered by Gemini & ChromaDB RAG Pipeline{Style.RESET_ALL} ")
    print("=" * 80)
    print(f"{Fore.GREEN}Type '/exit' or 'exit' to quit the chat.{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Type '/clear' to reset conversation history.{Style.RESET_ALL}")
    print("-" * 80 + "\n")

def chat_loop():
    """Main interactive chat loop."""
    # 1. Initialize RAG pipeline
    print(f"{Fore.YELLOW}Initializing knowledge base and connecting database...{Style.RESET_ALL}")
    try:
        rag_pipeline = LocalRAGPipeline()
        # Verify collection size
        collection_size = rag_pipeline.collection.count()
        if collection_size == 0:
            print(f"{Fore.YELLOW}Vector database is empty. Running ingestion...{Style.RESET_ALL}")
            rag_pipeline.ingest_directory()
            collection_size = rag_pipeline.collection.count()
        print(f"{Fore.GREEN}Ready! Loaded {collection_size} text chunks.{Style.RESET_ALL}\n")
    except Exception as e:
        print(f"{Fore.RED}Critical Error initializing database: {e}{Style.RESET_ALL}")
        print("Please check your database directory or dependencies.")
        return

    print_header()
    
    # 2. Maintain conversation history state
    conversation_history = []
    
    while True:
        try:
            # Get user query
            user_input = input(f"{Fore.WHITE + Style.BRIGHT}You: {Style.RESET_ALL}").strip()
            
            if not user_input:
                continue
                
            # Exit controls
            if user_input.lower() in ['/exit', 'exit', 'quit']:
                print(f"\n{Fore.CYAN}Thank you for choosing Adsparkx AI. Goodbye!{Style.RESET_ALL}\n")
                break
                
            # Clear controls
            if user_input.lower() == '/clear':
                conversation_history = []
                print(f"\n{Fore.GREEN}Conversation history cleared!{Style.RESET_ALL}\n")
                continue

            print(f"{Fore.LIGHTBLACK_EX}Processing request...{Style.RESET_ALL}")
            
            # Step 1: Detect Persona (Pass history for context-aware classification)
            persona_result = classify_customer_persona(user_input, conversation_history)
            persona = persona_result.get("persona", "Frustrated User")
            confidence = persona_result.get("confidence", 1.0)
            reasoning = persona_result.get("reasoning", "")
            
            # Print detected persona with color codes
            if persona == "Technical Expert":
                persona_color = Fore.CYAN
            elif persona == "Frustrated User":
                persona_color = Fore.LIGHTRED_EX
            else: # Business Executive
                persona_color = Fore.YELLOW
                
            print(f"\n{Fore.WHITE}--- Persona Assessment ---")
            print(f"Detected Persona: {persona_color + Style.BRIGHT}{persona}{Style.RESET_ALL} (Confidence: {Fore.GREEN}{confidence * 100:.0f}%{Style.RESET_ALL})")
            print(f"Assessment Reasoning: {Fore.LIGHTBLACK_EX}{reasoning}{Style.RESET_ALL}")
            
            # Step 2: Retrieve Relevant Support Chunks
            retrieved_chunks = rag_pipeline.retrieve_context(user_input, top_k=config.TOP_K)
            
            print(f"\n{Fore.WHITE}--- RAG Search Results ---")
            if retrieved_chunks:
                for idx, chunk in enumerate(retrieved_chunks):
                    page_str = f" Page {chunk['page']}" if chunk.get('page') else ""
                    print(f" {idx + 1}. [{Fore.GREEN}{chunk['source']}{page_str}{Style.RESET_ALL}] Similarity Score: {Fore.GREEN}{chunk['score'] * 100:.1f}%{Style.RESET_ALL}")
                    # Print small snippet
                    snippet = chunk['text'][:120].replace('\n', ' ') + "..."
                    print(f"    {Fore.LIGHTBLACK_EX}Snippet: {snippet}{Style.RESET_ALL}")
            else:
                print(f" {Fore.RED}Zero documents retrieved.{Style.RESET_ALL}")

            # Step 3: Run Escalation and Handoff Check
            escalation_result = check_escalation(
                user_input, persona, conversation_history, retrieved_chunks
            )
            
            # Step 4: Handle Escalation state
            if escalation_result.get("escalate", False):
                reason = escalation_result.get("reason", "No reason details.")
                summary = escalation_result.get("handoff_summary", "{}")
                
                print(f"\n{Back.RED + Fore.WHITE + Style.BRIGHT} !!! ESCALATING TO HUMAN AGENT !!! {Style.RESET_ALL}")
                print(f"Trigger Reason: {Fore.RED}{reason}{Style.RESET_ALL}")
                
                # Generate matching tone escalation message
                response_pkg = generate_adaptive_response(
                    user_input, persona, retrieved_chunks, conversation_history
                )
                print(f"\n{Fore.LIGHTRED_EX + Style.BRIGHT}Agent (Handoff Warning): {Style.RESET_ALL}{response_pkg['response']}")
                
                print(f"\n{Fore.YELLOW}--- Structured Human Handoff Report (JSON) ---")
                try:
                    # Parse and print pretty JSON
                    report_data = json.loads(summary)
                    print(Fore.YELLOW + json.dumps(report_data, indent=2))
                except Exception:
                    print(Fore.YELLOW + summary)
                print("=" * 80 + "\n")
                
                # Exit chat loop upon escalation
                print(f"{Fore.LIGHTBLACK_EX}Exiting customer session. Handed off to active queue.{Style.RESET_ALL}\n")
                break
                
            # Step 5: Generate and Output Grounded Adapted Response
            response_pkg = generate_adaptive_response(
                user_input, persona, retrieved_chunks, conversation_history
            )
            
            print(f"\n{Fore.GREEN + Style.BRIGHT}Agent ({persona} Mode):{Style.RESET_ALL}")
            print(response_pkg["response"])
            print("-" * 80 + "\n")
            
            # Step 6: Update session state history
            conversation_history.append({
                "role": "user",
                "content": user_input,
                "persona": persona
            })
            conversation_history.append({
                "role": "assistant",
                "content": response_pkg["response"]
            })
            
        except KeyboardInterrupt:
            print(f"\n\n{Fore.CYAN}Chat session aborted by keyboard interrupt. Goodbye!{Style.RESET_ALL}\n")
            break
        except Exception as e:
            print(f"\n{Fore.RED}An unexpected error occurred: {e}{Style.RESET_ALL}\n")

if __name__ == "__main__":
    chat_loop()

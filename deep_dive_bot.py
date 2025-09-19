import json
import logging
from llm_gemini import call_gemini_llm # Updated import
import os
import glob

# (The rest of the script is updated to use the new LLM call)
# --- Basic Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Data Loading ---
def load_deal_notes(path: str = "notes") -> list:
    deal_notes = []
    json_files = glob.glob(os.path.join(path, '*.json'))
    if not json_files:
        logger.warning(f"No JSON files found in the '{path}' directory.")
        return []
    for file_path in json_files:
        try:
            with open(file_path, 'r') as f:
                deal_notes.append(json.load(f))
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load or parse {file_path}. Error: {e}")
    return deal_notes

# --- Chatbot 2: Core Logic ---
def run_deep_dive_chatbot(user_question: str, company_name: str, all_deals: list):
    print(f"\n--- Deep Dive on {company_name} ---")
    print(f"Investor Question: '{user_question}'")
    
    target_deal_note = None
    for deal in all_deals:
        if deal.get('company', '').lower() == company_name.lower():
            target_deal_note = deal
            break
            
    if not target_deal_note:
        print(f"\nAnswer: Sorry, I could not find a deal note for '{company_name}'.")
        return
        
    context = json.dumps(target_deal_note, indent=2)
    
    qa_prompt = f"""
    You are a meticulous VC analyst assistant. Your task is to answer the user's question based *strictly* and *only* on the provided context (the company's deal note).
    - If the answer is in the context, provide it clearly and concisely. You can quote specific numbers or facts.
    - If the information is not present in the context, you MUST respond with: "This information is not available in the provided deal note."
    - Do not use any external knowledge or make assumptions.
    
    User's Question: "{user_question}"
    """
    
    answer = call_gemini_llm(user_prompt=qa_prompt, context=context) # Using Gemini
    print(f"\nAnswer: {answer}")


# --- Main Execution Block ---
if __name__ == "__main__":
    all_deal_notes = load_deal_notes()
    if all_deal_notes:
        run_deep_dive_chatbot("What is the vesting period for founders at Hexafun?", "Hexafun", all_deal_notes)
        print("\n" + "="*50)
        run_deep_dive_chatbot("Tell me about Anamika Pandey's background", "Naario", all_deal_notes)
        print("\n" + "="*50)
        run_deep_dive_chatbot("What is Naario's month-over-month revenue growth?", "Naario", all_deal_notes)
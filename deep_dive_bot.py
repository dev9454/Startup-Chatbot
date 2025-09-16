import json
import logging
import boto3
import os
import glob
from botocore.exceptions import ClientError # <-- THIS LINE IS NOW CORRECTED

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Bedrock LLM Integration (Same as before) ---
BEDROCK_REGION = "us-east-1"
client = None
try:
    client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)
except Exception as e:
    logger.error(f"Failed to create Boto3 client. Please check your AWS configuration. Error: {e}")
    client = None

SUPERVISOR_PROMPT_TEMPLATE = """You are an expert VC analyst assistant.
Use the provided context to complete the task.

[CONTEXT]
{context}

[TASK]
{user_prompt}
"""

def call_bedrock_llm(user_prompt: str, context: str = "") -> str:
    if not client:
        return "ERROR: Boto3 client not initialized."
    prompt = SUPERVISOR_PROMPT_TEMPLATE.format(context=context, user_prompt=user_prompt)
    formatted_prompt = f"""
<|begin_of_text|><|start_header_id|>user<|end_header_id|>
{prompt}
<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>
"""
    native_request = {"prompt": formatted_prompt, "max_gen_len": 2048, "temperature": 0.0}
    request_body = json.dumps(native_request)
    try:
        response = client.invoke_model(modelId="meta.llama3-70b-instruct-v1:0", body=request_body)
        model_response = json.loads(response["body"].read())
        return model_response["generation"]
    except (ClientError, Exception) as e:
        logger.error(f"ERROR: Could not invoke LLM. Reason: {e}")
        return f"ERROR: LLM invocation failed. Details: {e}"

# --- Data Loading (Same as before) ---
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
    """
    Answers deep-dive questions about a specific company using its deal note as context.
    """
    print(f"\n--- Deep Dive on {company_name} ---")
    print(f"Investor Question: '{user_question}'")
    
    # 1. Retrieve the correct deal note
    target_deal_note = None
    for deal in all_deals:
        if deal.get('company', '').lower() == company_name.lower():
            target_deal_note = deal
            break
            
    if not target_deal_note:
        print(f"\nAnswer: Sorry, I could not find a deal note for '{company_name}'.")
        return
        
    # 2. Augment the prompt with the full deal note as context
    context = json.dumps(target_deal_note, indent=2)
    
    # 3. Generate the answer with a strict prompt to prevent hallucination
    qa_prompt = f"""
    You are a meticulous VC analyst assistant. Your task is to answer the user's question based *strictly* and *only* on the provided context (the company's deal note).
    - If the answer is in the context, provide it clearly and concisely. You can quote specific numbers or facts.
    - If the information is not present in the context, you MUST respond with: "This information is not available in the provided deal note."
    - Do not use any external knowledge or make assumptions.
    
    User's Question: "{user_question}"
    """
    
    answer = call_bedrock_llm(user_prompt=qa_prompt, context=context)
    
    print(f"\nAnswer: {answer}")


# --- Main Execution Block ---
if __name__ == "__main__":
    all_deal_notes = load_deal_notes()
    if all_deal_notes:
        # Example 1: A question where the answer is clearly in the Hexafun JSON
        run_deep_dive_chatbot("What is the vesting period for founders at Hexafun?", "Hexafun", all_deal_notes)
        
        print("\n" + "="*50)
        
        # Example 2: A question about a founder from the Naario JSON
        run_deep_dive_chatbot("Tell me about Anamika Pandey's background", "Naario", all_deal_notes)
        
        print("\n" + "="*50)

        # Example 3: A question where the answer is NOT in the JSON, to test the "I don't know" response
        run_deep_dive_chatbot("What is Naario's month-over-month revenue growth?", "Naario", all_deal_notes)
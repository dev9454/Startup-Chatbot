import json
import logging
import boto3
import os
import glob
from botocore.exceptions import ClientError

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Bedrock LLM Integration ---
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
    # (This function is unchanged)
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

# --- Data Loading ---
def load_deal_notes(path: str = "notes") -> list:
    # (This function is unchanged)
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

# --- START OF FIX: Helper function for robust revenue access ---
def get_y1_revenue(deal):
    """Safely gets Y1 revenue from a deal note, handling both dict and list traction data."""
    traction_data = deal.get('facts', {}).get('traction', {})
    if isinstance(traction_data, dict):
        return traction_data.get('revenue', {}).get('Y1', 'N/A')
    return 'N/A' # Return 'N/A' if traction is a list (like Naario's) or not found
# --- END OF FIX ---

# --- Chatbot Core Logic ---
def run_deal_screener_chatbot(user_query: str, all_deals: list):
    if not all_deals:
        print("Cannot run the chatbot as no deal notes were loaded.")
        return
    print(f"\nInvestor Query: '{user_query}'")
    extraction_prompt = f"""
    You are a data extraction expert. From the user's query, extract search criteria into a JSON object.
    Only use these keys: 'sector', 'min_y1_revenue_cr', 'founder_education_contains'.
    - 'sector' must be one of ["foodtech", "lifestyle"]. If not mentioned, the value should be null.
    - 'min_y1_revenue_cr' must be a number. If not mentioned, the value should be null.
    - 'founder_education_contains' must be a string. If not mentioned, the value should be null.
    User Query: "{user_query}"
    Respond with ONLY the JSON object and nothing else.
    """
    structured_query_str = call_bedrock_llm(user_prompt=extraction_prompt)
    try:
        json_start = structured_query_str.find('{')
        json_end = structured_query_str.rfind('}') + 1
        query_params = json.loads(structured_query_str[json_start:json_end])
        logger.info(f"Extracted Query Params: {query_params}")
    except (json.JSONDecodeError, IndexError):
        logger.error(f"Failed to parse LLM response for query extraction: {structured_query_str}")
        print("\nSorry, I had trouble understanding your criteria. Please try a different phrasing.")
        return

    # Filtering logic
    matching_deals = []
    for deal in all_deals:
        match = True
        if 'min_y1_revenue_cr' in query_params and query_params['min_y1_revenue_cr'] is not None:
            y1_revenue = get_y1_revenue(deal) # Use the new helper function
            if y1_revenue == 'N/A' or y1_revenue < query_params['min_y1_revenue_cr']:
                match = False
        if 'sector' in query_params and query_params['sector'] is not None:
            deal_sector = ""
            kpis_str = " ".join(deal.get('sector', {}).get('kpis', [])).lower()
            if "food safety" in kpis_str: deal_sector = "foodtech"
            elif "customer acquisition" in kpis_str: deal_sector = "lifestyle"
            if deal_sector != query_params['sector']: match = False
        if 'founder_education_contains' in query_params and query_params['founder_education_contains'] is not None:
            founders = deal.get('facts', {}).get('founders', [])
            search_term = query_params['founder_education_contains'].lower()
            if not any(search_term in (f.get('education') or '').lower() for f in founders): match = False
        if match:
            matching_deals.append(deal)

    if not matching_deals:
        print("\nNo companies found matching your criteria.")
        return

    # --- START OF FIX: Use the helper function in the summary creation ---
    results_context = json.dumps([
        {
            "company": d.get("company"),
            "summary": f"Y1 Revenue: {get_y1_revenue(d)} Cr.",
            "founders": [(f.get('name'), f.get('education')) for f in d.get('facts', {}).get('founders', [])]
        } for d in matching_deals
    ])
    # --- END OF FIX ---
    
    presentation_prompt = f"""
    Based on the provided data, present the search results to the investor. The user's original query was: "{user_query}". For each company, provide a brief, compelling summary.
    """
    final_response = call_bedrock_llm(user_prompt=presentation_prompt, context=results_context)
    print("\n--- Search Results ---")
    print(final_response)

# --- Main Execution Block ---
if __name__ == "__main__":
    all_deal_notes = load_deal_notes()
    if all_deal_notes:
        print("="*50)
        run_deal_screener_chatbot("Find me companies that made over 20 Cr in their first year", all_deal_notes)
        print("\n" + "="*50)
        run_deal_screener_chatbot("Show me startups with founders from NIT Warangal", all_deal_notes)
        print("\n" + "="*50)
        run_deal_screener_chatbot("Which companies are in the foodtech sector?", all_deal_notes)
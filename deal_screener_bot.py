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

# --- Helper Function for Revenue ---
def get_y1_revenue(deal):
    # (This function is unchanged)
    traction_data = deal.get('facts', {}).get('traction', {})
    if isinstance(traction_data, dict):
        return traction_data.get('revenue', {}).get('Y1', 'N/A')
    return 'N/A' 

# --- Chatbot Core Logic ---
def run_deal_screener_chatbot(user_query: str, all_deals: list):
    # (This function is updated)
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
    structured_query_str = call_gemini_llm(user_prompt=extraction_prompt) # Using Gemini
    try:
        json_start = structured_query_str.find('{')
        json_end = structured_query_str.rfind('}') + 1
        query_params = json.loads(structured_query_str[json_start:json_end])
        logger.info(f"Extracted Query Params: {query_params}")
    except (json.JSONDecodeError, IndexError):
        logger.error(f"Failed to parse LLM response for query extraction: {structured_query_str}")
        print("\nSorry, I had trouble understanding your criteria. Please try a different phrasing.")
        return

    # Filtering logic (same as before)
    matching_deals = []
    for deal in all_deals:
        match = True
        if 'min_y1_revenue_cr' in query_params and query_params['min_y1_revenue_cr'] is not None:
            y1_revenue = get_y1_revenue(deal)
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

    results_context = json.dumps([
        {
            "company": d.get("company"),
            "summary": f"Y1 Revenue: {get_y1_revenue(d)} Cr.",
            "founders": [(f.get('name'), f.get('education')) for f in d.get('facts', {}).get('founders', [])]
        } for d in matching_deals
    ])
    
    presentation_prompt = f"""
    Based on the provided data, present the search results to the investor. The user's original query was: "{user_query}". For each company, provide a brief, compelling summary.
    """
    final_response = call_gemini_llm(user_prompt=presentation_prompt, context=results_context) # Using Gemini
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
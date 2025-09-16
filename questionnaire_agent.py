import json
import logging
import boto3
import os
from botocore.exceptions import ClientError
import PyPDF2  # New library to read PDFs

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Bedrock LLM Integration (Same as before) ---
BEDROCK_REGION = "us-east-1"
client = None
try:
    client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)
except Exception as e:
    logger.error(f"Failed to create Boto3 client. Error: {e}")
    client = None

SUPERVISOR_PROMPT_TEMPLATE = """You are an expert AI assistant.
Use the provided context to complete the task.

[CONTEXT]
{context}

[TASK]
{user_prompt}
"""

def call_bedrock_llm(user_prompt: str, context: str = "") -> str:
    if not client: return "ERROR: Boto3 client not initialized."
    prompt = SUPERVISOR_PROMPT_TEMPLATE.format(context=context, user_prompt=user_prompt)
    formatted_prompt = f"""
<|begin_of_text|><|start_header_id|>user<|end_header_id|>
{prompt}
<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>
"""
    native_request = {"prompt": formatted_prompt, "max_gen_len": 4096, "temperature": 0.1}
    request_body = json.dumps(native_request)
    try:
        response = client.invoke_model(modelId="meta.llama3-70b-instruct-v1:0", body=request_body)
        model_response = json.loads(response["body"].read())
        return model_response["generation"]
    except (ClientError, Exception) as e:
        logger.error(f"ERROR: Could not invoke LLM. Reason: {e}")
        return f"ERROR: LLM invocation failed. Details: {e}"

# --- Step 1: Pitch Deck Ingestion ---
def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts text content from a given PDF file."""
    try:
        with open(pdf_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
    except FileNotFoundError:
        logger.error(f"File not found at path: {pdf_path}")
        return None
    except Exception as e:
        logger.error(f"Failed to read PDF. Reason: {e}")
        return None

# --- Main Agent Logic ---
def generate_questionnaire(pitch_deck_text: str) -> str:
    """
    Analyzes pitch deck text and generates a tailored questionnaire.
    """
    if not pitch_deck_text:
        return "Error: Pitch deck text is empty."

    # The agent's internal "Investor Checklist"
    INVESTOR_CHECKLIST = """
    {
      "The Basics": ["Company Name", "Website", "One-Liner"],
      "Problem & Solution": ["Problem Statement", "Your Solution", "Unique Value Proposition"],
      "Team": ["Founder Names & Roles", "Relevant Experience"],
      "Market Size": ["Total Addressable Market (TAM)", "Serviceable Addressable Market (SAM)", "Source of Market Data"],
      "Traction & Metrics": ["Current Revenue (ARR/MRR)", "Month-over-Month Growth", "Number of Customers", "Key KPIs (e.g., Churn, MAU)"],
      "Business Model": ["How You Make Money", "Pricing Tiers"],
      "Unit Economics": ["Customer Acquisition Cost (CAC)", "Customer Lifetime Value (LTV)", "Gross Margin"],
      "Competition": ["Direct Competitors", "Your Competitive Advantage"],
      "Financials": ["Historical Financial Summary", "3-5 Year Projections", "Current Burn Rate & Runway"],
      "The Ask": ["Funding Amount Requested", "Valuation", "Use of Funds"]
    }
    """
    
    # --- Agent Step 1: Analyze & Extract ---
    print("Step 1: Analyzing pitch deck and extracting key info...")
    prompt_1 = f"""
    You are a VC analyst. Extract key information from the pitch deck text below and populate the Investor Checklist.
    For any information not explicitly mentioned, state "Not Found". Respond with ONLY the populated JSON object.

    [Investor Checklist]
    {INVESTOR_CHECKLIST}
    """
    extracted_data_str = call_bedrock_llm(user_prompt=prompt_1, context=pitch_deck_text)

    # --- Agent Step 2: Identify Gaps & Red Flags ---
    print("Step 2: Identifying missing information and potential red flags...")
    prompt_2 = f"""
    You are a skeptical but fair VC analyst. Review the Extracted Data Summary.
    1. Identify crucial topics from the checklist that are marked "Not Found".
    2. Identify potential red flags (e.g., unrealistic claims, inconsistencies, missing metrics).
    List these points as a simple JSON array of strings.

    [Extracted Data Summary]
    {extracted_data_str}
    """
    analysis_topics_str = call_bedrock_llm(user_prompt=prompt_2, context="")

    # --- Agent Step 3: Generate Questionnaire ---
    print("Step 3: Generating tailored questionnaire...")
    prompt_3 = f"""
    You are an AI assistant creating a professional and friendly questionnaire for a startup founder.
    Based on the provided Analysis Topics, generate a set of clear questions. Group them under logical headings.
    Address the founder directly (e.g., "Hello, thank you for submitting...").
    """
    questionnaire = call_bedrock_llm(user_prompt=prompt_3, context=analysis_topics_str)
    
    return questionnaire

# --- Main Execution Block ---
if __name__ == "__main__":
    # 1. Set the path to your PDF file
    pdf_path = "Multipl_Pitch.pdf"  # <-- IMPORTANT: Change this to your actual file path

    # 2. Extract the text from the PDF
    pitch_deck_content = extract_text_from_pdf(pdf_path)

    print("--- Starting AI Questionnaire Agent ---")

    # 3. Check if text was successfully extracted before running the agent
    if pitch_deck_content:
        # Use the 'pitch_deck_content' variable here
        final_questionnaire = generate_questionnaire(pitch_deck_content)
        print("\n--- Generated Questionnaire ---")
        print(final_questionnaire)
    else:
        print("\nCould not run agent because no content was extracted from the PDF.")
        print("Please check that the file path is correct and the PDF is not empty or an image.")
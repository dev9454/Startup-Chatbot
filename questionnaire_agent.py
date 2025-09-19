import json
import logging
from llm_gemini import call_gemini_llm # Updated import
import os
import PyPDF2

# (The rest of the script is updated to use the new LLM call)
# --- Basic Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- PDF Ingestion ---
def extract_text_from_pdf(pdf_path: str) -> str:
    # (This function is unchanged)
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
    # (This function is updated)
    if not pitch_deck_text:
        return "Error: Pitch deck text is empty."

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
    
    print("Step 1: Analyzing pitch deck and extracting key info...")
    prompt_1 = f"""
    You are a VC analyst. Extract key information from the pitch deck text below and populate the Investor Checklist.
    For any information not explicitly mentioned, state "Not Found". Respond with ONLY the populated JSON object.
    [Investor Checklist]
    {INVESTOR_CHECKLIST}
    """
    extracted_data_str = call_gemini_llm(user_prompt=prompt_1, context=pitch_deck_text) # Using Gemini

    print("Step 2: Identifying missing information and potential red flags...")
    prompt_2 = f"""
    You are a skeptical but fair VC analyst. Review the Extracted Data Summary.
    1. Identify crucial topics from the checklist that are marked "Not Found".
    2. Identify potential red flags (e.g., unrealistic claims, inconsistencies, missing metrics).
    List these points as a simple JSON array of strings.
    [Extracted Data Summary]
    {extracted_data_str}
    """
    analysis_topics_str = call_gemini_llm(user_prompt=prompt_2) # Using Gemini

    print("Step 3: Generating tailored questionnaire...")
    prompt_3 = f"""
    You are an AI assistant creating a professional and friendly questionnaire for a startup founder.
    Based on the provided Analysis Topics, generate a set of clear questions. Group them under logical headings.
    Address the founder directly (e.g., "Hello, thank you for submitting...").
    """
    questionnaire = call_gemini_llm(user_prompt=prompt_3, context=analysis_topics_str) # Using Gemini
    
    return questionnaire

# --- Main Execution Block ---
if __name__ == "__main__":
    mock_pitch_deck_text = """
    **Naario: The Future of Healthy Eating**
    **Our Mission:** To improve the lives of women and families with healthy, natural food.
    We are Naario, born from the lives we aim to improve. Our first product is the Naario Millet Muesli (350gms).
    **The Team:**
    - Anamika Pandey: Alumnus of NIT Warangal, previously New Initiatives Lead at Bigbasket's BBdaily.
    - Charul Chandak: Alumnus of SPJIMR, experience at Nestle.
    **Market:** The market for millets as a functional food is ₹312 Bn. The export market is $2 billion.
    **Distribution:** We have partnerships with Big Basket and Amazon.
    """
    
    print("--- Starting AI Questionnaire Agent ---")
    if mock_pitch_deck_text:
        final_questionnaire = generate_questionnaire(mock_pitch_deck_text)
        print("\n--- Generated Questionnaire ---")
        print(final_questionnaire)
    else:
        print("Could not generate questionnaire because no pitch deck text was found.")
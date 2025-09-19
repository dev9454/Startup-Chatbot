# llm_gemini.py
import logging
import google.generativeai as genai
from config import GEMINI_API_KEY

# Basic setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure the Gemini API
try:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Gemini API configured successfully.")
except Exception as e:
    logger.error(f"Failed to configure Gemini API. Please check your API key. Error: {e}")
    
# Set up the model
generation_config = {
  "temperature": 0.1,
  "top_p": 1,
  "top_k": 1,
  "max_output_tokens": 8192,
}

model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest",
                              generation_config=generation_config)

def call_gemini_llm(user_prompt: str, context: str = "") -> str:
    """
    Calls the Gemini API with a given prompt and context.
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        return "ERROR: Gemini API key is not configured in config.py."
        
    full_prompt = f"""
    You are an expert AI assistant. Use the provided context to complete the task.

    [CONTEXT]
    {context}

    [TASK]
    {user_prompt}
    """
    
    try:
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        logger.error(f"ERROR: Could not invoke Gemini. Reason: {e}")
        return f"ERROR: Gemini invocation failed. Details: {e}"
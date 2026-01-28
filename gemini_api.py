import os
import json
from datetime import datetime
from google import genai
from google.genai import types

# Initialize the client globally or inside functions
# The new SDK doesn't use a global 'configure' state like the old one
def get_gemini_client():
    """Initialize Gemini Client with API key from environment"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    return genai.Client(api_key=api_key)


def send_prompt_and_store(prompt_parts: list | str, output_file: str = None):
    """
    Send prompt to Gemini API and store the response.
    
    Args:
        prompt_parts (list | str): The prompt content (string or list of strings/images)
        output_file (str): Path to store the response. If None, uses default naming
        
    Returns:
        The response object or error dict
    """
    try:
        client = get_gemini_client()
        
        # Send prompt and get response using the new V1 SDK syntax
        # We use 'gemini-2.0-flash' as it is the current standard model
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt_parts,
            config=types.GenerateContentConfig(
                temperature=0.2, # Lower temperature for analytical tasks
            )
        )
        
        return response
        
    except Exception as e:
        error_response = {
            'timestamp': datetime.now().isoformat(),
            'prompt': str(prompt_parts)[:200] + "...", # Truncate for log readability
            'error': str(e),
            'status': 'failed'
        }
        
        # Store error to file
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'gemini_error_{timestamp}.json'
        
        with open(output_file, 'w') as f:
            json.dump(error_response, f, indent=2)
        
        print(f"Error occurred: {str(e)}")
        return error_response


def generate_prompt_from_dataframe(dfs_as_strings):
    """
    Constructs a prompt for Gemini to analyze DV360 anomaly datasets.
    
    Args:
        dfs_as_strings (list of str): List of CSV strings representing the anomaly dataframes.
        
    Returns:
        list of str: A list containing the instructions followed by the datasets.
    """
    
    # 1. Define the Role and specific Analysis Instructions
    system_instruction = """
    **Role:** You are an expert DV360 (Display & Video 360) Campaign Manager and Data Analyst.
    
    **Context:** I am providing you with multiple datasets containing "anomalies" detected today in recent campaigns. 
    Each dataset represents a different slice of data where performance deviated from the normal
    **Your Task:**
    Analyze these datasets and provide a strategic report for the client. For each dataset provided:
    1. **Diagnose Root Causes:** Hypothesize *why* this might be happening in strictly 1-2 sentence(e.g., low inventory quality, competitive bidding war, creative fatigue, technical exclusion issues).
    2. **Actionable Suggestions:** Provide 2-3 specific, tactical steps I can take in DV360 to fix this. Use standard DV360 terminology (e.g., "Apply negative targeting," "Adjust bid multipliers," "Check creative audit status," "Switch to fixed bidding").

    **Format:**
    Please structure your response clearly with headings for each dataset. Bullet points are preferred for the suggestions.
    """

    # 2. Combine instructions with the data
    # We put the instruction first, so the model knows what to do with the data that follows.
    full_prompt_payload = [system_instruction] + dfs_as_strings
    
    return full_prompt_payload
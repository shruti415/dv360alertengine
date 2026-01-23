import google.generativeai as genai
import os
from datetime import datetime
import json

# Configure Gemini API
def configure_gemini():
    """Configure Gemini API with API key from environment"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    genai.configure(api_key=api_key)


def send_prompt_and_store(prompt: str, output_file: str = None) -> dict:
    """
    Send prompt to Gemini API and store the response
    
    Args:
        prompt (str): The prompt to send to Gemini
        output_file (str): Path to store the response. If None, uses default naming
        
    Returns:
        dict: Contains the response and metadata
    """
    try:
        configure_gemini()
        
        # Initialize the Gemini model
        model = genai.GenerativeModel('gemini-pro')
        
        # Send prompt and get response
        response = model.generate_content(prompt)
        
        # Prepare response data
        response_data = {
            'timestamp': datetime.now().isoformat(),
            'prompt': prompt,
            'response': response.text,
            'status': 'success'
        }
        
        # Store response to file if no specific output file provided
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'gemini_response_{timestamp}.json'
        
        # Save response to JSON file
        with open(output_file, 'w') as f:
            json.dump(response_data, f, indent=2)
        
        print(f"Response saved to {output_file}")
        
        return response_data
        
    except Exception as e:
        error_response = {
            'timestamp': datetime.now().isoformat(),
            'prompt': prompt,
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


def generate_prompt_from_dataframe(df, analysis_type: str = "general") -> str:
    """
    Generate a prompt from a dataframe for Gemini API
    
    Args:
        df: Pandas DataFrame
        analysis_type (str): Type of analysis (general, summary, insights, etc.)
        
    Returns:
        str: Generated prompt
    """
    # Get dataframe info
    shape = df.shape
    columns = df.columns.tolist()
    dtypes = df.dtypes.to_dict()
    
    # Get sample data
    sample_data = df.head(3).to_string()
    
    # Create prompt based on analysis type
    if analysis_type == "summary":
        prompt = f"""
Analyze the following data and provide a concise summary:

Dataset Shape: {shape[0]} rows, {shape[1]} columns
Columns: {', '.join(columns)}
Data Types: {dtypes}

Sample Data:
{sample_data}

Please provide:
1. Brief overview of the dataset
2. Key statistics
3. Notable patterns or anomalies
"""
    
    elif analysis_type == "insights":
        prompt = f"""
Analyze the following data and provide actionable insights:

Dataset Shape: {shape[0]} rows, {shape[1]} columns
Columns: {', '.join(columns)}

Sample Data:
{sample_data}

Please provide:
1. Top 3 key insights
2. Potential issues or concerns
3. Recommendations for action
"""
    
    else:  # general
        prompt = f"""
Analyze the following dataset:

Dataset Shape: {shape[0]} rows, {shape[1]} columns
Columns: {', '.join(columns)}
Data Types: {dtypes}

Sample Data:
{sample_data}

Provide your analysis:
"""
    
    return prompt

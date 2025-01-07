import os
import openai
from dotenv import load_dotenv

# Load environment variables (e.g., OPENAI_API_KEY) from .env, if present
load_dotenv()

# Ensure the API key is set
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("Missing OPENAI_API_KEY environment variable.")

def analyze_data_with_gpt_stream(data):
    """
    Sends 'data' to GPT for streaming analysis.
    Yields chunks of the GPT response.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": f"Analyze the following data:\n\n{data}"}
            ],
            stream=True  # Enable streaming
        )

        for chunk in response:
            if "choices" in chunk:
                for choice in chunk["choices"]:
                    if "delta" in choice and "content" in choice["delta"]:
                        yield choice["delta"]["content"]

    except Exception as e:
        print("Error during GPT streaming analysis:", e)
        yield f"Error: {str(e)}"

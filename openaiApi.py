import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_data_with_gpt_stream(data):
    """
    Sends 'data' to GPT for streaming analysis.
    Yields chunks of the GPT response.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": f"Analyze the following data:\n\n{data}"}],
            stream=True  # Enable streaming
        )

        for chunk in response:
            if "choices" in chunk:
                for choice in chunk["choices"]:
                    if "delta" in choice and "content" in choice["delta"]:
                        yield choice["delta"]["content"]
    except Exception as e:
        print(f"Error in analyze_data_with_gpt_stream: {e}")
        yield f"Error: {str(e)}"

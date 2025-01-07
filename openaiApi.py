# openaiApi.py

import os
import openai
from dotenv import load_dotenv

from openai import OpenAI
client = OpenAI()

# Load environment variables (e.g., OPENAI_API_KEY) from .env, if present
load_dotenv()

# Ensure the API key is set
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("Missing OPENAI_API_KEY environment variable.")

def analyze_data_with_gpt(data):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": f"Analyze the following data:\n\n{data}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print("Error during GPT analysis:", e)
        return {"error": str(e)}


# Optional: test locally
if __name__ == "__main__":
    sample_text = """
    Mars transiting Jupiter with a conjunction on 2025-01-01.
    Transit intensity is high. 
    """
    result = analyze_data_with_gpt(sample_text)
    print("GPT Analysis Result:")
    print("--------------------")
    print(result)

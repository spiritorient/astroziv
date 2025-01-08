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
    """
    Sends the 'data' to GPT for analysis using openai>=1.0.0.
    Returns the GPT response text.
    """
    # Using new openai>=1.0.0 syntax: openai.Chat.create(...)
    response = client.chat.completions.create(
        model="gpt-4o",  # or "gpt-4", "gpt-3.5-turbo-16k", etc.
        messages=[
            # {"role": "system", "content": "You're an excellent and experienced intellectual academic expert. You apply analytical interdisciplinary methodology by merging relevant scientific branches. Discursive, extensive and enlightening analysis. Depth analysis and content breakdown. You pay particular attention to the exhaustive and sovereign derivation of definitions of terms. Analytically you connect context and self-inciatively create textually and intellectually rich and deep content. Qualitative and quantitative writing style."},
            {
                "role": "user",
                "content": f"Please analyze the following data as roleplaying a role of adept astrologist:\n\n{data}\n"
            }
        ],
       # temperature=0.7
    )
    print("      ")
    print("      ")
    print("      ")
    print("      ")
    print(response.usage.prompt_tokens)
    print(response.usage.completion_tokens)
    print("      ")
    print("      ")
    print("      ")
    print("      ")
    print("      ")
    print("      ")
    print("      ")

    return response.choices[0].message.content


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

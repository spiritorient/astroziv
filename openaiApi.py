import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables (e.g., OPENAI_API_KEY) from .env, if present
load_dotenv()

# Instantiate the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Check if the API key is set
if not client.api_key:
    raise ValueError("Missing OPENAI_API_KEY environment variable.")

def analyze_data_with_gpt_stream(data):
    """
    Sends 'data' to GPT for streaming analysis.
    Yields chunks of the GPT response.
    """
    try:
        # Initiate the streaming response
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": f"Analyze the following data:\n\n{data}"}
            ],
            stream=True  # Enable streaming
        )

        # Yield each chunk of the response as it arrives
        for chunk in response:
            if chunk.choices:
                for choice in chunk.choices:
                    if hasattr(choice, "delta") and hasattr(choice.delta, "content"):
                        yield choice.delta.content

    except Exception as e:
        print("Error during GPT streaming analysis:", e)
        yield f"Error: {str(e)}"

# Optional: Test the streaming function locally
if __name__ == "__main__":
    sample_text = """
    Mars transiting Jupiter with a conjunction on 2025-01-01.
    Transit intensity is high.
    """

    print("Streaming GPT analysis result:")
    for chunk in analyze_data_with_gpt_stream(sample_text):
        print(chunk, end="")

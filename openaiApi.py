import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables (e.g., OPENAI_API_KEY) from .env, if present
load_dotenv()

# Initialize the OpenAI client
client = OpenAI()

# Ensure the API key is set
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("Missing OPENAI_API_KEY environment variable.")

# Your Assistant ID (replace with your actual Assistant ID)
ASSISTANT_ID = "asst_mcEJdPyp5ATrM1f86vj7v5ED"

def analyze_data_with_assistant(data):
    """
    Sends the 'data' to your OpenAI Assistant for analysis.
    Returns the Assistant's response text.
    """
    # Create a new thread
    thread = client.beta.threads.create()

    # Add the user's message to the thread
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=f"Please analyze the following data as roleplaying a role of an adept astrologist:\n\n{data}\n"
    )

    # Run the Assistant on the thread
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID
    )

    # Wait for the Assistant to respond
    while run.status != "completed":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )

    # Retrieve the Assistant's response
    messages = client.beta.threads.messages.list(
        thread_id=thread.id
    )

    # Extract and return the Assistant's response
    assistant_response = ""
    for message in messages.data:
        if message.role == "assistant":
            assistant_response = message.content[0].text.value
            break

    return assistant_response


# Optional: test locally
if __name__ == "__main__":
    sample_text = """
    Mars transiting Jupiter with a conjunction on 2025-01-01.
    Transit intensity is high. 
    """
    result = analyze_data_with_assistant(sample_text)
    print("Assistant Analysis Result:")
    print("-------------------------")
    print(result)
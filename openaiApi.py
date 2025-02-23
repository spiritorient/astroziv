import os
from re import T
from dotenv import load_dotenv
from openai import OpenAI
import time

load_dotenv()
client = OpenAI()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("Missing OPENAI_API_KEY environment variable.")

def analyze_data_with_chat_completion(data):
    """
    Sends all transit data to OpenAI's Chat Completion API in a single request.
    Returns the model's response text.
    """
    system_message = """
You're an excellent and experienced intellectual expert in a role of an adept astrologist that provides discursive, extensive and enlightening deep analysis with qualitative and quantitative writing style; analyze all of the following data progressively ensuring no transit is omitted for any day, including multiple transits on the same day and provide an insightful and deep analysis of every and each of the transits for every and each day, furthermore provide 'Warnings', 'Advices' and 'Guidances' regarding 'Daily Actions' for all of the timespan depending on every and each of the transits and corresponding intensities, additionally provide detailed 'Daily Insights' and 'Conclusions' taking into account data as a whole in fluent and follow up style, furthermore explaining provided with insightful and holistic style of full data analysis.
"""
    try:
        response = client.chat.completions.create(
            model="o1-mini",
            messages=[
                {"role": "user", "content": system_message + data}
            ],
            store=True,
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"Chat Completion error: {str(e)}")

if __name__ == "__main__":
    sample_text = """
Day: 2025-02-23
1. Transiting Planet: Mars, Natal Planet: Jupiter, Aspect: Square, Intensity: 0.573
2. Transiting Planet: Mercury, Natal Planet: Mercury, Aspect: Trine, Intensity: 0.738

Day: 2025-02-24
1. Transiting Planet: Mars, Natal Planet: Jupiter, Aspect: Square, Intensity: 0.572
2. Transiting Planet: Mercury, Natal Planet: Mercury, Aspect: Trine, Intensity: 0.967
    """
    result = analyze_data_with_chat_completion(sample_text)
    print("Chat Completion Analysis Result:")
    print("-------------------------")
    print(result)
# interpretation.py
import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create OpenAI client instance
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_interpretation(chart_data):
    prompt = (
        "You are an expert astrologer. Based on the following JSON chart data, including astrocartography lines, "
        "generate a concise yet insightful interpretation focused solely on how these astrocartography lines "
        "influence the user. Only refer to birth chart details (e.g., planetary or house positions) in relation to "
        "the planetary lines shown, which represent areas of geographic influence. Assume this interpretation is "
        "for the user at their birth location. Do not analyze the entire birth chart; instead, describe the potential "
        "effects the planetary lines might have on the user, prioritizing those closest to the center of influence.\n\n"
        f"{chart_data}\n\n"
        "Return a brief and readable interpretation suitable for an astrology app."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a skilled astrocartographer and interpret planetary line influences with precision."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,
            temperature=0.8
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating interpretation: {str(e)}"

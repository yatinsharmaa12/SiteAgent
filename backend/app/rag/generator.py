import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()


class GeminiGenerator:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set")

        self.client = genai.Client(api_key=api_key)

    def generate(self, prompt: str) -> str:
        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model="gemini-3.7-flash",
                    contents=prompt,
                )

                return response.text

            except Exception:
                if attempt == 2:
                    raise

                time.sleep(2 ** attempt)

        return response.text
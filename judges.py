# judges.py
"""
Thin wrapper around the Gemini API. Keeps all model-calling
logic in one place so app.py stays simple.
"""

import random

from PIL import Image
from google import genai
from google.genai import types

from prompts import JUDGES, ALL_JUDGES_SYSTEM


class DesktopCourtAI:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    def _generate(self, image_path: str, prompt: str) -> str:
        """
        Sends image + prompt to Gemini and returns the text response.
        Raises a RuntimeError with a clean message on failure so the
        web layer can show something sensible instead of a raw trace.
        """
        try:
            image = Image.open(image_path)
        except Exception as exc:
            raise RuntimeError(f"Could not open image: {exc}") from exc

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, image],
                config=types.GenerateContentConfig(
                    temperature=1.2,
                    max_output_tokens=1500
                )
            )
        except Exception as exc:
            raise RuntimeError(f"Gemini API error: {exc}") from exc

        text = (response.text or "").strip()
        if not text:
            raise RuntimeError("Gemini returned an empty response. Try again.")

        return text

    def run_judge(self, image_path: str, judge_name: str) -> str:
        """Single Judge Mode"""
        if judge_name not in JUDGES:
            raise ValueError(f"Unknown judge: {judge_name}")

        return self._generate(image_path=image_path, prompt=JUDGES[judge_name])

    def run_random_judge(self, image_path: str):
        """Random Judge Mode -> (judge_name, result)"""
        judge_name = random.choice(list(JUDGES.keys()))
        result = self._generate(image_path=image_path, prompt=JUDGES[judge_name])
        return judge_name, result

    def run_all_judges(self, image_path: str) -> str:
        """All Judges Mode"""
        return self._generate(image_path=image_path, prompt=ALL_JUDGES_SYSTEM)

    def get_judge_names(self):
        return list(JUDGES.keys())

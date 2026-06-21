# judges.py
"""
Thin wrapper around the Gemini API. Keeps all model-calling
logic in one place so app.py stays simple.
"""

import random
import time

from PIL import Image
from google import genai
from google.genai import types
from google.genai import errors as genai_errors

from prompts import JUDGES, ALL_JUDGES_SYSTEM

# Single-judge verdicts fit comfortably in this budget.
SINGLE_JUDGE_MAX_TOKENS = 1500

# "All Judges" has to fit 12 personas in one response — needs a lot more
# room or it gets cut off mid-sentence (which is what was happening).
ALL_JUDGES_MAX_TOKENS = 6000

# Retry behavior for transient 429s (rate limit, not daily quota).
MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 2  # 2s, 4s, 8s


class DesktopCourtAI:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    def _generate(self, image_path: str, prompt: str, max_output_tokens: int) -> str:
        """
        Sends image + prompt to Gemini and returns the text response.
        Retries on transient 429 rate-limit errors with exponential backoff.
        Raises a RuntimeError with a clean message on failure so the
        web layer can show something sensible instead of a raw trace.
        """
        try:
            image = Image.open(image_path)
        except Exception as exc:
            raise RuntimeError(f"Could not open image: {exc}") from exc

        last_error = None

        for attempt in range(MAX_RETRIES + 1):
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[prompt, image],
                    config=types.GenerateContentConfig(
                        temperature=1.2,
                        max_output_tokens=max_output_tokens
                    )
                )
                return self._extract_text(response)

            except genai_errors.ClientError as exc:
                last_error = exc
                status_code = getattr(exc, "code", None)

                if status_code == 429:
                    if self._is_daily_quota_error(exc):
                        raise RuntimeError(
                            "Daily free-tier quota used up for today. "
                            "It resets at midnight Pacific Time — try again later, "
                            "or add billing in Google AI Studio for higher limits."
                        ) from exc

                    # Per-minute rate limit (RPM/TPM) — this is transient,
                    # worth retrying with backoff.
                    if attempt < MAX_RETRIES:
                        wait = BASE_BACKOFF_SECONDS * (2 ** attempt)
                        time.sleep(wait)
                        continue

                    raise RuntimeError(
                        "The court is overwhelmed with cases right now (rate limit). "
                        "Please wait a few seconds and try again."
                    ) from exc

                raise RuntimeError(f"Gemini API error: {exc}") from exc

            except Exception as exc:
                raise RuntimeError(f"Gemini API error: {exc}") from exc

        # Should not reach here, but just in case
        raise RuntimeError(f"Gemini API error: {last_error}")

    @staticmethod
    def _is_daily_quota_error(exc: "genai_errors.ClientError") -> bool:
        """
        Inspects the structured error body for a QuotaFailure violation
        whose quotaId mentions PerDay. Falls back to substring-checking
        the raw message if the structured details aren't present, since
        Google's error shape isn't 100% guaranteed across SDK versions.
        """
        details = getattr(exc, "details", None)

        try:
            if isinstance(details, dict):
                error_details = details.get("error", {}).get("details", []) or details.get("details", [])
                for entry in error_details:
                    violations = entry.get("violations", [])
                    for violation in violations:
                        quota_id = violation.get("quotaId", "")
                        if "perday" in quota_id.lower():
                            return True
                        if "perminute" in quota_id.lower():
                            return False
        except (AttributeError, TypeError):
            pass

        # Fallback: crude text match if structured parsing didn't find anything
        message = str(exc).lower()
        return "per day" in message or "perday" in message.replace(" ", "")

    @staticmethod
    def _extract_text(response) -> str:
        text = (response.text or "").strip()
        if not text:
            raise RuntimeError("Gemini returned an empty response. Try again.")
        return text

    def run_judge(self, image_path: str, judge_name: str) -> str:
        """Single Judge Mode"""
        if judge_name not in JUDGES:
            raise ValueError(f"Unknown judge: {judge_name}")

        return self._generate(
            image_path=image_path,
            prompt=JUDGES[judge_name],
            max_output_tokens=SINGLE_JUDGE_MAX_TOKENS
        )

    def run_random_judge(self, image_path: str):
        """Random Judge Mode -> (judge_name, result)"""
        judge_name = random.choice(list(JUDGES.keys()))
        result = self._generate(
            image_path=image_path,
            prompt=JUDGES[judge_name],
            max_output_tokens=SINGLE_JUDGE_MAX_TOKENS
        )
        return judge_name, result

    def run_all_judges(self, image_path: str) -> str:
        """All Judges Mode"""
        return self._generate(
            image_path=image_path,
            prompt=ALL_JUDGES_SYSTEM,
            max_output_tokens=ALL_JUDGES_MAX_TOKENS
        )

    def get_judge_names(self):
        return list(JUDGES.keys())

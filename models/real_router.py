import os
import time

from dotenv import load_dotenv
from google import genai
from openai import OpenAI

from monitoring.monitor import log_request

load_dotenv()


class RealModelRouter:
    """Route requests to Gemini first, then OpenAI if Gemini fails."""

    def __init__(self):
        self.gemini_model = os.getenv(
            "GEMINI_MODEL",
            "gemini-2.5-flash",
        )

        self.openai_model = os.getenv(
            "OPENAI_MODEL",
            "gpt-4.1-mini",
        )

        self.last_used_model = None

    def _call_gemini(self, prompt):
        """Generate a response using Gemini."""

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is missing from your .env file."
            )

        client = genai.Client(api_key=api_key)

        result = client.models.generate_content(
            model=self.gemini_model,
            contents=prompt,
        )

        if not result.text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return result.text

    def _call_openai(self, prompt):
        """Generate a response using OpenAI."""

        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is missing from your .env file."
            )

        client = OpenAI(api_key=api_key)

        result = client.responses.create(
            model=self.openai_model,
            input=prompt,
        )

        if not result.output_text:
            raise RuntimeError(
                "OpenAI returned an empty response."
            )

        return result.output_text

    def _log(
        self,
        model,
        started_at,
        status,
        fallback_used,
        error=None,
    ):
        """Log request details to the monitoring CSV."""

        elapsed = time.perf_counter() - started_at

        try:
            log_request(
                model=model,
                response_time=elapsed,
                status=status,
                fallback_used=fallback_used,
                error=error,
            )
        except Exception as logging_error:
            print(
                "Monitoring log warning:",
                logging_error,
            )

    def generate(
        self,
        prompt,
        force_gemini_failure=False,
    ):
        """
        Try Gemini first, then OpenAI.

        Set force_gemini_failure=True only when testing
        whether the OpenAI fallback works.
        """

        started_at = time.perf_counter()
        gemini_error = None

        # Attempt 1: Gemini
        try:
            if force_gemini_failure:
                raise RuntimeError(
                    "Simulated Gemini failure for testing."
                )

            response = self._call_gemini(prompt)

            self.last_used_model = (
                f"Gemini ({self.gemini_model})"
            )

            self._log(
                model=self.last_used_model,
                started_at=started_at,
                status="success",
                fallback_used=False,
            )

            return {
                "response": response,
                "model": self.last_used_model,
                "fallback_used": False,
                "error": None,
            }

        except Exception as error:
            gemini_error = str(error)

            print("Gemini request failed.")
            print("Trying OpenAI as the backup provider.")

        # Attempt 2: OpenAI
        try:
            response = self._call_openai(prompt)

            self.last_used_model = (
                f"OpenAI ({self.openai_model})"
            )

            self._log(
                model=self.last_used_model,
                started_at=started_at,
                status="success",
                fallback_used=True,
                error=f"Gemini failed: {gemini_error}",
            )

            return {
                "response": response,
                "model": self.last_used_model,
                "fallback_used": True,
                "error": None,
            }

        except Exception as error:
            openai_error = str(error)
            self.last_used_model = None

            error_message = (
                f"Gemini failed: {gemini_error}; "
                f"OpenAI failed: {openai_error}"
            )

            self._log(
                model="Both providers failed",
                started_at=started_at,
                status="failed",
                fallback_used=True,
                error=error_message,
            )

            return {
                "response": (
                    "Both providers failed. "
                    "Check the error details and configuration."
                ),
                "model": None,
                "fallback_used": True,
                "error": error_message,
            }
"""
AI model factory.

On Jules' GCP VM, uses Vertex AI with Application Default Credentials —
no API key required. The VM's service account is used automatically.

For local development outside GCP:
  Option A: run `gcloud auth application-default login` and set
            GOOGLE_CLOUD_PROJECT to your project ID.
  Option B: set GEMINI_API_KEY to use the public Gemini API directly.
"""

from __future__ import annotations

import os

# Single model name used across both auth paths to keep behaviour consistent.
# Update here when switching to a newer model.
GEMINI_MODEL = "gemini-2.0-flash"


def get_model(temperature: float = 0.1):
    """Return a configured Gemini generative model.

    Tries Vertex AI (ADC) first; falls back to google-generativeai + API key.
    """
    try:
        import vertexai
        from vertexai.generative_models import GenerationConfig, GenerativeModel

        vertexai.init()  # reads project from env / metadata server / gcloud config
        return GenerativeModel(
            GEMINI_MODEL,
            generation_config=GenerationConfig(
                response_mime_type="application/json",
                temperature=temperature,
            ),
        )
    except Exception as vertex_err:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "No AI credentials found.\n"
                "  On Jules VM: Vertex AI ADC should work automatically.\n"
                "  Locally: set GEMINI_API_KEY or run `gcloud auth application-default login`.\n"
                f"  Vertex AI error was: {vertex_err}"
            ) from vertex_err

        import google.generativeai as genai

        genai.configure(api_key=api_key)
        return genai.GenerativeModel(
            GEMINI_MODEL,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=temperature,
            ),
        )

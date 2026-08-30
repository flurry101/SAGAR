"""
Bhashini Adapter — Indian Regional Language Translation

Uses the Bhashini ULCA (Universal Language Contribution API) pipeline
for translating ORCA advisories into Indian regional languages.

Supported languages (via Bhashini NMT pipeline):
    en ↔ hi, ta, te, kn, ml, bn, mr, gu, pa, or

Architecture:
    English structured advisory
      ↓
    BhashiniAdapter.translate()
      ↓
    Indian regional language text

Gemini remains the fallback ONLY when:
    1. Bhashini API is unreachable
    2. Bhashini credentials are not configured
    3. The requested language pair is not supported

Reference: SIH26176 — Indian regional language support, Bhashini integration
"""

from __future__ import annotations

import os
import json
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Bhashini-supported Indian language codes
BHASHINI_SUPPORTED_LANGUAGES = {
    "hi", "ta", "te", "kn", "ml", "bn", "mr", "gu", "pa", "or",
}

# Bhashini ULCA pipeline endpoints
BHASHINI_PIPELINE_URL = "https://meity-auth.udyat.ai/ulca/apis/v0/model/getModelsPipeline"
BHASHINI_COMPUTE_URL_DEFAULT = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"


class BhashiniAdapter:
    """Adapter for the Bhashini ULCA translation pipeline.

    Usage:
        adapter = BhashiniAdapter()
        result = adapter.translate(
            text="Avoid departure at 05:00. High waves detected.",
            source_lang="en",
            target_lang="hi",
        )
        # result = {
        #     "translated_text": "05:00 बजे प्रस्थान से बचें। ऊंची लहरें पाई गईं।",
        #     "translation_provider": "bhashini",
        #     "source_lang": "en",
        #     "target_lang": "hi",
        #     "success": True,
        # }
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        user_id: Optional[str] = None,
        pipeline_url: Optional[str] = None,
        timeout: float = 15.0,
    ):
        self.api_key = api_key or os.environ.get("BHASHINI_API_KEY", "")
        self.user_id = user_id or os.environ.get("BHASHINI_USER_ID", "")
        self.pipeline_url = pipeline_url or os.environ.get(
            "BHASHINI_PIPELINE_URL", BHASHINI_PIPELINE_URL
        )
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        """Check if Bhashini credentials are available."""
        return bool(self.api_key and self.user_id)

    def supports_language(self, lang_code: str) -> bool:
        """Check if a language code is supported by Bhashini NMT."""
        return lang_code in BHASHINI_SUPPORTED_LANGUAGES

    def translate(
        self,
        text: str,
        source_lang: str = "en",
        target_lang: str = "hi",
    ) -> dict:
        """Translate text using the Bhashini ULCA pipeline.

        Args:
            text: The text to translate.
            source_lang: Source language ISO 639-1 code (default: "en").
            target_lang: Target language ISO 639-1 code.

        Returns:
            dict with keys:
                translated_text: str
                translation_provider: "bhashini" | "unavailable"
                source_lang: str
                target_lang: str
                success: bool
                error: str | None
        """
        base_result = {
            "translated_text": text,
            "translation_provider": "unavailable",
            "source_lang": source_lang,
            "target_lang": target_lang,
            "success": False,
            "error": None,
        }

        # --- Validation ---
        if not text or not text.strip():
            base_result["error"] = "Empty text provided."
            return base_result

        if source_lang == target_lang:
            base_result["translated_text"] = text
            base_result["translation_provider"] = "passthrough"
            base_result["success"] = True
            return base_result

        if not self.supports_language(target_lang):
            base_result["error"] = f"Language '{target_lang}' is not supported by Bhashini."
            return base_result

        if not self.is_configured:
            base_result["error"] = "Bhashini API credentials not configured."
            return base_result

        # --- Step 1: Get pipeline config (model selection) ---
        try:
            pipeline_config = self._get_pipeline_config(source_lang, target_lang)
        except Exception as e:
            logger.warning(f"Bhashini pipeline config failed: {e}")
            base_result["error"] = f"Pipeline config failed: {e}"
            return base_result

        if not pipeline_config:
            base_result["error"] = "No translation model available for this language pair."
            return base_result

        # --- Step 2: Call compute endpoint ---
        try:
            translated = self._compute_translation(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang,
                pipeline_config=pipeline_config,
            )
            base_result["translated_text"] = translated
            base_result["translation_provider"] = "bhashini"
            base_result["success"] = True
            return base_result

        except Exception as e:
            logger.warning(f"Bhashini translation failed: {e}")
            base_result["error"] = f"Translation API failed: {e}"
            return base_result

    def _get_pipeline_config(self, source_lang: str, target_lang: str) -> Optional[dict]:
        """Fetch the Bhashini NMT pipeline configuration for a language pair.

        Returns the pipeline config dict or None if unavailable.
        """
        headers = {
            "Content-Type": "application/json",
            "userID": self.user_id,
            "ulcaApiKey": self.api_key,
        }

        payload = {
            "pipelineTasks": [
                {
                    "taskType": "translation",
                    "config": {
                        "language": {
                            "sourceLanguage": source_lang,
                            "targetLanguage": target_lang,
                        }
                    },
                }
            ],
            "pipelineRequestConfig": {
                "pipelineId": "64392f96daac500b55c543cd",
            },
        }

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(self.pipeline_url, json=payload, headers=headers)
            resp.raise_for_status()

        data = resp.json()

        # Extract the compute endpoint and service ID
        pipeline_response = data.get("pipelineResponseConfig", [])
        pipeline_inference = data.get("pipelineInferenceAPIEndPoint", {})

        if not pipeline_response:
            return None

        callback_url = pipeline_inference.get("callbackUrl", BHASHINI_COMPUTE_URL_DEFAULT)
        inference_key = pipeline_inference.get("inferenceApiKey", {}).get("value", "")

        config_item = pipeline_response[0].get("config", [{}])
        if isinstance(config_item, list) and config_item:
            service_id = config_item[0].get("serviceId", "")
        elif isinstance(config_item, dict):
            service_id = config_item.get("serviceId", "")
        else:
            service_id = ""

        return {
            "callback_url": callback_url,
            "inference_key": inference_key,
            "service_id": service_id,
        }

    def _compute_translation(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        pipeline_config: dict,
    ) -> str:
        """Call the Bhashini compute endpoint to perform translation."""
        callback_url = pipeline_config["callback_url"]
        inference_key = pipeline_config["inference_key"]
        service_id = pipeline_config["service_id"]

        headers = {
            "Content-Type": "application/json",
            "Authorization": inference_key,
        }

        payload = {
            "pipelineTasks": [
                {
                    "taskType": "translation",
                    "config": {
                        "language": {
                            "sourceLanguage": source_lang,
                            "targetLanguage": target_lang,
                        },
                        "serviceId": service_id,
                    },
                }
            ],
            "inputData": {
                "input": [{"source": text}],
            },
        }

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(callback_url, json=payload, headers=headers)
            resp.raise_for_status()

        data = resp.json()

        # Extract translated text
        pipeline_output = data.get("pipelineResponse", [])
        if pipeline_output:
            output_list = pipeline_output[0].get("output", [])
            if output_list:
                return output_list[0].get("target", text)

        return text

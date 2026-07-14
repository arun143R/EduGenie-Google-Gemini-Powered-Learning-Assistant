import logging
from google import genai
from google.genai import errors as genai_errors
from app.config import settings

logger = logging.getLogger(__name__)

class GeminiClient:
    """
    Singleton client wrapping Google Generative AI interactions.
    Provides lazy client configuration and comprehensive API error handling.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GeminiClient, cls).__new__(cls)
            cls._instance._client = None
            cls._instance._initialized = False
        return cls._instance

    def _initialize(self) -> None:
        if self._initialized:
            return

        api_key = settings.GEMINI_API_KEY
        if not api_key or api_key.startswith("your_"):
            logger.warning("Gemini API key is empty or not configured. Gemini wrapper will run in mock fallback mode.")
            return

        try:
            self._client = genai.Client(api_key=api_key)
            self._model_name = settings.GEMINI_MODEL_NAME
            self._initialized = True
            logger.info(f"Gemini AI client singleton successfully initialized with model: {self._model_name}")
        except Exception as e:
            logger.error(f"Error configuring Google Generative AI client: {e}")

    def call_gemini_api(self, prompt: str, mock_fallback_response: str) -> str:
        """
        Executes generation against Gemini API. Falls back to mock if configuration is missing,
        and logs granular details on API failures.
        """
        self._initialize()

        if not self._initialized or self._client is None:
            logger.warning("Gemini API is not fully configured/initialized. Returning mock fallback.")
            return mock_fallback_response

        try:
            logger.info("Executing Google Gemini API call...")
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=prompt,
            )

            if not response:
                logger.error("Gemini API returned None response.")
                return mock_fallback_response

            if not response.text:
                logger.error("Gemini API returned empty text (possibly blocked by safety filters or empty completion).")
                return mock_fallback_response

            return response.text

        except genai_errors.ClientError as e:
            logger.error(f"Gemini API client error (invalid request/auth): {e}")
            return f"[ERROR] Gemini API client error: {e}"
        except genai_errors.APIError as e:
            logger.error(f"Gemini API server error: {e}")
            return f"[ERROR] Gemini API error: {e}"
        except Exception as e:
            logger.error(f"Unexpected error calling Gemini API: {e}")
            return mock_fallback_response

# Instantiate the singleton client for application-wide reuse
gemini_client = GeminiClient()

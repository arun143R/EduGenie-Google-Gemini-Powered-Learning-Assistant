import logging
from app.config import settings

logger = logging.getLogger(__name__)

class LaMiniClient:
    """
    Singleton client managing HuggingFace LaMini-Flan-T5 pipeline.
    Ensures lazy-loading, singleton instantiation, CPU-only configuration,
    and fallback mock generation mode support.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LaMiniClient, cls).__new__(cls)
            cls._instance._generator = None
            cls._instance._initialized = False
        return cls._instance

    def _initialize(self) -> None:
        if self._initialized:
            return

        try:
            from transformers import pipeline
            import torch

            model_name = settings.HF_MODEL_NAME
            logger.info(f"Loading HuggingFace model lazily (CPU only): {model_name}...")
            
            # Build text-to-text generation pipeline on CPU only
            self._generator = pipeline(
                "text2text-generation",
                model=model_name,
                device="cpu"
            )
            self._initialized = True
            logger.info("LaMini model successfully loaded.")
        except Exception as e:
            logger.error(f"Failed to initialize HuggingFace model pipeline: {e}")

    def call_lamini_model(self, prompt: str, mock_fallback_response: str) -> str:
        """
        Executes text generation using the LaMini T5 pipeline. Lazy loads on first execution.
        """
        if not settings.USE_LOCAL_MODEL:
            logger.info("USE_LOCAL_MODEL is False. Skipping LaMini, returning mock fallback.")
            return mock_fallback_response

        # Lazy load on demand on the first request
        self._initialize()

        if not self._initialized or self._generator is None:
            logger.warning("LaMini model is not initialized/loaded. Returning mock fallback.")
            return mock_fallback_response

        try:
            logger.info("Executing HuggingFace generation...")
            outputs = self._generator(prompt, max_length=512, num_return_sequences=1)
            
            if outputs and len(outputs) > 0:
                return outputs[0].get("generated_text", "")
            return "[ERROR] Empty response from LaMini model"
        except Exception as e:
            logger.error(f"Failed to execute HuggingFace model inference: {e}")
            return mock_fallback_response

# Instantiate singleton client for application-wide reuse
lamini_client = LaMiniClient()

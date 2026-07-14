import logging
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from app.config import settings

logger = logging.getLogger(__name__)

_explain_tokenizer = None
_explain_model = None


def _load_model():
    global _explain_tokenizer, _explain_model
    if _explain_tokenizer is not None and _explain_model is not None:
        return

    model_name = getattr(settings, "HF_EXPLAIN_MODEL", "MBZUAI/LaMini-Flan-T5-783M")
    try:
        logger.info(f"Loading explanation model: {model_name}")
        _explain_tokenizer = AutoTokenizer.from_pretrained(model_name)
        _explain_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        logger.info("Explanation model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load explanation model: {e}")
        _explain_tokenizer = None
        _explain_model = None


def explain_topic(topic: str) -> str:
    if not topic or not topic.strip():
        return "Please provide a valid concept to explain."

    _load_model()

    if _explain_tokenizer is None or _explain_model is None:
        return (
            f"The concept of '{topic}' could not be explained because "
            f"the local model is not available. Please configure a valid model or API key."
        )

    input_text = (
        f"Explain the concept of '{topic}' in a simple and clear way "
        f"for a school student."
    )

    try:
        inputs = _explain_tokenizer(input_text, return_tensors="pt")
        outputs = _explain_model.generate(
            **inputs,
            max_new_tokens=300,
            temperature=0.7,
            top_k=50,
            top_p=0.95,
            do_sample=True,
        )
        explanation = _explain_tokenizer.decode(outputs[0], skip_special_tokens=True)
        return explanation
    except Exception as e:
        logger.error(f"Explanation generation failed: {e}")
        return f"An error occurred while generating the explanation for '{topic}'."

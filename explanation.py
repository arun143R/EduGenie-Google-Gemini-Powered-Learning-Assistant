from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app import models, schemas
from app.ai.prompts import get_explain_prompt
from app.ai.gemini import gemini_client

router = APIRouter(prefix="/api/explanation", tags=["Concept Explainer"])

@router.post("/explain", response_model=schemas.ExplainResponse)
async def explain_concept(
    payload: schemas.ExplainRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint to explain academic concepts.
    Adapts explanation difficulty level (beginner, intermediate, advanced)
    by framing the prompt accordingly and retrieving the AI result.
    """
    if not payload.concept.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Concept cannot be empty. Please provide a valid concept to explain."
        )

    prompt = get_explain_prompt(payload.concept, payload.level.value)

    fallback_text = (
        f"# {payload.concept}\n\n"
        f"## Overview\n\n"
        f"This is a placeholder explanation at the **{payload.level.value}** level. "
        f"Once a valid GEMINI_API_KEY is configured, the AI will explain this concept "
        f"with appropriate depth and vocabulary.\n\n"
        f"---\n\n"
        f"## Key Concepts\n\n"
        f"- Core principles of {payload.concept}\n"
        f"- Foundational terminology\n"
        f"- Practical relevance\n\n"
        f"---\n\n"
        f"## How to Enable Live Answers\n\n"
        f"1. Set `GEMINI_API_KEY` in your `.env` file\n"
        f"2. Restart the application\n"
        f"3. Re-ask to receive an AI-generated explanation"
    )
    explanation = gemini_client.call_gemini_api(prompt, mock_fallback_response=fallback_text)

    # 3. Log to History DB
    history_entry = models.History(
        user_id=current_user.id,
        activity_type="explain",
        input_text=f"Concept: {payload.concept} | Level: {payload.level}",
        output_text=explanation
    )
    db.add(history_entry)
    db.commit()
    db.refresh(history_entry)

    return schemas.ExplainResponse(
        concept=payload.concept,
        level=payload.level,
        explanation=explanation
    )

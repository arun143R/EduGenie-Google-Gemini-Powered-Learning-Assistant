from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app import models, schemas
from app.ai.prompts import get_qna_prompt
from app.ai.gemini import gemini_client

router = APIRouter(prefix="/api/qna", tags=["Q&A"])

@router.post("/ask", response_model=schemas.QnaResponse)
async def ask_question(
    payload: schemas.QnaRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint for students to ask academic questions.
    Queries the Gemini AI engine, saves the prompt/response to the user's history,
    and returns the structured response.
    """
    if not payload.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question content cannot be empty. Please provide a valid question to ask."
        )

    prompt = get_qna_prompt(payload.question)

    fallback_text = (
        f"# {payload.question}\n\n"
        f"## Overview\n\n"
        f"This is a placeholder response for your question. "
        f"Once a valid GEMINI_API_KEY is configured, the AI tutor will provide a detailed, "
        f"structured educational answer covering key concepts, examples, and real-world applications.\n\n"
        f"---\n\n"
        f"## How to Enable Live Answers\n\n"
        f"1. Set `GEMINI_API_KEY` in your `.env` file\n"
        f"2. Restart the application\n"
        f"3. Re-ask your question to receive an AI-generated response"
    )
    answer = gemini_client.call_gemini_api(prompt, mock_fallback_response=fallback_text)

    # 3. Log to History DB
    history_entry = models.History(
        user_id=current_user.id,
        activity_type="qna",
        input_text=payload.question,
        output_text=answer
    )
    db.add(history_entry)
    db.commit()
    db.refresh(history_entry)

    return schemas.QnaResponse(
        question=payload.question,
        answer=answer
    )

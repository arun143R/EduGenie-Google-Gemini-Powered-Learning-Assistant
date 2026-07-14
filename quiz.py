import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app import models, schemas
from app.ai.prompts import get_quiz_prompt
from app.ai.gemini import gemini_client

router = APIRouter(prefix="/api/quiz", tags=["MCQ Quiz Generator"])

@router.post("/generate", response_model=schemas.QuizCreateResponse)
async def generate_quiz(
    payload: schemas.QuizRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint to generate an MCQ quiz on a specific topic.
    Requests structured JSON output from Gemini containing questions, options, and correct answers.
    Persists the quiz in the DB and returns the quiz object to the client (hiding/including answers as needed,
    here we return the questions and options, but the schemas includes correct_answer for grading).
    """
    # 1. Structure the prompt to request specific JSON layout
    prompt = get_quiz_prompt(payload.topic, payload.num_questions)

    # 2. Setup realistic mock questions fallback
    mock_questions = [
        {
            "id": i,
            "question_text": f"Question {i} about {payload.topic}?",
            "options": [
                {"label": "A", "text": "This is a placeholder option A"},
                {"label": "B", "text": "This is the correct placeholder answer"},
                {"label": "C", "text": "This is a placeholder option C"},
                {"label": "D", "text": "This is a placeholder option D"}
            ],
            "correct_answer": "B"
        }
        for i in range(1, payload.num_questions + 1)
    ]
    mock_questions_str = json.dumps(mock_questions)

    # 3. Call Gemini API
    ai_response = gemini_client.call_gemini_api(prompt, mock_fallback_response=mock_questions_str)

    # Extract JSON block if API wrapped it in markdown code fences
    cleaned_response = ai_response.strip()
    if cleaned_response.startswith("```json"):
        cleaned_response = cleaned_response[7:]
    if cleaned_response.endswith("```"):
        cleaned_response = cleaned_response[:-3]
    cleaned_response = cleaned_response.strip()

    try:
        parsed_questions = json.loads(cleaned_response)
        if not isinstance(parsed_questions, list):
            raise ValueError("parsed_questions is not a list")
    except Exception:
        parsed_questions = mock_questions
        cleaned_response = mock_questions_str

    # 4. Save Quiz to database
    new_quiz = models.Quiz(
        user_id=current_user.id,
        topic=payload.topic,
        questions_json=cleaned_response,
        total_questions=len(parsed_questions)
    )
    db.add(new_quiz)
    db.commit()
    db.refresh(new_quiz)

    # Map database row columns to the response schema (omitting correct_answer)
    return schemas.QuizCreateResponse(
        quiz_id=new_quiz.id,
        topic=new_quiz.topic,
        questions=[schemas.MCQQuestionPublic(**q) for q in parsed_questions]
    )


@router.post("/{quiz_id}/submit", response_model=schemas.QuizSubmitResponse)
async def submit_quiz(
    quiz_id: int,
    payload: schemas.QuizSubmitRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint to grade a user's submitted MCQ answers.
    Retrieves the quiz from the database, compares user answers, updates the score,
    and returns grading feedback.
    """
    quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id, models.Quiz.user_id == current_user.id).first()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found. It may have been deleted or you may not have access to it."
        )

    try:
        original_questions = json.loads(quiz.questions_json)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse quiz questions from storage."
        )

    # Grade the quiz
    score = 0
    total = len(original_questions)
    
    for q in original_questions:
        q_id = q.get("id")
        correct_opt = q.get("correct_answer")
        
        # User answer for this question ID (cast payload dict keys to match standard parsing)
        user_opt = payload.answers.get(str(q_id)) or payload.answers.get(q_id)
        
        if user_opt and user_opt.upper().strip() == correct_opt.upper().strip():
            score += 1

    # Update Quiz Score in DB
    quiz.score = score
    db.commit()

    # Formulate feedback
    percentage = (score / total) * 100 if total > 0 else 0.0
    if percentage >= 80:
        feedback = "Excellent! You have a solid grasp of this topic."
    elif percentage >= 50:
        feedback = "Good effort! Revise the topic and try again to improve your score."
    else:
        feedback = "Keep learning! Don't hesitate to ask for conceptual clarification."

    # Log action to User History
    history_entry = models.History(
        user_id=current_user.id,
        activity_type="quiz",
        input_text=f"Quiz ID: {quiz_id} | Topic: {quiz.topic}",
        output_text=f"Score: {score}/{total} ({percentage:.1f}%)"
    )
    db.add(history_entry)
    db.commit()

    return schemas.QuizSubmitResponse(
        quiz_id=quiz.id,
        score=score,
        total_questions=total,
        percentage=percentage,
        feedback=feedback
    )

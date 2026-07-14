import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.auth import get_current_user
from app import models, schemas
from app.ai.prompts import get_roadmap_prompt
from app.ai.gemini import gemini_client

router = APIRouter(prefix="/api/roadmap", tags=["Learning Roadmap"])

@router.post("/generate", response_model=schemas.RoadmapResponse)
async def generate_roadmap(
    payload: schemas.RoadmapRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint to generate a personalized step-by-step learning roadmap on a given topic.
    Leverages Gemini to return structured learning nodes, stores it in database, and returns.
    """
    if not payload.topic.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Topic cannot be empty. Please provide a valid topic for your learning roadmap."
        )

    # 1. Structure the prompt to request structured JSON roadmap output
    prompt = get_roadmap_prompt(payload.topic)

    # 2. Setup mock fallback learning steps
    mock_steps = [
        {
            "step_number": 1,
            "title": f"Introduction to {payload.topic}",
            "description": f"Learn the fundamental concepts and basic terminologies of {payload.topic}.",
            "resources": ["Official Documentation", "Introductory Video Tutorial"]
        },
        {
            "step_number": 2,
            "title": f"Core Concepts of {payload.topic}",
            "description": f"Deep dive into standard methods, patterns, and logic used in {payload.topic}.",
            "resources": ["Textbook Chapter 2", "Hands-on Practice Exercises"]
        },
        {
            "step_number": 3,
            "title": f"Advanced Projects and Application",
            "description": f"Apply your skills to build a real-world project using {payload.topic} concepts.",
            "resources": ["GitHub Sandbox Repository", "Advanced Reference Guide"]
        }
    ]
    mock_steps_str = json.dumps(mock_steps)

    # 3. Call Gemini API
    ai_response = gemini_client.call_gemini_api(prompt, mock_fallback_response=mock_steps_str)

    # Clean code blocks
    cleaned_response = ai_response.strip()
    if cleaned_response.startswith("```json"):
        cleaned_response = cleaned_response[7:]
    if cleaned_response.endswith("```"):
        cleaned_response = cleaned_response[:-3]
    cleaned_response = cleaned_response.strip()

    try:
        parsed_steps = json.loads(cleaned_response)
        if not isinstance(parsed_steps, list):
            raise ValueError("parsed_steps is not a list")
    except Exception:
        parsed_steps = mock_steps
        cleaned_response = mock_steps_str

    # 4. Save Roadmap to Database
    new_roadmap = models.Roadmap(
        user_id=current_user.id,
        topic=payload.topic,
        roadmap_json=cleaned_response
    )
    db.add(new_roadmap)
    db.commit()
    db.refresh(new_roadmap)

    return schemas.RoadmapResponse(
        roadmap_id=new_roadmap.id,
        topic=new_roadmap.topic,
        steps=[schemas.RoadmapStep(**step) for step in parsed_steps]
    )


@router.get("/list", response_model=List[schemas.RoadmapResponse])
async def list_roadmaps(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve all learning roadmaps created by the current authenticated user.
    """
    db_roadmaps = db.query(models.Roadmap).filter(models.Roadmap.user_id == current_user.id).all()
    
    response_list = []
    for rm in db_roadmaps:
        try:
            steps = json.loads(rm.roadmap_json)
        except Exception:
            steps = []
        response_list.append(
            schemas.RoadmapResponse(
                roadmap_id=rm.id,
                topic=rm.topic,
                steps=[schemas.RoadmapStep(**s) for s in steps]
            )
        )
    return response_list

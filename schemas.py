from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import List, Dict, Optional


class ExplainLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class SummaryLength(str, Enum):
    short = "short"
    medium = "medium"
    long = "long"

# --- Authentication Schemas ---

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=120)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Username cannot be empty")
        return v.strip()

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")
        return v.strip().lower()

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# --- History Schemas ---

class HistoryBase(BaseModel):
    activity_type: str
    input_text: str
    output_text: str

class HistoryResponse(HistoryBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Q&A (Ask AI) Schemas ---

class QnaRequest(BaseModel):
    question: str = Field(..., min_length=1)

class QnaResponse(BaseModel):
    question: str
    answer: str


# --- Concept Explainer Schemas ---

class ExplainRequest(BaseModel):
    concept: str = Field(..., min_length=1)
    level: ExplainLevel = ExplainLevel.beginner

class ExplainResponse(BaseModel):
    concept: str
    level: str
    explanation: str


# --- Note Summarizer Schemas ---

class SummaryRequest(BaseModel):
    text: str = Field(..., min_length=1)
    length: SummaryLength = SummaryLength.medium

class SummaryResponse(BaseModel):
    original_length: int
    summary_length: int
    summary: str


# --- MCQ Quiz Schemas ---

class QuizRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)
    num_questions: int = Field(default=5, ge=3, le=15)

class MCQOption(BaseModel):
    label: str  # A, B, C, D
    text: str

class MCQQuestion(BaseModel):
    id: int
    question_text: str
    options: List[MCQOption]
    correct_answer: str  # A, B, C, or D

class MCQQuestionPublic(BaseModel):
    id: int
    question_text: str
    options: List[MCQOption]

class QuizCreateResponse(BaseModel):
    quiz_id: int
    topic: str
    questions: List[MCQQuestionPublic]

    model_config = ConfigDict(from_attributes=True)

class QuizSubmitRequest(BaseModel):
    answers: Dict[int, str]  # {question_id: selected_option_label}

class QuizSubmitResponse(BaseModel):
    quiz_id: int
    score: int
    total_questions: int
    percentage: float
    feedback: str


# --- Learning Roadmap Schemas ---

class RoadmapRequest(BaseModel):
    topic: str = Field(..., min_length=1)

class RoadmapStep(BaseModel):
    step_number: int
    title: str
    description: str
    resources: List[str] = []

class RoadmapResponse(BaseModel):
    roadmap_id: int
    topic: str
    steps: List[RoadmapStep]

    model_config = ConfigDict(from_attributes=True)

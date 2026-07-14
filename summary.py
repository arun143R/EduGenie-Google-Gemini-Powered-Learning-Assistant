from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app import models, schemas
from app.config import settings
from app.ai.prompts import get_summarize_prompt
from app.ai.gemini import gemini_client
from app.ai.lamini import lamini_client

router = APIRouter(prefix="/api/summary", tags=["Note Summarizer"])

@router.post("/summarize", response_model=schemas.SummaryResponse)
async def summarize_notes(
    payload: schemas.SummaryRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint for summarizing note text.
    Configures a HuggingFace LaMini-Flan-T5 query based on target length (short, medium, long),
    saves input and output length stats, and records the session in history.
    """
    input_text = payload.text.strip()
    if not input_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content to summarize cannot be empty. Please provide text to summarize."
        )

    prompt = get_summarize_prompt(input_text, payload.length.value)

    fallback_text = (
        f"# Summary of Your Notes\n\n"
        f"## Overview\n\n"
        f"This is a placeholder summary at the **{payload.length.value}** length. "
        f"Once a valid GEMINI_API_KEY is configured, the AI will generate a concise "
        f"summary tailored to your requested length.\n\n"
        f"---\n\n"
        f"## Key Points\n\n"
        f"- Main concepts from your input text\n"
        f"- Core arguments and ideas\n"
        f"- Important takeaways\n\n"
        f"---\n\n"
        f"## How to Enable Live Summaries\n\n"
        f"1. Set `GEMINI_API_KEY` in your `.env` file\n"
        f"2. Restart the application\n"
        f"3. Re-submit your text for an AI-generated summary"
    )
    
    if settings.USE_LOCAL_MODEL:
        summary_text = lamini_client.call_lamini_model(prompt, mock_fallback_response=fallback_text)
    else:
        summary_text = gemini_client.call_gemini_api(prompt, mock_fallback_response=fallback_text)

    # 3. Log to History DB
    history_entry = models.History(
        user_id=current_user.id,
        activity_type="summarize",
        input_text=f"Length: {payload.length} | Text: {input_text[:100]}...",
        output_text=summary_text
    )
    db.add(history_entry)
    db.commit()
    db.refresh(history_entry)

    return schemas.SummaryResponse(
        original_length=len(input_text),
        summary_length=len(summary_text),
        summary=summary_text
    )


from fastapi import UploadFile, File
import io
import pypdf

@router.post("/extract-text")
async def extract_text_from_file(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user)
):
    """
    Extracts raw text from uploaded PDF or TXT files.
    """
    filename = file.filename.lower()
    if not filename.endswith(('.pdf', '.txt')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Please upload a PDF or TXT file."
        )

    try:
        content = await file.read()
        if filename.endswith('.txt'):
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                text = content.decode('latin-1')
        else: # PDF
            pdf_file = io.BytesIO(content)
            reader = pypdf.PdfReader(pdf_file)
            extracted_pages = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_pages.append(page_text)
            text = "\n".join(extracted_pages)

        if not text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No text could be extracted from the uploaded file."
            )

        return {"text": text}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process file: {str(e)}"
        )

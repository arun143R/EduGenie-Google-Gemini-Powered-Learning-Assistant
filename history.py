from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.auth import get_current_user
from app import models, schemas

router = APIRouter(prefix="/api/history", tags=["User History"])

@router.get("/list", response_model=List[schemas.HistoryResponse])
async def list_history(
    activity_type: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve history entries for the current authenticated user.
    Optionally filter by activity_type (e.g. 'qna', 'explain', 'summarize', 'quiz', 'roadmap').
    """
    query = db.query(models.History).filter(models.History.user_id == current_user.id)
    
    if activity_type:
        query = query.filter(models.History.activity_type == activity_type)
        
    # Order by newest first
    entries = query.order_by(models.History.created_at.desc()).all()
    return entries


@router.delete("/delete/{history_id}", status_code=status.HTTP_200_OK)
async def delete_history_entry(
    history_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a specific history entry.
    """
    entry = db.query(models.History).filter(
        models.History.id == history_id,
        models.History.user_id == current_user.id
    ).first()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History entry not found. It may have been already deleted or you may not have access to it."
        )

    db.delete(entry)
    db.commit()
    return {"message": "History entry successfully deleted."}

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..core.security import get_db, get_current_user
from ..domain.exporting import export_whoop

router = APIRouter(prefix="/export", tags=["export"])

@router.post("/whoop")
def export_whoop_file(lang: str = "en", days: int = 365, db: Session = Depends(get_db), user=Depends(get_current_user)):
    xlsx, pdf = export_whoop(db, user.id, lang, days)
    return {"xlsx": xlsx, "pdf": pdf}

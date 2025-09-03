# schemas.py
from pydantic import BaseModel
from typing import Optional

class GoldPlanOut(BaseModel):
    id: int
    name: str
    plan_type: str
    duration_months: Optional[int]
    min_investment: float
    returns: Optional[str]
    description: Optional[str]

    class Config:
        orm_mode = True

class GoldPlanCreate(BaseModel):
    name: str
    plan_type: str
    duration_months: Optional[int] = None
    min_investment: float
    returns: Optional[str] = None
    description: Optional[str] = None

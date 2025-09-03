# models.py
from sqlalchemy import Column, Integer, String, Float, Text
from database import Base

class GoldPlan(Base):
    __tablename__ = "gold_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    plan_type = Column(String(50), nullable=False)      # e.g., 'Digital','ETF','SGB','SIP','MutualFund'
    duration_months = Column(Integer, nullable=True)    # None for flexible
    min_investment = Column(Float, nullable=False)      # rupees
    returns = Column(String(100), nullable=True)        # e.g., "2.5% + market appreciation"
    description = Column(Text, nullable=True)

# main.py
import os
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import SessionLocal, engine, Base
from models import GoldPlan
from schemas import GoldPlanOut, GoldPlanCreate
from dotenv import load_dotenv
import random
from typing import Union

load_dotenv()

app = FastAPI(title="Gold Plans API")

# Dependency: DB session per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables and seed sample data on startup (safe for small apps)
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

    # seed only if table empty
    db = SessionLocal()
    try:
        count = db.query(GoldPlan).count()
        if count == 0:
            sample = [
                GoldPlan(
                    name="Digital Gold",
                    plan_type="Digital",
                    duration_months=None,
                    min_investment=100.0,
                    returns="Market linked",
                    description="Buy digital gold in small quantities; stored by provider."
                ),
                GoldPlan(
                    name="Gold SIP",
                    plan_type="SIP",
                    duration_months=12,
                    min_investment=2000.0,
                    returns="Approx 5% (market linked)",
                    description="Monthly SIP into gold ETFs or digital gold."
                ),
                GoldPlan(
                    name="Sovereign Gold Bonds (SGB)",
                    plan_type="SGB",
                    duration_months=96,  # 8 years
                    min_investment=1000.0,
                    returns="2.5% interest + market appreciation",
                    description="Government-backed; interest paid annually; tax benefits on maturity."
                ),
                GoldPlan(
                    name="Gold ETF",
                    plan_type="ETF",
                    duration_months=None,
                    min_investment=5000.0,
                    returns="Market linked",
                    description="Traded on NSE/BSE; needs Demat; liquid."
                ),
                GoldPlan(
                    name="Gold Mutual Fund (FoF)",
                    plan_type="MutualFund",
                    duration_months=None,
                    min_investment=1000.0,
                    returns="Market linked",
                    description="Mutual fund investing in gold ETFs; SIP available; no Demat needed."
                )
            ]
            db.add_all(sample)
            db.commit()
    finally:
        db.close()

# --------------------------
# GET /suggest_gold_plans
# Optional query params:
#   budget (float) => max budget user said they can invest
#   duration_months (int) => desired minimum investment period
#   plan_type (str) => filter by plan type (Digital, ETF, SGB, SIP, MutualFund)
# --------------------------
@app.get("/suggest_gold_plans", response_model=Union[GoldPlanOut, dict])
def suggest_gold_plans(
    budget: Optional[float] = Query(None, description="User's budget in rupees"),
    duration_months: Optional[int] = Query(None, description="Desired minimum duration in months"),
    plan_type: Optional[str] = Query(None, description="Filter by plan type"),
    db: Session = Depends(get_db)
):
    q = db.query(GoldPlan)

    if budget is not None:
        q = q.filter(GoldPlan.min_investment <= budget)

    if duration_months is not None:
        # treat None duration_months in DB as flexible -> include them
        q = q.filter(
            (GoldPlan.duration_months == None) | (GoldPlan.duration_months <= duration_months)
        )

    if plan_type:
        q = q.filter(GoldPlan.plan_type.ilike(f"%{plan_type}%"))

    plans = q.order_by(GoldPlan.min_investment).all()
    print("plan", type(plans))
    if plans:
            suggested_plan = random.choice(plans)  # select one plan randomly
    else:
            suggested_plan = {"plan_name": "N/A", "description": "No plans available at the moment."}
    return suggested_plan

# GET single plan
@app.get("/plans/{plan_id}", response_model=GoldPlanOut)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(GoldPlan).filter(GoldPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    return plan

# Admin: create plan (protect this in prod)
@app.post("/plans", response_model=GoldPlanOut)
def create_plan(payload: GoldPlanCreate, db: Session = Depends(get_db)):
    plan = GoldPlan(**payload.dict())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan

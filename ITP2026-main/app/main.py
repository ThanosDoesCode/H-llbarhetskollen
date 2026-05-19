from __future__ import annotations
import datetime as dt
import json
from contextlib import asynccontextmanager
from typing import Dict, Tuple
from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from .db import get_session, Base, engine
from .models import Activity, EmissionFactor, User
from .schemas import (
    ActivityCreate,
    ActivityOut,
    EmissionFactorOut,
    UserCreate,
    UserOut,
    WeeklyReportOut,
)
from .services.emissions import Factor, FactorMap, calculate_co2e

@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Hållbarhetskollen API (starter)", lifespan=lifespan)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

@app.get("/ui", response_class=HTMLResponse)
def ui_home(request: Request) -> HTMLResponse:
    tpl = templates.get_template("index.html")
    html = tpl.render({"request": request})
    return HTMLResponse(html)

@app.get("/ui/users", response_class=HTMLResponse)
def ui_users(request: Request, db: Session = Depends(get_session)) -> HTMLResponse:
    users = list(db.execute(select(User).order_by(User.id.asc())).scalars().all())
    tpl = templates.get_template("create_user.html")
    html = tpl.render({"request": request, "users": users, "message": None, "error": None})
    return HTMLResponse(html)

@app.post("/ui/users", response_class=HTMLResponse)
def ui_create_user(request: Request, name: str = Form(default=""), db: Session = Depends(get_session)) -> HTMLResponse:
    name = name.strip()
    users = list(db.execute(select(User).order_by(User.id.asc())).scalars().all())
    tpl = templates.get_template("create_user.html")
    if not name:
        html = tpl.render({"request": request, "users": users, "message": None, "error": "Name får inte vara tomt."})
        return HTMLResponse(html)
    user = User(name=name)
    db.add(user)
    db.commit()
    users = list(db.execute(select(User).order_by(User.id.asc())).scalars().all())
    html = tpl.render({"request": request, "users": users, "message": f"Skapade användare '{user.name}'", "error": None})
    return HTMLResponse(html)

@app.post("/ui/users/{user_id}/delete", response_class=HTMLResponse)
def ui_delete_user(user_id: int, request: Request, db: Session = Depends(get_session)) -> HTMLResponse:
    tpl = templates.get_template("create_user.html")
    user = db.get(User, user_id)
    if not user:
        users = list(db.execute(select(User).order_by(User.id.asc())).scalars().all())
        html = tpl.render({"request": request, "users": users, "message": None, "error": f"Användare {user_id} finns inte."})
        return HTMLResponse(html)
    deleted_name = user.name
    db.delete(user)
    db.commit()
    users = list(db.execute(select(User).order_by(User.id.asc())).scalars().all())
    html = tpl.render({"request": request, "users": users, "message": f"Raderade användare '{deleted_name}' (id={user_id})", "error": None})
    return HTMLResponse(html)

@app.get("/ui/activities", response_class=HTMLResponse)
def ui_activities(request: Request, db: Session = Depends(get_session)) -> HTMLResponse:
    users = list(db.execute(select(User).order_by(User.id.asc())).scalars().all())
    factors = list(db.execute(select(EmissionFactor)).scalars().all())
    categories = sorted(set(f.category for f in factors))
    activities_raw = list(db.execute(select(Activity).order_by(Activity.id.desc())).scalars().all())
    user_map = {u.id: u.name for u in users}
    factor_map = _load_factor_map(db)
    activities_out = []
    for a in activities_raw:
        try:
            co2e = calculate_co2e(a.category, a.key, a.amount, factor_map)
        except KeyError:
            co2e = None
        activities_out.append({
            "user_name": user_map.get(a.user_id, "?"),
            "category": a.category,
            "key": a.key,
            "amount": a.amount,
            "date": a.date,
            "co2e": co2e,
        })
    factors_json = json.dumps([{"category": f.category, "key": f.key} for f in factors])
    tpl = templates.get_template("activities.html")
    html = tpl.render({
        "request": request,
        "users": users,
        "factors": factors,
        "categories": categories,
        "factors_json": factors_json,
        "activities": activities_out,
        "message": None,
        "error": None,
    })
    return HTMLResponse(html)

@app.post("/ui/activities", response_class=HTMLResponse)
def ui_create_activity(
    request: Request,
    user_id: int = Form(...),
    category: str = Form(...),
    key: str = Form(...),
    amount: float = Form(...),
    date: str = Form(...),
    db: Session = Depends(get_session),
) -> HTMLResponse:
    users = list(db.execute(select(User).order_by(User.id.asc())).scalars().all())
    factors = list(db.execute(select(EmissionFactor)).scalars().all())
    categories = sorted(set(f.category for f in factors))
    factors_json = json.dumps([{"category": f.category, "key": f.key} for f in factors])
    tpl = templates.get_template("activities.html")
    try:
        parsed_date = dt.date.fromisoformat(date)
    except ValueError:
        html = tpl.render({"request": request, "users": users, "factors": factors, "categories": categories, "factors_json": factors_json, "activities": [], "message": None, "error": "Ogiltigt datumformat."})
        return HTMLResponse(html)
    activity = Activity(user_id=user_id, category=category, key=key, amount=amount, date=parsed_date)
    db.add(activity)
    db.commit()
    activities_raw = list(db.execute(select(Activity).order_by(Activity.id.desc())).scalars().all())
    user_map = {u.id: u.name for u in users}
    factor_map = _load_factor_map(db)
    activities_out = []
    for a in activities_raw:
        try:
            co2e = calculate_co2e(a.category, a.key, a.amount, factor_map)
        except KeyError:
            co2e = None
        activities_out.append({
            "user_name": user_map.get(a.user_id, "?"),
            "category": a.category,
            "key": a.key,
            "amount": a.amount,
            "date": a.date,
            "co2e": co2e,
        })
    html = tpl.render({"request": request, "users": users, "factors": factors, "categories": categories, "factors_json": factors_json, "activities": activities_out, "message": "Aktivitet sparad!", "error": None})
    return HTMLResponse(html)

@app.get("/ui/reports/weekly", response_class=HTMLResponse)
def ui_weekly_report(
    request: Request,
    user_id: int | None = None,
    week_start: str | None = None,
    db: Session = Depends(get_session),
) -> HTMLResponse:
    users = list(db.execute(select(User).order_by(User.id.asc())).scalars().all())
    tpl = templates.get_template("weekly.html")
    total_co2e = None
    week_end = None
    error = None
    if user_id is not None and week_start:
        try:
            start = dt.date.fromisoformat(week_start)
            end = start + dt.timedelta(days=6)
            week_end = str(end)
        except ValueError:
            error = "Ogiltigt datumformat, använd YYYY-MM-DD."
        else:
            stmt = (
                select(Activity)
                .where(Activity.user_id == user_id)
                .where(Activity.date >= start)
                .where(Activity.date <= end)
            )
            activities = list(db.execute(stmt).scalars().all())
            factor_map = _load_factor_map(db)
            total_co2e = 0.0
            for a in activities:
                try:
                    total_co2e += calculate_co2e(a.category, a.key, a.amount, factor_map)
                except KeyError:
                    continue
    html = tpl.render({
        "request": request,
        "users": users,
        "selected_user_id": user_id,
        "week_start": week_start,
        "week_end": week_end,
        "total_co2e": total_co2e,
        "error": error,
    })
    return HTMLResponse(html)

@app.post("/users", response_model=UserOut)
def create_user(payload: UserCreate, db: Session = Depends(get_session)) -> User:
    user = User(name=payload.name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_session)) -> list[User]:
    return list(db.execute(select(User)).scalars().all())

def _load_factor_map(db: Session) -> FactorMap:
    factors = db.execute(select(EmissionFactor)).scalars().all()
    mapping: FactorMap = {}
    for f in factors:
        mapping[(f.category, f.key)] = Factor(category=f.category, key=f.key, unit=f.unit, co2e_per_unit=f.co2e_per_unit)
    return mapping

@app.get("/emission-factors", response_model=list[EmissionFactorOut])
def list_factors(db: Session = Depends(get_session)) -> list[EmissionFactor]:
    return list(db.execute(select(EmissionFactor)).scalars().all())

@app.post("/activities", response_model=ActivityOut)
def create_activity(payload: ActivityCreate, db: Session = Depends(get_session)) -> ActivityOut:
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    activity = Activity(
        user_id=payload.user_id,
        category=payload.category,
        key=payload.key,
        amount=payload.amount,
        date=payload.date,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    factors = _load_factor_map(db)
    try:
        co2e = calculate_co2e(activity.category, activity.key, activity.amount, factors)
    except KeyError:
        co2e = None
    return ActivityOut(
        id=activity.id,
        user_id=activity.user_id,
        category=activity.category,
        key=activity.key,
        amount=activity.amount,
        date=activity.date,
        co2e=co2e,
    )

@app.get("/activities", response_model=list[ActivityOut])
def list_activities(
    user_id: int | None = Query(default=None),
    db: Session = Depends(get_session),
) -> list[ActivityOut]:
    stmt = select(Activity)
    if user_id is not None:
        stmt = stmt.where(Activity.user_id == user_id)
    activities = list(db.execute(stmt).scalars().all())
    factors = _load_factor_map(db)
    out: list[ActivityOut] = []
    for a in activities:
        try:
            co2e = calculate_co2e(a.category, a.key, a.amount, factors)
        except KeyError:
            co2e = None
        out.append(
            ActivityOut(
                id=a.id,
                user_id=a.user_id,
                category=a.category,
                key=a.key,
                amount=a.amount,
                date=a.date,
                co2e=co2e,
            )
        )
    return out

def _week_bounds(week_start: dt.date) -> tuple[dt.date, dt.date]:
    return week_start, week_start + dt.timedelta(days=6)

@app.get("/reports/weekly", response_model=WeeklyReportOut)
def weekly_report(
    user_id: int = Query(...),
    week_start: dt.date = Query(..., description="Veckans startdatum (måndag)"),
    db: Session = Depends(get_session),
) -> WeeklyReportOut:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    start, end = _week_bounds(week_start)
    stmt = (
        select(Activity)
        .where(Activity.user_id == user_id)
        .where(Activity.date >= start)
        .where(Activity.date <= end)
    )
    activities = list(db.execute(stmt).scalars().all())
    factors = _load_factor_map(db)
    total = 0.0
    for a in activities:
        try:
            total += calculate_co2e(a.category, a.key, a.amount, factors)
        except KeyError:
            continue
    return WeeklyReportOut(user_id=user_id, week_start=start, week_end=end, total_co2e=total)
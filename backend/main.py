import time
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy.orm import Session
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

import models
import schemas
import elo
from database import engine, get_db, Base
from llm_clients import generate_response, pick_two_models, AVAILABLE_MODELS

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Model Testing Arena",
    description="Head-to-head LLM evaluation platform with Elo ranking, "
                "latency/cost tracking, and Prometheus metrics.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Prometheus metrics ----
REQUEST_COUNT = Counter("arena_requests_total", "Total requests", ["endpoint"])
BATTLE_LATENCY = Histogram("arena_battle_latency_seconds", "Battle endpoint latency")


def get_or_create_rating(db: Session, model_name: str) -> models.ModelRating:
    rating = db.query(models.ModelRating).filter_by(model_name=model_name).first()
    if not rating:
        rating = models.ModelRating(model_name=model_name)
        db.add(rating)
        db.commit()
        db.refresh(rating)
    return rating


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/models")
def list_models():
    REQUEST_COUNT.labels(endpoint="/models").inc()
    return {"models": AVAILABLE_MODELS}


@app.post("/battle", response_model=schemas.BattleResponse)
def battle(req: schemas.BattleRequest, db: Session = Depends(get_db)):
    REQUEST_COUNT.labels(endpoint="/battle").inc()
    start = time.time()

    if not req.prompt or not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    model_a, model_b = pick_two_models(req.model_a, req.model_b)

    response_a, latency_a, cost_a = generate_response(model_a, req.prompt)
    response_b, latency_b, cost_b = generate_response(model_b, req.prompt)

    battle_record = models.Battle(
        prompt=req.prompt,
        model_a=model_a,
        model_b=model_b,
        response_a=response_a,
        response_b=response_b,
        latency_a_ms=latency_a,
        latency_b_ms=latency_b,
        cost_a_usd=cost_a,
        cost_b_usd=cost_b,
    )
    db.add(battle_record)
    db.commit()
    db.refresh(battle_record)

    BATTLE_LATENCY.observe(time.time() - start)

    return schemas.BattleResponse(
        battle_id=battle_record.id,
        prompt=req.prompt,
        model_a=model_a,
        model_b=model_b,
        response_a=response_a,
        response_b=response_b,
        latency_a_ms=latency_a,
        latency_b_ms=latency_b,
        cost_a_usd=cost_a,
        cost_b_usd=cost_b,
    )


@app.post("/vote")
def vote(req: schemas.VoteRequest, db: Session = Depends(get_db)):
    REQUEST_COUNT.labels(endpoint="/vote").inc()

    if req.choice not in ("a", "b", "tie"):
        raise HTTPException(status_code=400, detail="choice must be 'a', 'b', or 'tie'")

    battle_record = db.query(models.Battle).filter_by(id=req.battle_id).first()
    if not battle_record:
        raise HTTPException(status_code=404, detail="Battle not found")
    if battle_record.winner is not None:
        raise HTTPException(status_code=409, detail="This battle has already been voted on")

    battle_record.winner = req.choice
    db.add(models.Vote(battle_id=req.battle_id, choice=req.choice))

    rating_a = get_or_create_rating(db, battle_record.model_a)
    rating_b = get_or_create_rating(db, battle_record.model_b)

    new_a, new_b = elo.update_ratings(rating_a.elo_rating, rating_b.elo_rating, req.choice)

    for rating, new_elo, is_winner, is_loser, latency, cost in (
        (rating_a, new_a, req.choice == "a", req.choice == "b", battle_record.latency_a_ms, battle_record.cost_a_usd),
        (rating_b, new_b, req.choice == "b", req.choice == "a", battle_record.latency_b_ms, battle_record.cost_b_usd),
    ):
        rating.elo_rating = new_elo
        rating.total_battles += 1
        if is_winner:
            rating.wins += 1
        elif is_loser:
            rating.losses += 1
        else:
            rating.ties += 1
        # running average
        n = rating.total_battles
        rating.avg_latency_ms = round(((rating.avg_latency_ms * (n - 1)) + latency) / n, 2)
        rating.avg_cost_usd = round(((rating.avg_cost_usd * (n - 1)) + cost) / n, 6)

    db.commit()

    return {
        "battle_id": req.battle_id,
        "winner": req.choice,
        "new_elo_a": new_a,
        "new_elo_b": new_b,
    }


@app.get("/leaderboard", response_model=list[schemas.LeaderboardEntry])
def leaderboard(db: Session = Depends(get_db)):
    REQUEST_COUNT.labels(endpoint="/leaderboard").inc()
    ratings = db.query(models.ModelRating).order_by(models.ModelRating.elo_rating.desc()).all()
    return ratings

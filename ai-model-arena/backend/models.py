from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from database import Base


class ModelRating(Base):
    __tablename__ = "model_ratings"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, unique=True, index=True)
    elo_rating = Column(Float, default=1200.0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    ties = Column(Integer, default=0)
    total_battles = Column(Integer, default=0)
    avg_latency_ms = Column(Float, default=0.0)
    avg_cost_usd = Column(Float, default=0.0)


class Battle(Base):
    __tablename__ = "battles"

    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(Text)
    model_a = Column(String)
    model_b = Column(String)
    response_a = Column(Text)
    response_b = Column(Text)
    latency_a_ms = Column(Float)
    latency_b_ms = Column(Float)
    cost_a_usd = Column(Float)
    cost_b_usd = Column(Float)
    winner = Column(String, nullable=True)  # "a" | "b" | "tie" | None (unvoted)
    created_at = Column(DateTime, default=datetime.utcnow)


class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    battle_id = Column(Integer, ForeignKey("battles.id"))
    choice = Column(String)  # "a" | "b" | "tie"
    created_at = Column(DateTime, default=datetime.utcnow)

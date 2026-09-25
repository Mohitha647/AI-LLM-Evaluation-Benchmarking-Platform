from typing import Optional
from pydantic import BaseModel, ConfigDict


class BattleRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    prompt: str
    model_a: Optional[str] = None   # if omitted, arena picks 2 random models
    model_b: Optional[str] = None


class BattleResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    battle_id: int
    prompt: str
    model_a: str
    model_b: str
    response_a: str
    response_b: str
    latency_a_ms: float
    latency_b_ms: float
    cost_a_usd: float
    cost_b_usd: float


class VoteRequest(BaseModel):
    battle_id: int
    choice: str  # "a" | "b" | "tie"


class LeaderboardEntry(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)
    model_name: str
    elo_rating: float
    wins: int
    losses: int
    ties: int
    total_battles: int
    avg_latency_ms: float
    avg_cost_usd: float

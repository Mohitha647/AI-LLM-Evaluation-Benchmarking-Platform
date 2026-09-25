# ⚔️ AI Model Testing Arena

A full-stack platform for **blind head-to-head LLM evaluation**, ranked with an
Elo rating system (same family of algorithm used by LMSYS Chatbot Arena),
with latency/cost tracking, Prometheus metrics, Docker containerization, and
a GitHub Actions CI/CD pipeline — built to demonstrate both **AI/ML** and
**Cloud/DevOps** skills in a single project.

---

## Features

- **15+ pluggable models** battle head-to-head on any prompt you submit
- **Elo ranking system** — ratings update after every vote, just like chess ratings
- **Latency & cost tracking** per model, per battle, with running averages
- **Idempotent voting** — a battle can only be voted on once (duplicate-safe)
- **Mock mode** — runs completely offline with simulated model responses
  (no API keys needed to demo it); flip one env var to call real
  OpenAI/Anthropic APIs
- **Prometheus `/metrics` endpoint** for observability
- **Dockerized** backend + frontend via `docker-compose`
- **CI/CD** via GitHub Actions — automated tests + Docker image build/push
- **REST API** documented automatically at `/docs` (FastAPI Swagger UI)

---

## Tech Stack

| Layer      | Technology                                  |
|------------|----------------------------------------------|
| Backend    | FastAPI, Python, SQLAlchemy, Pydantic        |
| Database   | SQLite (dev) — swap `DATABASE_URL` for Postgres in prod |
| Frontend   | HTML, Tailwind CSS (CDN), vanilla JavaScript |
| Monitoring | prometheus-client                            |
| Container  | Docker, docker-compose                       |
| CI/CD      | GitHub Actions                               |
| Testing    | pytest, FastAPI TestClient                   |

---

## Project Structure

```
ai-model-arena/
├── backend/
│   ├── main.py           # FastAPI app & routes
│   ├── models.py         # SQLAlchemy ORM models
│   ├── schemas.py        # Pydantic request/response schemas
│   ├── elo.py             # Elo rating algorithm
│   ├── llm_clients.py    # Pluggable mock/real LLM client layer
│   ├── database.py       # DB session/engine setup
│   ├── requirements.txt
│   └── tests/
│       └── test_api.py   # pytest test suite
├── frontend/
│   └── index.html        # Single-page arena UI
├── .github/workflows/
│   └── ci-cd.yml          # GitHub Actions pipeline
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## How to Run — Step by Step

You can run this **three ways**. Pick whichever suits your demo.

### Option A — Quickest: Python virtual environment (no Docker)

```bash
# 1. Unzip and enter the project
unzip ai-model-arena.zip
cd ai-model-arena/backend

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API is now live at **http://localhost:8000**
Interactive API docs (Swagger UI): **http://localhost:8000/docs**

Now open the frontend:
```bash
# In a new terminal, from the project root
cd ../frontend
python3 -m http.server 8080
```
Open **http://localhost:8080** in your browser. The API URL field at the top
defaults to `http://localhost:8000` — leave it as is.

---

### Option B — Docker (single container, backend only)

```bash
cd ai-model-arena
docker build -t ai-model-arena .
docker run -p 8000:8000 ai-model-arena
```
API live at **http://localhost:8000**. Open `frontend/index.html` directly
in your browser (or serve it as in Option A).

---

### Option C — docker-compose (backend + frontend together — recommended)

```bash
cd ai-model-arena
docker-compose up --build
```
- Backend: **http://localhost:8000**
- Frontend: **http://localhost:8080**
- Metrics: **http://localhost:8000/metrics**

Stop it with `docker-compose down`.

---

## Using the App

1. Open the frontend in your browser.
2. Type a prompt (e.g. *"Explain how binary search works"*) and click **Start Battle**.
3. Two anonymous model responses (Model A / Model B) appear side by side,
   along with latency and estimated cost.
4. Vote for the better one (or tie). The models' identities are revealed
   after voting, and their **Elo ratings update automatically**.
5. Check the **Leaderboard** at the bottom to see rankings, win/loss record,
   average latency, and average cost per model.

---

## Switching from Mock Mode to Real LLM APIs

By default the arena runs in `MOCK_MODE=true`, simulating realistic latency
and responses so the whole project works with **zero API keys and zero cost**
— ideal for demos and interviews.

To use real models:

1. Copy `.env.example` to `backend/.env`
2. Set:
   ```
   MOCK_MODE=false
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   ```
3. Restart the backend. Models whose names contain `gpt` or `claude` will
   now route to the real OpenAI/Anthropic APIs; all others keep using
   the mock generator (extend `llm_clients.py` to add more real providers).

---

## Running Tests

```bash
cd backend
pytest -v
```
Covers: health check, model listing, full battle→vote→Elo-update flow,
duplicate-vote rejection (idempotency), and input validation.

---

## CI/CD Pipeline (GitHub Actions)

`.github/workflows/ci-cd.yml` runs automatically on every push to `main`:

1. **Test job** — installs dependencies, runs the full pytest suite
2. **Build & push job** (only if tests pass) — builds the Docker image and
   pushes it to Docker Hub

To enable the push step, add these secrets in your GitHub repo
(**Settings → Secrets and variables → Actions**):
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

A commented-out `deploy` job is included as a starting point for deploying
to AWS ECS, GCP Cloud Run, or Azure — fill in your cloud credentials as
repo secrets and uncomment it once you provision the infrastructure.

---

## Deploying to the Cloud (summary)

**AWS (ECS/Fargate):**
1. Push the Docker image to Amazon ECR (`aws ecr create-repository`, `docker push`)
2. Create an ECS cluster + Fargate service pointing at that image, port 8000
3. Put an Application Load Balancer in front for a stable public URL
4. Add auto-scaling policy based on CPU/request count

**GCP (Cloud Run) — simplest option:**
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/ai-model-arena
gcloud run deploy ai-model-arena --image gcr.io/PROJECT_ID/ai-model-arena --port 8000 --allow-unauthenticated
```
Cloud Run auto-scales (including to zero) out of the box.

**Monitoring in production:** point a Prometheus server at `/metrics`, or
scrape it into Grafana Cloud / CloudWatch for dashboards and alerting.

---

## Resume Bullet (once deployed + load-tested)

> Built an AI model evaluation platform benchmarking LLMs on accuracy,
> latency, and cost using an Elo ranking system; containerized with Docker
> and deployed on [AWS ECS / GCP Cloud Run] with CI/CD via GitHub Actions,
> handling [X] req/sec with [X]ms median latency under load testing.

Fill in the `[X]` values using the `locustfile.py` load test from earlier —
point it at this API's `/battle` and `/leaderboard` endpoints once deployed.

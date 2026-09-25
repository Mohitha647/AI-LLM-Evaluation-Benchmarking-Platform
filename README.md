# AI Model Testing Arena

A full-stack platform for \*\*blind head-to-head LLM evaluation, where multiple AI models are compared using the same prompts and ranked with an "Elo rating system". It tracks user votes, response latency, and estimated API cost, with "Prometheus monitoring, Docker containerization, and GitHub Actions CI/CD".

The project was created to demonstrate practical "AI/ML and Cloud/DevOps skills" through a real-world model evaluation system, covering LLM API integration, backend development, database management, performance monitoring, automated testing, and deployment.



## Features

* **15+ pluggable models** battle head-to-head on any prompt you submit
* **Elo ranking system** — ratings update after every vote, just like chess ratings
* **Latency \& cost tracking** per model, per battle, with running averages
* **Idempotent voting** — a battle can only be voted on once (duplicate-safe)
* **Mock mode** — runs completely offline with simulated model responses
(no API keys needed to demo it); flip one env var to call real
OpenAI/Anthropic APIs
* **Prometheus `/metrics` endpoint** for observability
* **Dockerized** backend + frontend via `docker-compose`
* **CI/CD** via GitHub Actions — automated tests + Docker image build/push
* **REST API** documented automatically at `/docs` (FastAPI Swagger UI)



## Tech Stack

|Layer|Technology|
|-|-|
|Backend|FastAPI, Python, SQLAlchemy, Pydantic|
|Database|SQLite (dev) — swap `DATABASE\_URL` for Postgres in prod|
|Frontend|HTML, Tailwind CSS (CDN), vanilla JavaScript|
|Monitoring|prometheus-client|
|Container|Docker, docker-compose|
|CI/CD|GitHub Actions|
|Testing|pytest, FastAPI TestClient|



## Project Structure


ai-model-arena/
├── backend/
│   ├── main.py           # FastAPI app \& routes
│   ├── models.py         # SQLAlchemy ORM models
│   ├── schemas.py        # Pydantic request/response schemas
│   ├── elo.py             # Elo rating algorithm
│   ├── llm\_clients.py    # Pluggable mock/real LLM client layer
│   ├── database.py       # DB session/engine setup
│   ├── requirements.txt
│   └── tests/
│       └── test\_api.py   # pytest test suite
├── frontend/
│   └── index.html        # Single-page arena UI
├── .github/workflows/
│   └── ci-cd.yml          # GitHub Actions pipeline
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md



## How to Run — Step by Step

You can run this **three ways**. Pick whichever suits your demo.

### Option A — Quickest: Python virtual environment (no Docker)


# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\\Scripts\\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API is now live at **http://localhost:8000**
Interactive API docs (Swagger UI): **http://localhost:8000/docs**

Now open the frontend:


# In a new terminal, from the project root
cd ../frontend
python3 -m http.server 8080


Open **http://localhost:8080** in your browser. The API URL field at the top
defaults to `http://localhost:8000` — leave it as is.



### Option B — Docker (single container, backend only)


cd ai-model-arena
docker build -t ai-model-arena .
docker run -p 8000:8000 ai-model-arena


API live at **http://localhost:8000**. Open `frontend/index.html` directly
in your browser (or serve it as in Option A).



### Option C — docker-compose (backend + frontend together — recommended)


cd ai-model-arena
docker-compose up --build



* Backend: **http://localhost:8000**
* Frontend: **http://localhost:8080**
* Metrics: **http://localhost:8000/metrics**

Stop it with `docker-compose down`.



## Using the App

1. Open the frontend in your browser.
2. Type a prompt (e.g. *"Explain how binary search works"*) and click **Start Battle**.
3. Two anonymous model responses (Model A / Model B) appear side by side,
along with latency and estimated cost.
4. Vote for the better one (or tie). The models' identities are revealed
after voting, and their **Elo ratings update automatically**.
5. Check the **Leaderboard** at the bottom to see rankings, win/loss record,
average latency, and average cost per model.



## Switching from Mock Mode to Real LLM APIs

By default the arena runs in `MOCK\_MODE=true`, simulating realistic latency
and responses so the whole project works with **zero API keys and zero cost**
— ideal for demos and interviews.

To use real models:

1. Copy `.env.example` to `backend/.env`
2. Set:


   MOCK\_MODE=false
   OPENAI\_API\_KEY=sk-...
   ANTHROPIC\_API\_KEY=sk-ant-...
   

3. Restart the backend. Models whose names contain `gpt` or `claude` will
now route to the real OpenAI/Anthropic APIs; all others keep using
the mock generator (extend `llm\_clients.py` to add more real providers).



## Running Tests


cd backend
pytest -v


Covers: health check, model listing, full battle→vote→Elo-update flow,
duplicate-vote rejection (idempotency), and input validation.



## CI/CD Pipeline (GitHub Actions)

`.github/workflows/ci-cd.yml` runs automatically on every push to `main`:

1. **Test job** — installs dependencies, runs the full pytest suite
2. **Build \& push job** (only if tests pass) — builds the Docker image and
pushes it to Docker Hub

To enable the push step, add these secrets in your GitHub repo
(**Settings → Secrets and variables → Actions**):

* `DOCKERHUB\_USERNAME`
* `DOCKERHUB\_TOKEN`

A commented-out `deploy` job is included as a starting point for deploying
to AWS ECS, GCP Cloud Run, or Azure — fill in your cloud credentials as
repo secrets and uncomment it once you provision the infrastructure.

\---

## Deploying to the Cloud (summary)

**AWS (ECS/Fargate):**

1. Push the Docker image to Amazon ECR (`aws ecr create-repository`, `docker push`)
2. Create an ECS cluster + Fargate service pointing at that image, port 8000
3. Put an Application Load Balancer in front for a stable public URL
4. Add auto-scaling policy based on CPU/request count

**GCP (Cloud Run) — simplest option:**

```bash
gcloud builds submit --tag gcr.io/PROJECT\_ID/ai-model-arena
gcloud run deploy ai-model-arena --image gcr.io/PROJECT\_ID/ai-model-arena --port 8000 --allow-unauthenticated
```

Cloud Run auto-scales (including to zero) out of the box.

**Monitoring in production:** point a Prometheus server at `/metrics`, or
scrape it into Grafana Cloud / CloudWatch for dashboards and alerting.


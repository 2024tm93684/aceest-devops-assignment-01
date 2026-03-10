# ACEest Fitness & Gym — DevOps CI/CD Pipeline

![CI/CD Pipeline](https://github.com/2024tm93684/aceest-devops-assignment-01/actions/workflows/main.yml/badge.svg)

Flask REST API built version-by-version from 10 provided tkinter source files,
demonstrating a complete DevOps workflow with automated testing, containerisation,
and dual CI/CD pipelines via GitHub Actions and Jenkins.

## Version History (tkinter source → Flask feature)
| Version | Source File           | Flask Feature Added                              |
|---------|-----------------------|--------------------------------------------------|
| v1.0    | Aceestver-1_0.py      | Initial Flask API — 3 programs, calorie calc     |
| v1.1    | Aceestver-1_1.py      | Richer PROGRAMS dict, improved validation        |
| v1.1.2  | Aceestver1_1_2.py     | In-memory client store, /clients, /export        |
| v2.0.1  | Aceestver2_0_1.py     | SQLite DB, /client persists, /progress, tests    |
| v2.1.2  | Aceestver-2_1_2.py    | Code refactor — no new endpoints                 |
| v2.2.1  | Aceestver-2_2_1.py    | GET /progress/<client>                           |
| v2.2.4  | Aceestver-2_2_4.py    | 4 programs, /workout, /metrics, /bmi             |
| v3.0.1  | Aceestver-3_0_1.py    | GET /status endpoint                             |
| v3.1.2  | Aceestver-3_1_2.py    | POST /login, GET /users, Jenkinsfile             |
| v3.2.4  | Aceestver-3_2_4.py    | /generate_program, /generate_pdf, /membership    |

## Local Setup and Execution
```bash
# 1. Clone the repository
git clone https://github.com/2024tm93684/aceest-devops-assignment-01.git
cd aceest-devops-assignment-01

# 2. Install dependencies
pip install -r requirements.txt
# OR
pip3 install -r requirements.txt

# 3. Run the Flask application
python app.py
# API is now live at http://localhost:8080

# 4. Verify it's running
curl http://localhost:8080/health
# Expected: {"status": "healthy"}
```

## All API Endpoints
| Method | Endpoint                     | Description                   |
|--------|------------------------------|-------------------------------|
| GET    | /                            | API status                    |
| GET    | /health                      | Health check                  |
| GET    | /status                      | Live client count             |
| GET    | /programs                    | List all programs             |
| GET    | /program/<name>              | Program detail                |
| POST   | /calculate_calories          | Calorie calculation           |
| POST   | /client                      | Save client to DB             |
| GET    | /client/<name>               | Get client from DB            |
| GET    | /clients                     | List all clients              |
| GET    | /export_clients              | Export client data as JSON    |
| GET    | /site_metrics                | Gym capacity & break-even     |
| POST   | /progress                    | Log weekly adherence          |
| GET    | /progress/<name>             | Get adherence chart data      |
| POST   | /workout                     | Log workout session           |
| GET    | /workouts/<name>             | Get workout history           |
| POST   | /metrics                     | Log body metrics              |
| GET    | /metrics/<name>              | Get body metrics history      |
| GET    | /bmi/<name>                  | Calculate BMI                 |
| POST   | /login                       | Authenticate user             |
| GET    | /users                       | List all users                |
| GET    | /generate_program/<name>     | AI-style program generator    |
| GET    | /generate_pdf/<name>         | Generate PDF client report    |
| GET    | /membership/<name>           | Check membership expiry       |

## Running Tests Manually
```bash
# Run all tests with verbose output
pytest test_app.py -v
# OR
python3 -m pytest test_app.py -v

# Run with coverage report (shows % per function)
pytest test_app.py -v --cov=app --cov-report=term-missing

# Run with quality gate — fails if coverage drops below 80%
pytest test_app.py -v --cov=app --cov-report=term-missing --cov-fail-under=80

# Run tests inside Docker (mirrors CI environment exactly)
docker run aceest-fitness:latest pytest test_app.py -v --cov=app --cov-fail-under=80
```

## Docker
```bash
# Build the image
docker build -t aceest-fitness:latest .

# Run the container
docker run -p 8080:8080 aceest-fitness:latest

# API is now live at http://localhost:8080
```

## CI/CD Integration Logic

This project uses **two complementary pipelines** that serve different purposes
and together enforce full build confidence before any code reaches production.

**GitHub Actions** (`.github/workflows/main.yml`) is the *gatekeeper* — introduced
at v1.0 with a single lint job and expanded at v2.0.1 to three sequential jobs once
Dockerfile and tests both existed. It runs automatically on every push and pull request
to both `develop` and `main`. It enforces three sequential quality checks: lint
(flake8 must pass), Docker image assembly (image must build cleanly), and automated
tests with a coverage quality gate (pytest must pass with ≥80% coverage inside the
container). A PR cannot be merged if any of these three jobs fail — this applies to
both feature → develop PRs and the final develop → main release PR.

**Jenkins** (`Jenkinsfile`) is the *build server* — it runs the same five stages
(Checkout → Install → Lint → Test with quality gate → Docker Build) but executes
on a dedicated Jenkins server rather than GitHub's cloud runners. This demonstrates
an on-premise CI setup, mirrors how enterprise teams run pipelines on internal
infrastructure, and provides a full audit log of every build in the Jenkins UI at
`http://localhost:8080`.

The two pipelines are intentionally redundant: GitHub Actions catches issues
immediately at the PR stage, while Jenkins provides an independent verification
on a separate runtime. Together they demonstrate the DevOps principle of
*pipeline-as-code* — the entire build, test, and package process is version-
controlled in the repository alongside the application code.

## Branching Strategy
```
main        — production-only, receives ONE PR (develop → main at v3.2.4)
develop     — integration branch, receives all 10 feature PRs
feature/*   — one branch per version (e.g. feature/v2.0.1-sqlite-db-tests-docker)
```
Flow: feature/vX.X.X → develop (per version PR) → main (single final release PR)
Release tags (v1.0 → v3.2.4) are cut from develop after each feature merge.

## Commit Convention
| Prefix     | Used for                              |
|------------|---------------------------------------|
| feat:      | New endpoint or feature               |
| refactor:  | Code restructure, no feature change   |
| ci:        | Pipeline configuration                |
| docs:      | README or documentation update        |
# 🧠 AI Document Intelligence API

> **Extract structured data from any document using AI** — invoices, ID cards, resumes, medical forms, and more.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-https%3A%2F%2Fdoc--intelligence--api.cyrus--thindwa.me-2ea44f)](https://doc-intelligence-api.cyrus-thindwa.me)
[![Swagger Docs](https://img.shields.io/badge/Swagger%20Docs-/docs-85EA2D)](https://doc-intelligence-api.cyrus-thindwa.me/docs)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Live Demo](#-live-demo)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Quick Start (Local)](#-quick-start-local)
- [API Reference](#-api-reference)
- [Example Workflows](#-example-workflows)
- [Plans & Rate Limits](#-plans--rate-limits)
- [Environment Variables](#-environment-variables)
- [Deployment](#-deployment)
- [License](#-license)

---

## 📖 Overview

The **AI Document Intelligence API** lets you upload documents (PDFs, images, Word files, or plain text) and extract structured data using Claude AI. Instead of manually reading through documents, you define the fields you want — the API does the rest.

**Use cases:**
- 📄 **Invoice processing** — extract vendor, amounts, line items
- 🆔 **Identity verification** — extract names, ID numbers, expiry dates
- 📝 **Resume parsing** — extract skills, experience, education
- 🏥 **Medical form data entry** — extract patient info, diagnoses, medications

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        HTTPS (443)                                  │
│                          │                                          │
│                    ┌─────▼──────┐                                   │
│                    │   Traefik  │  (SSL termination / reverse proxy)│
│                    │ (Dokploy)  │                                   │
│                    └─────┬──────┘                                   │
│                          │                                          │
│              ┌───────────┴───────────┐                              │
│              │                       │                              │
│     ┌────────▼────────┐   ┌─────────▼────────┐                     │
│     │   Frontend      │   │    Backend       │                     │
│     │  (Nginx / React)│   │ (FastAPI / Uvicorn)                    │
│     │  :80            │   │  :8000            │                    │
│     └────────┬────────┘   └─────────┬────────┘                     │
│              │                      │                              │
│              │       ┌──────────────┼──────────────┐               │
│              │       │              │              │               │
│              │  ┌────▼────┐  ┌──────▼──────┐  ┌───▼────┐          │
│              │  │PostgreSQL│  │   Redis     │  │Claude  │          │
│              │  │  :5432   │  │   :6379     │  │   AI   │          │
│              │  └─────────┘  └─────────────┘  └────────┘          │
│              │                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Client                    Traefik              Frontend (Nginx)        Backend (FastAPI)      Claude AI
  │                         │                       │                      │                   │
  │── POST /v1/extract ────►│── HTTPS :443 ────────►│── proxy /v1/ ──────►│───► parse doc ────►│
  │   (multipart: file +    │                       │                     │                   │
  │    fields/schema)       │                       │                     │◄── structured ─────│
  │◄──── JSON response ─────│◄──────────────────────│◄──── JSON ──────────│◄──── data ─────────│
  │                         │                       │                     │
```

---

## 🎮 Live Demo

🌐 **Frontend UI:** [https://doc-intelligence-api.cyrus-thindwa.me](https://doc-intelligence-api.cyrus-thindwa.me)

📘 **Interactive Swagger Docs:** [https://doc-intelligence-api.cyrus-thindwa.me/docs](https://doc-intelligence-api.cyrus-thindwa.me/docs)

> **Note:** You'll need an API key to make requests. Create one at `POST /v1/keys` via the Swagger UI or curl.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **📄 Multi-format support** | PDF, PNG, JPEG, WEBP, TXT, DOCX |
| **🧩 Predefined schemas** | `invoice`, `identity`, `resume`, `medical` |
| **🎯 Custom fields** | Define any fields you want extracted |
| **⚡ Batch processing** | Process up to 10 documents in parallel |
| **📊 Confidence scores** | Optional per-field confidence metrics |
| **🔑 API key auth** | Per-key rate limits with 3 plan tiers |
| **🖥️ React frontend** | Drag-and-drop UI for quick testing |
| **📈 Usage tracking** | Full request logging and rate limiting |

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19 + Vite + Axios + Tailwind CSS |
| **Backend** | Python 3.11 + FastAPI + SQLAlchemy (async) |
| **Database** | PostgreSQL 16 |
| **Cache** | Redis 7 |
| **AI** | Claude API (Anthropic) |
| **Reverse Proxy** | Traefik (via Dokploy) |
| **Containerisation** | Docker Compose |
| **Deployment** | Dokploy on Ubuntu (DigitalOcean) |

---

## 🚀 Quick Start (Local)

### Prerequisites

- Docker & Docker Compose
- An [Anthropic API key](https://console.anthropic.com/)

### 1. Clone the repository

```bash
git clone https://github.com/cyrusthindwa/doc-intelligence-api.git
cd doc-intelligence-api
```

### 2. Set environment variables

```bash
# Root .env (shared with Docker Compose)
cp .env.example .env
```

Edit `.env` and add your **Anthropic API key**:

```env
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
```

### 3. Start all services

```bash
docker compose up -d --build
```

This starts:
- **PostgreSQL** on `:5432`
- **Redis** on `:6379`
- **Backend API** on `:8000`
- **Frontend** on `:80`

### 4. Run database migrations

```bash
docker exec docapi_backend alembic upgrade head
```

### 5. Create an API key

```bash
curl -X POST http://localhost:8000/v1/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "Dev Key", "plan": "demo"}'
```

Copy the returned `api_key` value — you'll use it in the `x-api-key` header.

### 6. Access the app

- **Frontend UI:** [http://localhost](http://localhost)
- **Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

---

## 📚 API Reference

All endpoints are prefixed with `/v1` and require an API key in the `x-api-key` header (except `POST /v1/keys` and `GET /health`).

### Authentication

```http
x-api-key: doc_demo_a1b2c3d4e5f6...
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/v1/extract` | Extract data from a single document |
| `POST` | `/v1/batch` | Extract data from up to 10 documents |
| `GET` | `/v1/schema` | List all predefined schemas |
| `GET` | `/v1/schema/{name}` | Get full schema definition |
| `POST` | `/v1/keys` | Create a new API key |
| `GET` | `/v1/keys/validate` | Validate the current API key |

### Full OpenAPI spec

Visit [https://doc-intelligence-api.cyrus-thindwa.me/docs](https://doc-intelligence-api.cyrus-thindwa.me/docs) (or `/docs` locally) for the complete interactive documentation.

---

## 💡 Example Workflows

### 1. Invoice extraction (predefined schema)

```bash
curl -X POST https://doc-intelligence-api.cyrus-thindwa.me/v1/extract \
  -H "x-api-key: doc_demo_xxxxxxxxxx" \
  -F "file=@invoice.pdf" \
  -F "schema_name=invoice"
```

### 2. Resume parsing (custom fields)

```bash
curl -X POST https://doc-intelligence-api.cyrus-thindwa.me/v1/extract \
  -H "x-api-key: doc_demo_xxxxxxxxxx" \
  -F "file=@resume.pdf" \
  -F 'fields=["name","email","skills","experience"]'
```

### 3. Identity document with confidence scores

```bash
curl -X POST https://doc-intelligence-api.cyrus-thindwa.me/v1/extract \
  -H "x-api-key: doc_demo_xxxxxxxxxx" \
  -F "file=@passport.png" \
  -F "schema_name=identity" \
  -F "confidence=true"
```

### 4. Batch processing (multiple invoices)

```bash
curl -X POST https://doc-intelligence-api.cyrus-thindwa.me/v1/batch \
  -H "x-api-key: doc_demo_xxxxxxxxxx" \
  -F "files=@invoice1.pdf" \
  -F "files=@invoice2.pdf" \
  -F "files=@invoice3.pdf" \
  -F "schema_name=invoice"
```

### 5. Create a new API key

```bash
curl -X POST https://doc-intelligence-api.cyrus-thindwa.me/v1/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "Production App", "plan": "starter"}'
```

### 6. Validate your API key

```bash
curl -X GET https://doc-intelligence-api.cyrus-thindwa.me/v1/keys/validate \
  -H "x-api-key: doc_demo_xxxxxxxxxx"
```

---

## 📊 Plans & Rate Limits

| Plan | Rate Limit | Best For |
|------|-----------|----------|
| **Demo** | 10 req/min | Testing & evaluation |
| **Starter** | 60 req/min | Small projects & personal use |
| **Pro** | 300 req/min | Production applications |

Rate limit headers are included in every response:

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 8
X-RateLimit-Reset: 1700000000
```

---

## 🔐 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API key | _(required)_ |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@postgres:5432/docapi` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `CORS_ORIGIN` | Allowed CORS origin | `http://localhost:3000` |
| `VITE_API_URL` | Frontend API URL (empty = relative) | _(empty for production)_ |
| `VITE_API_KEY` | Frontend default API key | _(optional)_ |

---

## 🚢 Deployment

This project is deployed using **Dokploy** on a DigitalOcean droplet with **Traefik** handling SSL termination and reverse proxy.

### Deploy via Dokploy

1. Push your code to GitHub
2. Create a new project in Dokploy
3. Point it to your GitHub repository
4. Set the environment variables in Dokploy's dashboard
5. Dokploy automatically builds and deploys using the `docker-compose.yml`

### Manual deployment

```bash
# On your server
git clone https://github.com/cyrusthindwa/doc-intelligence-api.git
cd doc-intelligence-api

# Set up env
cp .env.example .env
# Edit .env with your keys

# Start everything
docker compose up -d --build

# Run migrations
docker exec docapi_backend alembic upgrade head

# Create first API key
curl -X POST http://localhost:8000/v1/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "Admin Key", "plan": "pro"}'
```

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built with ❤️ using FastAPI, React, and Claude AI
  <br>
  <a href="https://doc-intelligence-api.cyrus-thindwa.me">Live Demo</a> ·
  <a href="https://doc-intelligence-api.cyrus-thindwa.me/docs">API Docs</a> ·
  <a href="https://github.com/cyrusthindwa/doc-intelligence-api">GitHub</a>
</p>

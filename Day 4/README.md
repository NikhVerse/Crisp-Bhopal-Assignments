# 🤖 AI Email Auto Responder

<div align="center">

![AI Email Auto Responder Banner](screenshots/banner.png)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](docker-compose.yml)
[![n8n](https://img.shields.io/badge/n8n-Workflow-EA4B71?logo=n8n)](workflows/email_responder.json)
[![Ollama](https://img.shields.io/badge/Ollama-llama3.1-000000)](https://ollama.com)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-DC244C)](https://qdrant.tech)
[![CRISP Day 4](https://img.shields.io/badge/CRISP-Day%204%20Assignment-blueviolet)]()

> **An autonomous, production-ready AI email assistant** that monitors your Gmail inbox, understands email intent, remembers past conversations, generates professional replies, and sends them — all with zero manual effort.

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Workflow Diagram](#-workflow-diagram)
- [Technology Stack](#-technology-stack)
- [Agentic AI Concepts](#-agentic-ai-concepts)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Docker Setup](#-docker-setup)
- [Gmail API Setup](#-gmail-api-setup)
- [Running the Project](#-running-the-project)
- [Importing the Workflow](#-importing-the-workflow)
- [Screenshots](#-screenshots)
- [Email Categories](#-email-categories)
- [Bonus Features](#-bonus-features)
- [Future Improvements](#-future-improvements)
- [Reflection](#-reflection)
- [License](#-license)

---

## 🌟 Overview

The **AI Email Auto Responder** is a fully autonomous Agentic AI system built on top of [n8n](https://n8n.io/), [Ollama](https://ollama.com), and [Qdrant](https://qdrant.tech). It acts as your personal executive email assistant — reading, understanding, classifying, and replying to emails with human-level intelligence.

This project was built as a **CRISP Day 4 Agentic AI Assignment** and demonstrates real-world AI agent design with:

- 🧠 **Planning** — Multi-step reasoning before acting  
- 💾 **Memory** — Persistent vector memory via Qdrant  
- 🔧 **Tool Usage** — Gmail, HTTP, File, Markdown nodes  
- 🤖 **Autonomy** — Self-directed email classification and reply generation  
- 🔄 **Multi-step Reasoning** — Planner → Classifier → Writer → Approval → Sender  

---

## ✨ Features

| Feature | Description |
|---|---|
| 📥 Gmail Monitoring | Automatically polls Gmail inbox every minute |
| 🧠 Intent Understanding | AI reads and comprehends email context |
| 🗂️ Email Classification | Classifies into 10 categories automatically |
| 🚨 Urgency Detection | Scores email urgency (1–10) |
| 💾 Memory | Remembers past conversations via Qdrant vector DB |
| ✍️ AI Reply Generation | Generates professional, context-aware replies |
| ✅ Approval Gate | Waits for human approval before sending |
| 📤 Auto Send | Sends approved replies via Gmail API |
| 📝 Markdown Logs | Generates detailed logs for every email processed |
| 📊 Analytics | Tracks category distributions, response times |
| 🌐 Translation | Detects non-English emails and translates |
| 📅 Meeting Summaries | Extracts action items from meeting emails |
| 🔖 Auto Labeling | Labels emails by category in Gmail |
| 🚫 Spam Detection | Identifies and skips spam/newsletter emails |
| 📋 Task Extraction | Extracts follow-up tasks from emails |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI Email Auto Responder                       │
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────────────┐  │
│  │  Gmail   │───▶│  n8n     │───▶│     Ollama (LLM)         │  │
│  │  Inbox   │    │  Engine  │    │     llama3.1 / qwen3      │  │
│  └──────────┘    └────┬─────┘    └──────────────────────────┘  │
│                       │                                          │
│              ┌────────┼────────┐                                 │
│              ▼        ▼        ▼                                 │
│         ┌────────┐ ┌──────┐ ┌──────────┐                       │
│         │Qdrant  │ │ Logs │ │ Approval │                       │
│         │Vector  │ │ (.md)│ │  Gate    │                       │
│         │Memory  │ │      │ │          │                       │
│         └────────┘ └──────┘ └──────────┘                       │
│                                                                  │
│  Docker Network: email_ai_net                                   │
│  Volumes: n8n_data · ollama_data · qdrant_data · logs_data     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Workflow Diagram

```
Gmail Trigger (Poll every 1 min)
         │
         ▼
  ┌─────────────┐
  │  Read Email  │  ← Fetch full email body, sender, subject
  └──────┬──────┘
         │
         ▼
  ┌─────────────────┐
  │ Retrieve Memory  │  ← Search Qdrant for past conversations
  └──────┬──────────┘
         │
         ▼
  ┌─────────────────────────────────────────────────────┐
  │                 AI PLANNER NODE                       │
  │  • Understand Intent                                  │
  │  • Classify Email Category                           │
  │  • Score Urgency (1–10)                              │
  │  • Determine Reply Style                             │
  │  • Generate Draft Reply                              │
  │  • Extract Tasks / Meeting Info                      │
  │  • Detect Language / Translate                       │
  │  • Check for Spam                                    │
  └──────┬──────────────────────────────────────────────┘
         │
         ▼
  ┌─────────────┐
  │   Switch    │  ← Route by category
  │   Node      │
  └──────┬──────┘
         │
   ┌─────┴──────┐
   ▼            ▼
[Spam]    [Non-Spam]
Skip        │
            ▼
     ┌─────────────┐
     │  Approval   │  ← Wait for human approval webhook
     │    Gate     │
     └──────┬──────┘
            │
     ┌──────┴──────┐
     ▼             ▼
[Approved]    [Rejected]
    │              │
    ▼              ▼
Send Email    Discard &
    │          Log Reason
    ▼
Save to Qdrant Memory
    │
    ▼
Generate Markdown Log
    │
    ▼
 ✅ Done
```

---

## 🛠 Technology Stack

| Technology | Version | Role |
|---|---|---|
| **n8n** | Latest | Workflow automation engine |
| **Docker** | 24+ | Container orchestration |
| **Docker Compose** | v3.8 | Service configuration |
| **Ollama** | Latest | Local LLM server |
| **llama3.1 / qwen3** | Latest | AI language model |
| **Qdrant** | Latest | Vector database for memory |
| **Gmail API** | v1 | Email read/send |
| **HTTP Node** | — | Qdrant REST API calls |
| **Markdown Node** | — | Log generation |
| **File Node** | — | Persistent log storage |

---

## 🤖 Agentic AI Concepts

This project demonstrates all 5 core Agentic AI principles:

### 1. 🗺️ Planning
The AI Planner node thinks before acting. It:
- Reads the email completely
- Understands the intent
- Retrieves memory context
- Plans the reply approach
- Chooses tone and format

### 2. 💾 Memory
Using Qdrant vector database:
- Stores embeddings of every processed email
- Retrieves semantically similar past conversations
- Remembers writing style for each contact
- Tracks frequency of contacts
- Provides context for follow-up replies

### 3. 🔧 Tool Usage
The agent uses 7 tools:
- **Gmail Trigger** — watches inbox
- **Gmail Read** — fetches details
- **Ollama AI** — generates replies
- **HTTP (Qdrant)** — memory store/retrieve
- **Markdown** — generates logs
- **Gmail Send** — sends replies
- **Write File** — stores logs

### 4. 🤖 Autonomous Decision Making
The AI independently:
- Classifies emails without human input
- Detects spam and skips it
- Scores urgency automatically
- Chooses reply style (formal/casual)
- Decides when to ask for clarification

### 5. 🔄 Multi-step Reasoning
The agent follows a structured pipeline:
Read → Understand → Retrieve → Classify → Plan → Draft → Approve → Send → Store → Log

---

## 📁 Project Structure

```
email-auto-responder/
│
├── 🐳 docker-compose.yml       ← All services in one file
├── 🔒 .env.example             ← Environment variables template
├── 📖 README.md                ← This file
├── ⚖️  LICENSE                  ← MIT License
├── 🚫 .gitignore               ← Git ignore rules
├── 📦 requirements.txt         ← Python helper dependencies
│
├── workflows/
│   └── 📋 email_responder.json ← Complete importable n8n workflow
│
├── logs/                       ← Auto-generated email logs
│   └── .gitkeep
│
├── screenshots/                ← Project screenshots
│   └── .gitkeep
│
├── docs/
│   └── 📐 architecture.md     ← Detailed architecture docs
│
└── 📝 reflection.md            ← Agentic AI reflection report
```

---

## 📋 Prerequisites

Before you begin, ensure you have:

- ✅ [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- ✅ [Docker Compose](https://docs.docker.com/compose/) (included with Docker Desktop)
- ✅ A **Gmail account** with 2FA enabled
- ✅ A **Google Cloud Console** account
- ✅ At least **8GB RAM** (16GB recommended for LLM)
- ✅ At least **20GB free disk space** (for Ollama models)
- ✅ Internet connection (for initial setup)

---

## 🚀 Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/ai-email-auto-responder.git
cd ai-email-auto-responder
```

### Step 2: Copy Environment File

```bash
cp .env.example .env
```

### Step 3: Edit `.env` with your credentials

```bash
notepad .env   # Windows
# or
nano .env      # Linux/Mac
```

Fill in:
- `GMAIL_CLIENT_ID`
- `GMAIL_CLIENT_SECRET`
- `GMAIL_REFRESH_TOKEN`
- `GMAIL_USER_EMAIL`

---

## 🐳 Docker Setup

### Start All Services

```bash
docker compose up -d
```

This starts:
- **n8n** at `http://localhost:5678`
- **Ollama** at `http://localhost:11434`
- **Qdrant** at `http://localhost:6333`
- **ollama-init** pulls `llama3.1` model automatically

### Check Status

```bash
docker compose ps
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f n8n
docker compose logs -f ollama
docker compose logs -f qdrant
```

### Pull a Different Model

```bash
docker exec -it ollama_email_responder ollama pull qwen3
```

### Stop All Services

```bash
docker compose down
```

### Stop and Remove Data (Full Reset)

```bash
docker compose down -v
```

---

## 📧 Gmail API Setup

### Step 1: Enable Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project: `AI Email Responder`
3. Navigate to **APIs & Services → Library**
4. Search for **Gmail API** and click **Enable**

### Step 2: Create OAuth Credentials

1. Go to **APIs & Services → Credentials**
2. Click **Create Credentials → OAuth 2.0 Client ID**
3. Choose **Web Application** or **Desktop App**
4. Add Authorized redirect URI: `http://localhost:5678/oauth2/callback`
5. Download the credentials JSON
6. Copy `client_id` and `client_secret` to your `.env`

### Step 3: Get Refresh Token

1. In n8n, go to **Settings → Credentials**
2. Create a new **Gmail OAuth2 API** credential
3. Enter your Client ID and Secret
4. Click **Connect my account** and authorize Gmail
5. n8n will store the refresh token automatically

---

## ▶️ Running the Project

### 1. Start Docker

```bash
docker compose up -d
```

### 2. Access n8n

Open [http://localhost:5678](http://localhost:5678)

Login with:
- Username: `admin`
- Password: `admin123`

### 3. Import Workflow

1. Click **Workflows** in the left sidebar
2. Click **Import from file**
3. Select `workflows/email_responder.json`
4. Click **Import**

### 4. Configure Credentials

1. Open the imported workflow
2. Click on the **Gmail Trigger** node
3. Connect your Gmail credential
4. Repeat for **Gmail Read** and **Gmail Send** nodes

### 5. Activate Workflow

Toggle the **Active** switch at the top right of the workflow canvas.

### 6. Test

Send a test email to your Gmail inbox and watch the workflow execute!

---

## 📥 Importing the Workflow

The workflow is located at `workflows/email_responder.json`.

**Method 1 — UI Import:**
1. Open n8n → Workflows → Import from file
2. Select the JSON file

**Method 2 — API Import:**
```bash
curl -X POST http://localhost:5678/api/v1/workflows \
  -H "Content-Type: application/json" \
  -u admin:admin123 \
  -d @workflows/email_responder.json
```

---

## 📸 Screenshots

> Add your screenshots to the `screenshots/` folder after running the project.

| Screenshot | Description |
|---|---|
| `docker_desktop.png` | Docker Desktop showing all 4 containers running |
| `containers_running.png` | `docker compose ps` output |
| `n8n_dashboard.png` | n8n workflow dashboard |
| `workflow_canvas.png` | Full workflow canvas view |
| `planner_node.png` | AI Planner node configuration |
| `memory_node.png` | Qdrant memory node |
| `gmail_trigger.png` | Gmail Trigger node settings |
| `ai_reply.png` | Generated AI reply in n8n |
| `approval_node.png` | Approval webhook node |
| `email_sent.png` | Successful email sent confirmation |
| `logs_folder.png` | Generated markdown logs |

---

## 🗂️ Email Categories

The AI automatically classifies emails into:

| Category | Description |
|---|---|
| 📄 Job Application | Job applications, resumes, career inquiries |
| 👥 HR | Human resources, payroll, company policies |
| 🛠️ Support | Technical support, bug reports, help requests |
| 💼 Customer Inquiry | Sales inquiries, product questions |
| 👤 Personal | Friends, family, personal matters |
| 🏢 Business | Business proposals, partnerships, B2B |
| 📅 Meeting Request | Meeting invites, scheduling, calendars |
| 📰 Newsletter | Marketing, subscriptions, announcements |
| 🚫 Spam | Phishing, irrelevant bulk email |
| 🔖 Other | Everything else |

---

## 🎁 Bonus Features

- 🏷️ **Auto-label** emails in Gmail by category
- 🔍 **Spam detection** with auto-skip
- 📅 **Meeting summary extraction**
- 🌐 **Email translation** (detect language, reply in English)
- 💡 **Follow-up suggestions**
- ✅ **Task extraction** from email body
- 🚨 **Urgency scoring** (1–10 numeric scale)
- 📊 **Daily email summary** generation
- 📈 **Analytics data** for dashboard integration
- 🔔 **Follow-up reminders** stored to file

---

## 🔮 Future Improvements

- [ ] Add Slack/Telegram notification for approval requests
- [ ] Implement a web-based approval dashboard
- [ ] Add calendar integration for meeting scheduling
- [ ] Support multiple email accounts
- [ ] Add email thread summarization
- [ ] Implement RAG with company knowledge base
- [ ] Fine-tune a custom Ollama model on writing style
- [ ] Add voice-to-email via Whisper integration
- [ ] Build analytics dashboard with Grafana
- [ ] Add SMS fallback via Twilio
- [ ] Implement A/B testing for reply styles
- [ ] Add multi-language reply support

---

## 📝 Reflection

See [reflection.md](reflection.md) for a detailed Agentic AI reflection report covering:
- What is Agentic AI
- Why planning matters
- How memory improves responses
- Lessons learned
- Challenges faced

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with ❤️ for CRISP Day 4 Agentic AI Assignment**

[⭐ Star this repo](https://github.com/yourusername/ai-email-auto-responder) · [🐛 Report Bug](https://github.com/yourusername/ai-email-auto-responder/issues) · [💡 Request Feature](https://github.com/yourusername/ai-email-auto-responder/issues)

</div>

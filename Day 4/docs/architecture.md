# AI Email Auto Responder — Architecture Documentation

## System Overview

The AI Email Auto Responder is a multi-container system orchestrated by Docker Compose.
Each service has a distinct responsibility and communicates over an isolated Docker network.

---

## Container Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Docker Host Machine                              │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                   email_ai_net (bridge)                       │   │
│  │                                                               │   │
│  │  ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐  │   │
│  │  │     n8n      │   │   Ollama     │   │    Qdrant        │  │   │
│  │  │  :5678       │──▶│  :11434      │   │  :6333 :6334     │  │   │
│  │  │              │   │              │   │                  │  │   │
│  │  │ Workflow     │◀──│ llama3.1     │   │ Vector Memory    │  │   │
│  │  │ Engine       │   │ LLM Server   │   │ Store            │  │   │
│  │  └──────┬───────┘   └──────────────┘   └────────┬─────────┘  │   │
│  │         │                                        │             │   │
│  │         └────────────────────────────────────────┘             │   │
│  │                     HTTP REST API calls                         │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  Volumes:                                                            │
│  ├── n8n_data      → /home/node/.n8n                                │
│  ├── ollama_data   → /root/.ollama                                   │
│  ├── qdrant_data   → /qdrant/storage                                 │
│  └── logs_data     → /data/logs                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

```
Gmail Inbox
    │
    │ (OAuth 2.0 polling every 60s)
    ▼
n8n Gmail Trigger
    │
    │ (Raw email data)
    ▼
n8n Set Node (Extract: from, to, subject, body, messageId, threadId)
    │
    ▼
n8n HTTP Request → Qdrant REST API
    │ POST /collections/email_memory/points/search
    │ Body: {vector: [embedding], filter: {sender_email}}
    │
    │ Returns: past conversations (top 5)
    ▼
n8n AI Agent (Ollama: llama3.1)
    │ Input: email + memory context
    │ Output: structured JSON
    │ {intent, category, urgency, reply, tasks, spam_score}
    ▼
n8n Switch (category routing)
    │
    ├── [SPAM] → Write Log → Stop
    │
    └── [Non-Spam]
            │
            ▼
        n8n Wait/Webhook (approval gate)
            │
            ├── [REJECTED] → Log → Stop
            │
            └── [APPROVED]
                    │
                    ▼
                Gmail Send API
                    │
                    ▼
                Qdrant Upsert (store new memory)
                    │
                    ▼
                Markdown Node (generate log)
                    │
                    ▼
                Write File (save to /data/logs)
                    │
                    ▼
                ✅ Workflow Complete
```

---

## Qdrant Memory Schema

### Collection: `email_memory`

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Unique point ID |
| `vector` | float[384] | Semantic embedding of email content |
| `sender_email` | string | Sender's email address |
| `sender_name` | string | Sender's display name |
| `subject` | string | Email subject |
| `body_summary` | string | Summarized email body |
| `category` | string | AI-classified category |
| `urgency_score` | integer | 1–10 urgency scale |
| `reply_sent` | string | The reply we sent |
| `timestamp` | ISO datetime | When the email was processed |
| `thread_id` | string | Gmail thread ID for grouping |
| `message_id` | string | Gmail message ID |
| `tasks` | string[] | Extracted action items |
| `follow_up_needed` | boolean | Whether follow-up is required |

---

## AI Prompt Architecture

### System Prompt (Planner Node)

```
You are a professional executive email assistant with perfect memory and judgment.

Your task is to analyze incoming emails and produce a structured response plan.

Given:
- The email sender, subject, and body
- Previous conversation history with this sender (if any)

You must output ONLY valid JSON with these exact fields:
{
  "intent": "string — what the sender wants",
  "category": "one of: Job Application, HR, Support, Customer Inquiry, Personal, Business, Meeting Request, Newsletter, Spam, Other",
  "urgency_score": "integer 1-10",
  "urgency_reason": "string — why this urgency score",
  "reply_style": "one of: formal, casual, technical, empathetic",
  "draft_reply": "string — the complete professional reply to send",
  "reply_subject": "string — email subject line",
  "tasks": ["array of action items extracted from email"],
  "spam_score": "float 0.0-1.0",
  "spam_reason": "string — why this spam score",
  "follow_up_needed": "boolean",
  "follow_up_date": "ISO date string or null",
  "language_detected": "string — ISO 639-1 language code",
  "summary": "string — 1 sentence summary of the email",
  "meeting_info": {
    "is_meeting_request": "boolean",
    "proposed_time": "string or null",
    "location": "string or null",
    "attendees": ["array of emails or null"]
  }
}

Rules:
1. Never invent information. If unsure, ask for clarification.
2. If this is a follow-up, reference the previous conversation.
3. Keep replies concise and professional.
4. Never use filler phrases like "Hope this email finds you well."
5. Match the reply language to the sender's language unless they write in a non-English language — then reply in English.
6. Spam threshold: spam_score > 0.7 means do not reply.
```

---

## Approval Webhook Flow

```
Workflow reaches Approval Node
        │
        ▼
Webhook listener activated
(URL: http://localhost:5678/webhook/email-approval/{executionId})
        │
        │ User receives notification with:
        │  - Email summary
        │  - AI draft reply
        │  - Approve link
        │  - Reject link
        │
        ▼
User clicks Approve or Reject
        │
        ├── GET /webhook/email-approval/{id}?action=approve
        │       → Resume workflow → Send email
        │
        └── GET /webhook/email-approval/{id}?action=reject
                → Resume workflow → Log rejection → Stop
```

---

## Log Format

Each processed email generates a Markdown log file at:
`/data/logs/YYYY-MM-DD_HH-MM-SS_{sender_email}.md`

### Log Structure

```markdown
# Email Processing Log

**Date:** 2025-07-25 14:30:00
**Sender:** john.doe@company.com
**Subject:** Re: Project Proposal
**Category:** Business
**Urgency:** 7/10
**Spam Score:** 0.02

## Email Summary
[1-sentence summary]

## Intent
[What the sender wanted]

## AI Draft Reply
[The reply text]

## Action Taken
✅ SENT / ❌ REJECTED

## Tasks Extracted
- [ ] Send contract by Friday
- [ ] Schedule follow-up call

## Memory Stored
✅ Conversation stored in Qdrant

---
*Generated by AI Email Auto Responder*
```

---

## Security Considerations

1. **OAuth tokens** are stored in n8n's encrypted credential store, never in plain text
2. **`.env` file** is in `.gitignore` — never committed to Git
3. **Qdrant** runs on the internal Docker network, not exposed to the internet
4. **Approval gate** prevents unauthorized email sending
5. **Spam filtering** prevents the AI from replying to phishing attempts
6. **Local LLM** — all email data processed locally, never sent to external AI APIs

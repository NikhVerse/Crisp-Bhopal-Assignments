# Setup & Troubleshooting Guide: AI Email Approval Agent

This guide walks you through setting up, configuring, running, and troubleshooting the AI Email Approval Agent.

---

## 🛠️ Step-by-Step Installation

### 1. Prerequisites
Ensure you have the following installed on your machine:
* [Docker Desktop](https://www.docker.com/products/docker-desktop/)
* A Gmail/Google Workspace Account with access to [Google Cloud Console](https://console.cloud.google.com/)

---

### 2. Configure Environment Variables
1. Navigate to the `email-agent/` directory:
   ```bash
   cd email-agent
   ```
2. Copy the example configuration to create your local `.env`:
   ```bash
   cp .env.example .env
   ```
3. Open `.env` and fill in your details:
   * **N8N_PORT**: `5679` (defaults to avoid port conflicts with other running instances)
   * **GMAIL_CLIENT_ID** & **GMAIL_CLIENT_SECRET**: From your Google Cloud credentials page.
   * **GMAIL_REFRESH_TOKEN**: Generated via OAuth 2.0 Playground or manual consent flow.
   * **ADMIN_EMAIL**: The email where approval notifications will be sent.
   * **OLLAMA_PORT**: `11435`

---

### 3. Launch Services
Start the docker containers in detached mode:
```bash
docker compose up -d
```

This will spin up:
1. **n8n** (Port `5679`): Workflow Automation Engine
2. **Ollama** (Port `11435`): Local LLM Server
3. **Ollama Model Puller**: A temporary container that checks for and pulls the `llama3.2` model (~2.0 GB).

To monitor the download progress of the model, run:
```bash
docker logs -f ollama_agent_init
```

Once the model is fully loaded, this initialization container will terminate automatically.

---

## 📋 n8n Workflow Configuration

### 1. Access the Dashboard
Open your browser and navigate to:
```
http://localhost:5679
```
Login credentials (configured in `.env`):
* **User**: `admin`
* **Password**: `admin123`

---

### 2. Add Gmail Credentials
To securely interact with the Gmail API, create your Gmail credential within n8n:
1. Click **Settings** (⚙️ bottom-left) → **Credentials**.
2. Click **Add Credential** and search for **"Gmail OAuth2 API"**.
3. Fill in the credentials exactly from your `.env`:
   * **Client ID**
   * **Client Secret**
   * **Refresh Token**
4. Click **Save** and verify that n8n shows "Connection successful".

---

### 3. Import the Workflow
1. Go to **Workflows** → **⊕ New workflow** (or click the dropdown and choose **Import from File**).
2. Select the `workflows/email_agent.json` file inside your project directory.
3. Once loaded, click into the following Gmail nodes and select your newly saved Gmail credential:
   * `Gmail Trigger`
   * `Read Full Email`
   * `Send Gmail Reply (Auto)`
   * `Send Approval Notification`
   * `Send Gmail Reply (Approved)`
4. Click **Save** (top-right).
5. Toggle the **Active** switch to **Active** (turns green).

---

## 🔍 Verification & Testing

### 1. Test Spam Detection
Send an email to your registered inbox containing keywords like:
> "Buy cheap Rolex watches! Free shipping! Click link below now!"

* **Result**: The workflow triggers, classifies it as spam with high confidence, writes a markdown log to `logs/spam/spam-YYYY-MM-DD-HH-MM.md`, and terminates without sending a reply.

### 2. Test Auto-Reply
Send a simple greeting or simple query:
> "Hi, I just wanted to ask if you received the files I sent yesterday. Thanks."

* **Result**: The workflow triggers, classifies it as `auto_reply`, automatically sends a professional reply to the sender, saves the interaction to `data/memory/sender@email.com.json`, and writes a processing log to `logs/YYYY-MM-DD-HH-MM-SS.md`.

### 3. Test Human-in-the-Loop Approval
Send a complex request:
> "Hello Nikhil, I would like to schedule a 30-minute demo of your enterprise automation product next Tuesday at 3:00 PM IST. Please let me know if this works."

* **Result**:
  1. The workflow triggers, classifies it as `approval`.
  2. Sends an email to the `ADMIN_EMAIL` with the draft reply and two clickable links (Approve/Reject).
  3. The workflow execution enters a **Waiting** status.
  4. Once you click the **Approve** link:
     * n8n resumes execution.
     * The draft response is emailed.
     * Memory and logs are saved.

---

## 🛠️ Troubleshooting

### Issue 1: Ollama endpoint returns 404
* **Explanation**: The requested model `llama3.2` is not loaded in Ollama.
* **Fix**: Run `docker exec -it ollama_email_agent ollama pull llama3.2` to download the model manually.

### Issue 2: Permission denied inside n8n Code Nodes
* **Explanation**: The Code nodes require access to the Node.js `fs` module to save logs and memories.
* **Fix**: Ensure `NODE_FUNCTION_ALLOW_BUILTIN=*` is set in the `docker-compose.yml` file under the n8n environment section (this is enabled by default in our provided compose configuration).

### Issue 3: Gmail Webhook or Trigger not firing
* **Explanation**: Gmail API requires correct OAuth consent, credentials, and refresh token.
* **Fix**: Regenerate your refresh token using [Google OAuth Playground](https://developers.google.com/oauthplayground) with the scope `https://mail.google.com/`. Ensure the scope matches the n8n Gmail node requirements.

# CVGrok: AI Resume Analyzer & ATS Audit Dashboard

CVGrok is a professional-grade, production-ready AI Resume Analyzer designed to parse resume PDF documents, extract metadata structures, and execute a comprehensive semantic Applicant Tracking System (ATS) optimization audit. Powered by the **xAI Grok API**, the system performs lexical and syntactic analyses, suggests formatting changes, flags grammatical bugs, details keyword deficiencies, and generates an executive PDF report.

---

## Features

- **Heuristic & AI Multi-Pass Parsing:** Sequential text extraction via `PyMuPDF` and `pdfplumber` for maximum reliability, combined with regular expression metadata extractors for phone, email, and social handles (LinkedIn/GitHub).
- **Executive ATS Optimization:** Audit reports targeting resume layout compatibility, active verbs, readability thresholds, missing keywords, and job readiness.
- **Modern Glassmorphic Dark UI:** Responsive single-page dashboard featuring glowing micro-animations, animated score gauges, and light/dark toggling.
- **Interactive Checklist:** Live, interactive checklists that let candidates check off recommendations as they make edits.
- **Skill Insight Visualizations:** Radial, bar, and doughnut charts tracking candidate competencies and keyword weights using Chart.js.
- **Stateless PDF Audits:** Instant generation of print-ready, visual PDF reports using `reportlab`.
- **Local History Persistence:** Historical analysis reports saved securely to the browser's `LocalStorage` for easy reopening.
- **Graceful Fallback Mode:** Operates locally with heuristics and mock scores if the Grok API is not configured, facilitating instant interface validation.

---

## Tech Stack

### Frontend
- **HTML5:** Semantic architecture.
- **CSS3:** Flexbox/Grid systems, glassmorphism design variables, responsive layouts, animated transitions.
- **JavaScript (ES6+):** Async/Await API pipelines, LocalStorage state integration, Chart.js visualizations.

### Backend
- **Python (3.9+):** Backend runtime.
- **FastAPI:** High-performance web framework.
- **Uvicorn:** ASGI web server.
- **PyMuPDF & pdfplumber:** PDF extraction wrappers.
- **ReportLab:** Visual PDF report compiler.
- **HTTPX:** Async HTTP client interfacing with xAI API.

---

## Folder Structure

```
resume-analyzer/
│
├── backend/
│   ├── main.py              # Application setup, CORS, static file serving
│   ├── routes.py            # API endpoints (/upload, /analyze, /report, /cleanup)
│   ├── analyzer.py          # Coordinating parser output & Grok feedback
│   ├── parser.py            # Local text extractor & contact heuristic parser
│   ├── grok.py              # Grok API client logic using HTTPX
│   ├── reporter.py          # ReportLab PDF report template compiler
│   ├── requirements.txt     # Python system dependencies
│   └── uploads/             # Temporary folder for PDF processing
│
├── frontend/
│   ├── index.html           # Main Single-Page Application (SPA) dashboard
│   ├── style.css            # Cyberpunk-glassmorphism stylesheet
│   └── script.js            # Frontend router, charts, history & api handlers
│
├── .gitignore               # Ignored local envs and temporary PDFs
├── README.md                # System documentation
└── screenshots/             # Mock screenshots or assets
```

---

## Installation & Setup

### 1. Clone the Project & Enter Workspace
```bash
cd resume-analyzer
```

### 2. Configure Environment Variables
Create a `.env` file in the `backend/` directory:
```env
# xAI Grok Configuration
GROK_API_KEY=your_xai_grok_api_key_here
GROK_MODEL=grok-2-1212

# Optional Server Settings
PORT=8000
```
*Note: If no API key is specified, the application launches in a fallback demonstration mode, populating structural text fields locally.*

---

## Running the Application

### Option A: Unified Server (Serves Frontend & Backend together)

1. Create and activate a Python virtual environment:
   ```bash
   cd backend
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Launch the Uvicorn server:
   ```bash
   python main.py
   ```
   *The unified server runs at **`http://localhost:8000`** and serves both the API endpoints and the frontend user interface automatically!*

### Option B: Decoupled Development (Independent Frontend & Backend)

1. Run the backend API using Uvicorn as shown above.
2. Serve the `frontend/` directory using any local development static server. For example:
   ```bash
   cd ../frontend
   # Using Python:
   python -m http.server 3000
   # Using Node.js:
   npx serve -p 3000
   ```
3. Open **`http://localhost:3000`** in your browser. CORS is fully configured on the backend to allow cross-origin requests from any port during development.

---

## API Endpoints

All backend endpoints are prefixed with `/api`.

| Method | Endpoint | Description | Payload Schema | Response Schema |
| :--- | :--- | :--- | :--- | :--- |
| **POST** | `/api/upload` | Validates and extracts text from uploaded PDF. | Multipart Form (`file: UploadFile`) | `{ text: str, contact_info: {...}, sections: {...} }` |
| **POST** | `/api/analyze` | Queries Grok for complete ATS audit report. | `{ text: str, contact_info: {...} }` | Fully structured ATS JSON object |
| **POST** | `/api/report` | Complies and streams downloadable visual PDF. | Full ATS JSON object | Streams Binary `application/pdf` |
| **DELETE**| `/api/cleanup` | Wipes out processed PDFs from the upload cache. | None | `{ status: "success", cleaned_count: int }` |
| **GET** | `/health` | Retrieves health status and API configuration. | None | `{ status: "healthy", grok_api_configured: bool }` |

---

## Deployment Guides

### Backend Deployment (Render or Railway)

1. **Docker / Custom Build Command:**
   Make sure the project root points to `backend/requirements.txt` or execute:
   ```bash
   pip install -r backend/requirements.txt
   ```
2. **Start Command:**
   Point Uvicorn to run `main.py`:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```
3. **Environment Variable:**
   Configure `GROK_API_KEY` on your provider's settings dashboard.

### Frontend Deployment (Vercel or Netlify)

1. Set the **Build Command** to: `none` (Static Site).
2. Set the **Publish Directory** to: `frontend`.
3. If deploying decoupled, update the backend endpoint URL base in `frontend/script.js` (e.g. replacing relative paths `/api/...` with your hosted backend URL `https://your-backend.railway.app/api/...`).

---

## Future Improvements

1. **Job Description Matching:** Implement a text area in the upload view where users can paste target job requirements to generate tailored overlap scores.
2. **AI Skill Recommendation Engine:** Integrating course suggestions (e.g. from Coursera/EdX) matched directly to the identified skill gaps.
3. **Multi-Format Processing:** Support parsing `.docx` and `.txt` extensions alongside `.pdf`.

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

/**
 * app.js — Healthcare AI Clinical Assistant
 * ==========================================
 * Complete SPA logic: routing, API calls, UI interactions,
 * voice input, TTS, PDF download, theme, shortcuts, toast, history.
 */

"use strict";

/* =========================================================
   Constants
   ========================================================= */
const API_BASE = window.location.protocol === "file:" || window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost"
  ? "http://127.0.0.1:8080/api"
  : "/api";
const HISTORY_KEY = "hca_history";
const THEME_KEY   = "hca_theme";
const MAX_HISTORY = 50;

/* =========================================================
   State
   ========================================================= */
const state = {
  currentPage:      "dashboard",
  selectedCategory: "",
  isLoading:        false,
  apiOnline:        false,
  voiceRecognition: null,
  isRecording:      false,
  conversationHistory: JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]"),
  lastResult:       null,
  lastResultTitle:  "",
};

/* =========================================================
   DOM Helpers
   ========================================================= */
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

/* =========================================================
   Theme
   ========================================================= */
function initTheme() {
  const saved = localStorage.getItem(THEME_KEY) || "light";
  applyTheme(saved);
}

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  const btn = $("#themeToggle");
  if (btn) btn.textContent = theme === "dark" ? "☀️" : "🌙";
  localStorage.setItem(THEME_KEY, theme);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "light";
  applyTheme(current === "dark" ? "light" : "dark");
}

/* ==========================================================================
   Healthcare AI Clinical Assistant — Frontend SPA
   Professional Edition v2.0 | Vanilla JS | No framework
   ========================================================================== */
function navigate(pageId) {
  // Hide all pages
  $$(".page").forEach(p => p.classList.remove("active"));

  // Show target page
  const target = $(`#page-${pageId}`);
  if (target) target.classList.add("active");

  // Update nav items
  $$(".nav-item").forEach(item => {
    item.classList.toggle("active", item.dataset.page === pageId);
  });

  // Update navbar title
  const titles = {
    dashboard:    "Dashboard",
    symptom:      "Symptom Analyzer",
    medterm:      "Medical Term Explainer",
    prescription: "Prescription Explainer",
    healthtips:   "Health Tips",
    report:       "Medical Report Summary",
    emergency:    "Emergency Checker",
    about:        "About",
  };
  const titleEl = $("#navbarPageTitle");
  if (titleEl) titleEl.textContent = titles[pageId] || "Healthcare AI";

  state.currentPage = pageId;

  // Close mobile sidebar
  closeMobileSidebar();

  // Scroll to top
  window.scrollTo({ top: 0, behavior: "smooth" });
}

/* =========================================================
   Mobile Sidebar
   ========================================================= */
function openMobileSidebar() {
  $("#sidebar").classList.add("open");
  $("#sidebarOverlay").classList.add("visible");
  document.body.style.overflow = "hidden";
}

function closeMobileSidebar() {
  $("#sidebar").classList.remove("open");
  $("#sidebarOverlay").classList.remove("visible");
  document.body.style.overflow = "";
}

/* =========================================================
   API Health Check
   ========================================================= */
async function checkAPIStatus() {
  const dot  = $("#apiDot");
  const text = $("#apiStatusText");
  try {
    const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(5000) });
    if (res.ok) {
      state.apiOnline = true;
      if (dot)  { dot.className = "api-dot online"; }
      if (text) text.textContent = "API Online";
    } else {
      throw new Error("non-200");
    }
  } catch {
    state.apiOnline = false;
    if (dot)  { dot.className = "api-dot offline"; }
    if (text) text.textContent = "API Offline";
  }
}

/* =========================================================
   Toast Notifications
   ========================================================= */
function showToast(title, msg, type = "info", duration = 4000) {
  const message = msg;
  const container = $("#toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <div class="toast-stripe"></div>
    <div class="toast-body">
      <div class="toast-title">${title}</div>
      ${message ? `<div class="toast-msg">${message}</div>` : ""}
    </div>
    <button class="toast-close" onclick="this.closest('.toast').remove()" aria-label="Close notification">&times;</button>
  `;

  container.appendChild(toast);
  toast.querySelector(".toast-close").addEventListener("click", () => removeToast(toast));

  if (duration > 0) {
    setTimeout(() => removeToast(toast), duration);
  }
}

function removeToast(toast) {
  if (!toast.parentElement) return;
  toast.classList.add("removing");
  setTimeout(() => toast.remove(), 300);
}

/* =========================================================
   Markdown Renderer (lightweight)
   ========================================================= */
function renderMarkdown(text) {
  if (!text) return "";
  let html = escapeHtml(text);

  // Headers
  html = html.replace(/^######\s(.+)$/gm, "<h6>$1</h6>");
  html = html.replace(/^#####\s(.+)$/gm,  "<h5>$1</h5>");
  html = html.replace(/^####\s(.+)$/gm,   "<h4>$1</h4>");
  html = html.replace(/^###\s(.+)$/gm,    "<h3>$1</h3>");
  html = html.replace(/^##\s(.+)$/gm,     "<h2>$1</h2>");
  html = html.replace(/^#\s(.+)$/gm,      "<h1>$1</h1>");

  // Bold/Italic
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>");
  html = html.replace(/\*\*(.+?)\*\*/g,     "<strong>$1</strong>");
  html = html.replace(/\*(.+?)\*/g,         "<em>$1</em>");
  html = html.replace(/_(.+?)_/g,           "<em>$1</em>");

  // Inline code
  html = html.replace(/`(.+?)`/g, "<code>$1</code>");

  // Horizontal rule
  html = html.replace(/^---$/gm, "<hr>");

  // Blockquote
  html = html.replace(/^&gt;\s(.+)$/gm, "<blockquote>$1</blockquote>");

  // Unordered list
  html = html.replace(/^[-*]\s(.+)$/gm, "<li>$1</li>");
  html = html.replace(/(<li>.*<\/li>)(\n<li>)/g, "$1$2"); // keep consecutive
  html = html.replace(/((?:<li>.*<\/li>\n?)+)/g, "<ul>$1</ul>");

  // Ordered list
  html = html.replace(/^\d+\.\s(.+)$/gm, "<li>$1</li>");

  // Paragraphs (double newline)
  html = html.replace(/\n\n/g, "</p><p>");
  html = `<p>${html}</p>`;

  // Single newline to <br> inside paragraphs
  html = html.replace(/\n/g, "<br>");

  // Cleanup empty paragraphs
  html = html.replace(/<p>\s*<\/p>/g, "");
  html = html.replace(/<p>(<h[1-6]>)/g, "$1");
  html = html.replace(/(<\/h[1-6]>)<\/p>/g, "$1");
  html = html.replace(/<p>(<ul>)/g, "$1");
  html = html.replace(/(<\/ul>)<\/p>/g, "$1");
  html = html.replace(/<p>(<hr>)<\/p>/g, "$1");
  html = html.replace(/<p>(<blockquote>)/g, "$1");
  html = html.replace(/(<\/blockquote>)<\/p>/g, "$1");

  return html;
}

/* =========================================================
   Escape HTML
   ========================================================= */
function escapeHtml(str) {
  if (typeof str !== "string") return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/* =========================================================
   Word / Char / Reading Time Counter
   ========================================================= */
function textStats(text) {
  if (!text) return { chars: 0, words: 0, readTime: 0 };
  const words    = text.trim().split(/\s+/).filter(Boolean).length;
  const chars    = text.length;
  const readTime = Math.max(1, Math.ceil(words / 200));
  return { chars, words, readTime };
}

function formatStats(text) {
  const { words, chars, readTime } = textStats(text);
  return `${words} words · ${chars} chars · ~${readTime} min read`;
}

/* =========================================================
   History Management
   ========================================================= */
function saveToHistory(title, content, page) {
  const entry = {
    id:        Date.now(),
    title,
    content,
    page,
    timestamp: new Date().toLocaleString(),
  };
  state.conversationHistory.unshift(entry);
  if (state.conversationHistory.length > MAX_HISTORY) {
    state.conversationHistory = state.conversationHistory.slice(0, MAX_HISTORY);
  }
  localStorage.setItem(HISTORY_KEY, JSON.stringify(state.conversationHistory));
}

function clearHistory() {
  state.conversationHistory = [];
  localStorage.removeItem(HISTORY_KEY);
  showToast("History Cleared", "All conversation history has been removed.", "success");
}

/* =========================================================
   Copy to Clipboard
   ========================================================= */
async function copyToClipboard(text, btnEl) {
  try {
    await navigator.clipboard.writeText(text);
    const original = btnEl.textContent;
    btnEl.textContent = "Copied";
    btnEl.disabled = true;
    setTimeout(() => { btnEl.textContent = original; btnEl.disabled = false; }, 2000);
    showToast("Copied", "Response copied to clipboard.", "success");
  } catch {
    showToast("Copy Failed", "Unable to access clipboard.", "error");
  }
}

/* =========================================================
   Text-to-Speech
   ========================================================= */
function speakText(text) {
  if (!window.speechSynthesis) {
    showToast("TTS Not Supported", "Your browser does not support text-to-speech.", "warning");
    return;
  }
  window.speechSynthesis.cancel();
  const utterance   = new SpeechSynthesisUtterance(text.replace(/[#*_`]/g, ""));
  utterance.rate    = 0.9;
  utterance.pitch   = 1;
  utterance.volume  = 1;
  window.speechSynthesis.speak(utterance);
  showToast("Speaking", "Text-to-speech started. Click again to stop.", "info");
}

function stopSpeech() {
  if (window.speechSynthesis) window.speechSynthesis.cancel();
}

/* =========================================================
   Download as PDF (using browser print)
   ========================================================= */
function downloadAsPDF(content, title) {
  const printWindow = window.open("", "_blank", "width=800,height=600");
  if (!printWindow) {
    showToast("Popup Blocked", "Please allow popups and try again.", "warning");
    return;
  }

  const theme = document.documentElement.getAttribute("data-theme");
  const isDark = theme === "dark";

  printWindow.document.write(`
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>${escapeHtml(title)} — Healthcare AI</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    body {
      font-family: 'Inter', sans-serif;
      font-size: 14px;
      line-height: 1.7;
      color: #1e293b;
      max-width: 700px;
      margin: 40px auto;
      padding: 0 24px;
    }
    .header {
      border-bottom: 2px solid #0d7ee8;
      padding-bottom: 16px;
      margin-bottom: 24px;
    }
    .header h1 { font-size: 22px; color: #0d7ee8; margin: 0 0 4px; }
    .header p  { color: #64748b; font-size: 12px; margin: 0; }
    .content h2 { color: #0d7ee8; font-size: 16px; margin: 20px 0 8px; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; }
    .content h3 { color: #334155; font-size: 14px; margin: 14px 0 6px; }
    .content ul { padding-left: 20px; }
    .content li { margin-bottom: 4px; }
    .content strong { color: #1e293b; }
    .disclaimer {
      background: #fff7ed;
      border-left: 4px solid #f59e0b;
      padding: 12px 16px;
      border-radius: 4px;
      font-size: 12px;
      color: #92400e;
      margin-top: 24px;
    }
    .footer { margin-top: 32px; font-size: 11px; color: #94a3b8; text-align: center; border-top: 1px solid #e2e8f0; padding-top: 16px; }
    @media print { body { margin: 0; } }
  </style>
</head>
<body>
  <div class="header">
    <h1>${escapeHtml(title)}</h1>
    <p>Generated by Healthcare AI Clinical Assistant · ${new Date().toLocaleString()}</p>
  </div>
  <div class="content">
    ${renderMarkdown(content)}
  </div>
  <div class="disclaimer">
    Medical Disclaimer: This AI assistant is for educational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment.
  </div>
  <div class="footer">Healthcare AI Clinical Assistant · For educational purposes only · Not a substitute for professional medical advice</div>
</body>
</html>`);
  printWindow.document.close();
  setTimeout(() => {
    printWindow.focus();
    printWindow.print();
  }, 500);
}

/* =========================================================
   Voice Input
   ========================================================= */
function initVoiceInput(btnId, targetId) {
  const btn    = $(`#${btnId}`);
  const target = $(`#${targetId}`);
  if (!btn || !target) return;

  if (!("webkitSpeechRecognition" in window) && !("SpeechRecognition" in window)) {
    btn.style.display = "none";
    return;
  }

  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;

  btn.addEventListener("click", () => {
    if (state.isRecording) {
      state.voiceRecognition?.stop();
      btn.classList.remove("recording");
      btn.title = "Start voice input";
      state.isRecording = false;
      return;
    }

    const recognition     = new SR();
    recognition.lang      = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    state.voiceRecognition = recognition;
    state.isRecording      = true;
    btn.classList.add("recording");
    btn.title = "Stop recording";

    recognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      target.value += (target.value ? " " : "") + transcript;
      target.dispatchEvent(new Event("input"));
      showToast("Voice Captured", `"${transcript}"`, "success");
    };

    recognition.onerror = (e) => {
      showToast("Voice Error", `Speech recognition error: ${e.error}`, "error");
    };

    recognition.onend = () => {
      btn.classList.remove("recording");
      btn.title = "Start voice input";
      state.isRecording = false;
    };

    recognition.start();
  });
}

/* =========================================================
   Loading State Helpers
   ========================================================= */
function setLoading(loadingId, visible) {
  const el = $(`#${loadingId}`);
  if (el) el.classList.toggle("visible", visible);
}

function setResultVisible(cardId, visible) {
  const el = $(`#${cardId}`);
  if (el) el.classList.toggle("visible", visible);
}

/* =========================================================
   Generic API Caller
   ========================================================= */
async function callAPI(endpoint, payload, {
  loadingId, resultCardId, resultBodyId, resultTitleEl,
  title, pageTitle, generateBtnId
}) {
  if (state.isLoading) return;

  state.isLoading = true;
  const generateBtn = $(`#${generateBtnId}`);
  if (generateBtn) { generateBtn.disabled = true; generateBtn.textContent = "⏳ Generating…"; }

  setLoading(loadingId, true);
  setResultVisible(resultCardId, false);

  if (resultTitleEl) {
    const el = $(`#${resultTitleEl}`);
    if (el) el.textContent = title;
  }

  try {
    const response = await fetch(`${API_BASE}/${endpoint}`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(payload),
      signal:  AbortSignal.timeout(90000),
    });

    const data = await response.json();

    if (!response.ok || data.error) {
      const errMsg = data.error || `Server error ${response.status}`;
      showToast("API Error", errMsg, "error");
      return;
    }

    const content = data.result || "";
    state.lastResult      = content;
    state.lastResultTitle = title;

    // Render result
    const bodyEl = $(`#${resultBodyId}`);
    if (bodyEl) {
      const statsHtml = `<div class="result-meta">
        <span class="result-meta-item">📊 ${formatStats(content)}</span>
        <span class="result-meta-item">🕒 ${new Date().toLocaleTimeString()}</span>
      </div>`;
      bodyEl.innerHTML = statsHtml + `<div class="markdown-content">${renderMarkdown(content)}</div>`;
    }

    setResultVisible(resultCardId, true);
    saveToHistory(title, content, pageTitle);

    // Auto-scroll to result
    const card = $(`#${resultCardId}`);
    if (card) {
      setTimeout(() => card.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
    }

    showToast("Done!", `${title} generated successfully.`, "success");

  } catch (err) {
    if (err.name === "TimeoutError") {
      showToast("Timeout", "The request took too long. Please try again.", "error");
    } else if (err.name === "TypeError" && err.message.includes("fetch")) {
      showToast("Connection Error", "Cannot reach the API. Is the backend running?", "error");
    } else {
      showToast("Error", err.message || "An unexpected error occurred.", "error");
    }
  } finally {
    state.isLoading = false;
    if (generateBtn) {
      generateBtn.disabled = false;
      generateBtn.innerHTML = `<span class="btn-shimmer"></span>✨ Generate Analysis`;
    }
    setLoading(loadingId, false);
  }
}

/* =========================================================
   Form Validators
   ========================================================= */
function clearErrors(formId) {
  const form = $(`#${formId}`);
  if (!form) return;
  $$(".form-group.error", form).forEach(g => g.classList.remove("error"));
}

function showFieldError(fieldId, message) {
  const field = $(`#${fieldId}`);
  if (!field) return false;
  const group = field.closest(".form-group");
  if (group) {
    group.classList.add("error");
    const errEl = group.querySelector(".form-error");
    if (errEl) errEl.textContent = message;
  }
  field.focus();
  return true;
}

function validateRequired(fieldId, label) {
  const field = $(`#${fieldId}`);
  if (!field) return false;
  const val = field.value.trim();
  if (!val) {
    showFieldError(fieldId, `${label} is required.`);
    return false;
  }
  return true;
}

function validateAge(fieldId) {
  const field = $(`#${fieldId}`);
  if (!field) return false;
  const val = parseInt(field.value, 10);
  if (isNaN(val) || val < 0 || val > 120) {
    showFieldError(fieldId, "Age must be between 0 and 120.");
    return false;
  }
  return true;
}

/* =========================================================
   FEATURE 1 — Symptom Analyzer
   ========================================================= */
function initSymptomPage() {
  const form = $("#symptomForm");
  if (!form) return;

  // Character counter for symptoms textarea
  setupCharCounter("symptomSymptoms", "symptomSymptomsCount", 2000);
  setupCharCounter("symptomHistory",  "symptomHistoryCount",  2000);
  setupCharCounter("symptomMeds",     "symptomMedsCount",     1000);

  // Voice input
  initVoiceInput("voiceSymptoms", "symptomSymptoms");
  initVoiceInput("voiceHistory",  "symptomHistory");
  initVoiceInput("voiceMeds",     "symptomMeds");

  // Reset
  $("#symptomReset")?.addEventListener("click", () => {
    form.reset();
    clearErrors("symptomForm");
    setResultVisible("symptomResult", false);
    showToast("Reset", "Form has been cleared.", "info");
  });

  // Generate
  $("#symptomGenerate")?.addEventListener("click", async () => {
    clearErrors("symptomForm");
    const valid =
      validateAge("symptomAge") &&
      validateRequired("symptomSymptoms", "Current Symptoms") &&
      validateRequired("symptomDuration",  "Duration");
    if (!valid) {
      showToast("Validation Error", "Please fill all required fields correctly.", "error");
      return;
    }

    const payload = {
      age:               parseInt($("#symptomAge").value, 10),
      gender:            $("#symptomGender").value,
      medical_history:   $("#symptomHistory").value.trim() || "None",
      current_symptoms:  $("#symptomSymptoms").value.trim(),
      duration:          $("#symptomDuration").value.trim(),
      severity:          $("#symptomSeverity").value,
      current_medicines: $("#symptomMeds").value.trim() || "None",
    };

    await callAPI("symptom", payload, {
      loadingId:    "symptomLoading",
      resultCardId: "symptomResult",
      resultBodyId: "symptomResultBody",
      resultTitleEl:"symptomResultTitle",
      title:        "Symptom Analysis",
      pageTitle:    "Symptom Analyzer",
      generateBtnId:"symptomGenerate",
    });
  });

  // Result actions
  setupResultActions("symptomResult", "Symptom Analysis");
}

/* =========================================================
   FEATURE 2 — Medical Term Explainer
   ========================================================= */
function initMedTermPage() {
  setupCharCounter("medtermInput", "medtermCount", 200);
  initVoiceInput("voiceMedterm", "medtermInput");

  $("#medtermReset")?.addEventListener("click", () => {
    $("#medtermForm")?.reset();
    clearErrors("medtermForm");
    setResultVisible("medtermResult", false);
    showToast("Reset", "Form cleared.", "info");
  });

  // Quick term examples
  $$(".term-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const inp = $("#medtermInput");
      if (inp) { inp.value = chip.dataset.term; inp.dispatchEvent(new Event("input")); }
    });
  });

  $("#medtermGenerate")?.addEventListener("click", async () => {
    clearErrors("medtermForm");
    if (!validateRequired("medtermInput", "Medical Term")) {
      showToast("Validation Error", "Please enter a medical term.", "error");
      return;
    }

    const payload = { term: $("#medtermInput").value.trim() };

    await callAPI("medical-term", payload, {
      loadingId:    "medtermLoading",
      resultCardId: "medtermResult",
      resultBodyId: "medtermResultBody",
      resultTitleEl:"medtermResultTitle",
      title:        `Medical Term: ${payload.term}`,
      pageTitle:    "Medical Term Explainer",
      generateBtnId:"medtermGenerate",
    });
  });

  setupResultActions("medtermResult", "Medical Term Explanation");
}

/* =========================================================
   FEATURE 3 — Prescription Explainer
   ========================================================= */
function initPrescriptionPage() {
  setupCharCounter("prescriptionMeds", "prescriptionMedsCount", 1000);
  initVoiceInput("voicePrescription", "prescriptionMeds");

  $("#prescriptionReset")?.addEventListener("click", () => {
    $("#prescriptionForm")?.reset();
    clearErrors("prescriptionForm");
    setResultVisible("prescriptionResult", false);
    showToast("Reset", "Form cleared.", "info");
  });

  $("#prescriptionGenerate")?.addEventListener("click", async () => {
    clearErrors("prescriptionForm");
    if (!validateRequired("prescriptionMeds", "Medicine Names")) {
      showToast("Validation Error", "Please enter at least one medicine name.", "error");
      return;
    }

    const payload = { medicines: $("#prescriptionMeds").value.trim() };

    await callAPI("prescription", payload, {
      loadingId:    "prescriptionLoading",
      resultCardId: "prescriptionResult",
      resultBodyId: "prescriptionResultBody",
      resultTitleEl:"prescriptionResultTitle",
      title:        "Prescription Explanation",
      pageTitle:    "Prescription Explainer",
      generateBtnId:"prescriptionGenerate",
    });
  });

  setupResultActions("prescriptionResult", "Prescription Explanation");
}

/* =========================================================
   FEATURE 4 — Health Tips
   ========================================================= */
function initHealthTipsPage() {
  // Category selection
  $$(".category-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      $$(".category-btn").forEach(b => b.classList.remove("selected"));
      btn.classList.add("selected");
      state.selectedCategory = btn.dataset.category;
    });
  });

  $("#healthtipsReset")?.addEventListener("click", () => {
    $$(".category-btn").forEach(b => b.classList.remove("selected"));
    state.selectedCategory = "";
    setResultVisible("healthtipsResult", false);
    showToast("Reset", "Selection cleared.", "info");
  });

  $("#healthtipsGenerate")?.addEventListener("click", async () => {
    if (!state.selectedCategory) {
      showToast("Select a Category", "Please select a health category first.", "warning");
      return;
    }

    const payload = { category: state.selectedCategory };

    await callAPI("health-tips", payload, {
      loadingId:    "healthtipsLoading",
      resultCardId: "healthtipsResult",
      resultBodyId: "healthtipsResultBody",
      resultTitleEl:"healthtipsResultTitle",
      title:        `Health Tips: ${state.selectedCategory}`,
      pageTitle:    "Health Tips",
      generateBtnId:"healthtipsGenerate",
    });
  });

  setupResultActions("healthtipsResult", "Health Tips");
}

/* =========================================================
   FEATURE 5 — Medical Report Summarizer
   ========================================================= */
function initReportPage() {
  setupCharCounter("reportText", "reportCount", 4000);
  initVoiceInput("voiceReport", "reportText");

  $("#reportReset")?.addEventListener("click", () => {
    $("#reportForm")?.reset();
    clearErrors("reportForm");
    setResultVisible("reportResult", false);
    showToast("Reset", "Form cleared.", "info");
  });

  $("#reportGenerate")?.addEventListener("click", async () => {
    clearErrors("reportForm");
    const reportVal = $("#reportText")?.value?.trim() || "";
    if (reportVal.length < 20) {
      showFieldError("reportText", "Please paste a medical report (minimum 20 characters).");
      showToast("Validation Error", "Report text is too short.", "error");
      return;
    }

    const payload = { report_text: reportVal };

    await callAPI("report-summary", payload, {
      loadingId:    "reportLoading",
      resultCardId: "reportResult",
      resultBodyId: "reportResultBody",
      resultTitleEl:"reportResultTitle",
      title:        "Medical Report Summary",
      pageTitle:    "Medical Report Summarizer",
      generateBtnId:"reportGenerate",
    });
  });

  setupResultActions("reportResult", "Medical Report Summary");
}

/* =========================================================
   FEATURE 6 — Emergency Checker
   ========================================================= */
function initEmergencyPage() {
  setupCharCounter("emergencySymptoms", "emergencyCount", 2000);
  initVoiceInput("voiceEmergency", "emergencySymptoms");

  $("#emergencyReset")?.addEventListener("click", () => {
    $("#emergencyForm")?.reset();
    clearErrors("emergencyForm");
    setResultVisible("emergencyResult", false);
    showToast("Reset", "Form cleared.", "info");
  });

  $("#emergencyGenerate")?.addEventListener("click", async () => {
    clearErrors("emergencyForm");
    const sympVal = $("#emergencySymptoms")?.value?.trim() || "";
    if (sympVal.length < 5) {
      showFieldError("emergencySymptoms", "Please describe your symptoms (minimum 5 characters).");
      showToast("Validation Error", "Please describe symptoms in more detail.", "error");
      return;
    }

    const payload = { symptoms: sympVal };

    await callAPI("emergency", payload, {
      loadingId:    "emergencyLoading",
      resultCardId: "emergencyResult",
      resultBodyId: "emergencyResultBody",
      resultTitleEl:"emergencyResultTitle",
      title:        "Emergency Risk Assessment",
      pageTitle:    "Emergency Checker",
      generateBtnId:"emergencyGenerate",
    });
  });

  setupResultActions("emergencyResult", "Emergency Risk Assessment");
}

/* =========================================================
   Shared: Result Action Buttons
   ========================================================= */
function setupResultActions(cardId, title) {
  const card = $(`#${cardId}`);
  if (!card) return;

  card.querySelector(".result-copy-btn")?.addEventListener("click", async function () {
    const content = state.lastResult || "";
    if (!content) return;
    await copyToClipboard(content, this);
  });

  card.querySelector(".result-tts-btn")?.addEventListener("click", () => {
    const content = state.lastResult || "";
    if (!content) return;
    if (window.speechSynthesis?.speaking) { stopSpeech(); return; }
    speakText(content);
  });

  card.querySelector(".result-pdf-btn")?.addEventListener("click", () => {
    const content = state.lastResult || "";
    if (!content) return;
    downloadAsPDF(content, state.lastResultTitle || title);
    showToast("PDF", "Opening print dialog…", "info");
  });
}

/* =========================================================
   Character Counter
   ========================================================= */
function setupCharCounter(inputId, counterId, maxLen) {
  const input   = $(`#${inputId}`);
  const counter = $(`#${counterId}`);
  if (!input || !counter) return;

  const update = () => {
    const len = input.value.length;
    counter.textContent = `${len} / ${maxLen}`;
    counter.style.color = len > maxLen * 0.9 ? "var(--danger)" : "var(--text-muted)";
  };

  input.addEventListener("input", update);
  update();
}

/* =========================================================
   Dashboard — Quick Action Cards
   ========================================================= */
function initDashboard() {
  $$(".feature-card[data-navigate]").forEach(card => {
    card.addEventListener("click", () => navigate(card.dataset.navigate));
  });

  $$(".stat-card[data-navigate]").forEach(card => {
    card.addEventListener("click", () => navigate(card.dataset.navigate));
  });

  $(".hero-btn-primary")?.addEventListener("click", () => navigate("symptom"));
  $(".hero-btn-secondary")?.addEventListener("click", () => navigate("emergency"));
}

/* =========================================================
   Keyboard Shortcuts
   ========================================================= */
function initKeyboardShortcuts() {
  document.addEventListener("keydown", (e) => {
    // ? — Show shortcuts panel
    if (e.key === "?" && !e.ctrlKey && !e.metaKey) {
      const panel = $("#shortcutsPanel");
      const active = document.activeElement;
      // Don't trigger in inputs
      if (active.tagName === "INPUT" || active.tagName === "TEXTAREA" || active.tagName === "SELECT") return;
      panel?.classList.toggle("visible");
    }

    // Escape — Close modals, sidebar
    if (e.key === "Escape") {
      $("#shortcutsPanel")?.classList.remove("visible");
      closeMobileSidebar();
      stopSpeech();
    }

    // Ctrl/Cmd + D — Toggle dark mode
    if ((e.ctrlKey || e.metaKey) && e.key === "d") {
      e.preventDefault();
      toggleTheme();
    }

    // Ctrl/Cmd + 1-8 — Navigate pages
    if ((e.ctrlKey || e.metaKey) && !e.shiftKey) {
      const pageMap = {
        "1": "dashboard",
        "2": "symptom",
        "3": "medterm",
        "4": "prescription",
        "5": "healthtips",
        "6": "report",
        "7": "emergency",
        "8": "about",
      };
      if (pageMap[e.key]) {
        e.preventDefault();
        navigate(pageMap[e.key]);
      }
    }
  });

  // Close shortcuts panel on backdrop click
  $("#shortcutsBackdrop")?.addEventListener("click", () => {
    $("#shortcutsPanel")?.classList.remove("visible");
  });
}

/* =========================================================
   Init All
   ========================================================= */
function init() {
  initTheme();
  checkAPIStatus();
  setInterval(checkAPIStatus, 30000);

  // Navigation
  $$(".nav-item[data-page]").forEach(item => {
    item.addEventListener("click", () => navigate(item.dataset.page));
  });

  // Hamburger
  $("#hamburgerBtn")?.addEventListener("click", openMobileSidebar);
  $("#sidebarOverlay")?.addEventListener("click", closeMobileSidebar);

  // Theme toggle
  $("#themeToggle")?.addEventListener("click", toggleTheme);

  // Shortcuts toggle button
  $("#shortcutsBtn")?.addEventListener("click", () => {
    $("#shortcutsPanel")?.classList.toggle("visible");
  });

  // Clear history
  $("#clearHistoryBtn")?.addEventListener("click", () => {
    clearHistory();
  });

  // Init all pages
  initDashboard();
  initSymptomPage();
  initMedTermPage();
  initPrescriptionPage();
  initHealthTipsPage();
  initReportPage();
  initEmergencyPage();

  // Keyboard shortcuts
  initKeyboardShortcuts();

  // Show dashboard by default
  navigate("dashboard");

  // Welcome toast
  setTimeout(() => {
    showToast(
      "Welcome! 👋",
      "Healthcare AI is ready. Add your Grok API key to get started.",
      "info",
      5000
    );
  }, 600);
}

/* =========================================================
   Boot
   ========================================================= */
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}

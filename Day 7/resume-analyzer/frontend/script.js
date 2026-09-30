// ==========================================================================
// STATE MANAGEMENT & GLOBALS
// ==========================================================================
let currentReportData = null;
let currentCharts = {
    radar: null,
    bar: null,
    pie: null
};

// ==========================================================================
// INITIALIZATION & DOM EVENTS
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("file-input");
    const btnBrowse = document.getElementById("btn-browse");
    const btnHistory = document.getElementById("btn-history");
    const btnCloseHistory = document.getElementById("btn-close-history");
    const sidebarHistory = document.getElementById("sidebar-history");
    const sidebarOverlay = document.getElementById("sidebar-overlay");
    const btnClearHistory = document.getElementById("btn-clear-history");
    const btnThemeToggle = document.getElementById("theme-toggle");
    const btnBack = document.getElementById("btn-back");
    const btnDownloadPdf = document.getElementById("btn-download-pdf");
    const btnCopySuggestions = document.getElementById("btn-copy-suggestions");
    const btnCloseNotice = document.getElementById("btn-close-notice");
    const noticeBanner = document.getElementById("notice-banner");

    // Initialize Theme
    const savedTheme = localStorage.getItem("cvgrok_theme") || "dark";
    document.documentElement.setAttribute("data-theme", savedTheme);

    // Initialize History
    renderHistory();

    // Theme Toggle Handler
    btnThemeToggle.addEventListener("click", () => {
        const activeTheme = document.documentElement.getAttribute("data-theme");
        const nextTheme = activeTheme === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", nextTheme);
        localStorage.setItem("cvgrok_theme", nextTheme);
        // Redraw charts to align with new theme text/grid colors
        if (currentReportData) {
            renderCharts(currentReportData.skills_heatmap);
        }
    });

    // History Sidebar Toggles
    btnHistory.addEventListener("click", () => {
        sidebarHistory.classList.add("active");
        sidebarOverlay.classList.add("active");
    });

    const closeHistory = () => {
        sidebarHistory.classList.remove("active");
        sidebarOverlay.classList.remove("active");
    };

    btnCloseHistory.addEventListener("click", closeHistory);
    sidebarOverlay.addEventListener("click", closeHistory);

    btnClearHistory.addEventListener("click", () => {
        if (confirm("Are you sure you want to clear your analysis history?")) {
            localStorage.removeItem("cvgrok_history");
            renderHistory();
            closeHistory();
        }
    });

    // Landing View Back Button
    btnBack.addEventListener("click", () => {
        switchView("section-landing");
        currentReportData = null;
        // Clean up temporary uploads
        fetch("/api/cleanup", { method: "DELETE" }).catch(err => console.log("Cleanup failed:", err));
    });

    // Notice banner close
    if (btnCloseNotice) {
        btnCloseNotice.addEventListener("click", () => {
            noticeBanner.classList.add("hidden");
        });
    }

    // Browse files button click
    btnBrowse.addEventListener("click", (e) => {
        e.stopPropagation();
        fileInput.click();
    });

    // File input changes
    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    // Drag & Drop event listeners
    dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("dragover");
    });

    dropzone.addEventListener("dragleave", () => {
        dropzone.classList.remove("dragover");
    });

    dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    // Dashboard Tabs handlers (Formatting/Grammar/Career suggestions)
    const tipsTabBtns = document.querySelectorAll(".tips-tab-btn");
    tipsTabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tipsTabBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            
            const targetTab = btn.getAttribute("data-tab");
            const panes = document.querySelectorAll(".tips-pane");
            panes.forEach(pane => {
                pane.classList.remove("active-pane");
                if (pane.id === `pane-${targetTab}`) {
                    pane.classList.add("active-pane");
                }
            });
        });
    });

    // Dashboard Chart Tab handlers (Radar/Bar/Pie)
    const chartTabBtns = document.querySelectorAll(".tab-btn");
    chartTabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            chartTabBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            
            const targetChart = btn.getAttribute("data-chart");
            const canvases = document.querySelectorAll(".chart-canvas");
            canvases.forEach(canvas => {
                canvas.classList.remove("active-canvas");
                canvas.classList.add("hidden-canvas");
                if (canvas.id === `skills${capitalize(targetChart)}Chart`) {
                    canvas.classList.remove("hidden-canvas");
                    canvas.classList.add("active-canvas");
                }
            });
        });
    });

    // Copy Suggestions handler
    btnCopySuggestions.addEventListener("click", () => {
        if (!currentReportData) return;
        
        const textToCopy = `
=== ATS SCORE: ${currentReportData.ats_score}% ===
=== READABILITY: ${currentReportData.readability_score}% ===
=== INTERVIEW PROBABILITY: ${currentReportData.interview_probability}% ===

--- SUMMARY ---
${currentReportData.summary}

--- KEY STRENGTHS ---
${currentReportData.strengths.map(s => `• ${s}`).join("\n")}

--- AREAS FOR IMPROVEMENT ---
${currentReportData.weaknesses.map(w => `• ${w}`).join("\n")}

--- ACTIONS & RECOMMENDATIONS ---
${currentReportData.recommendations.map(r => `• ${r}`).join("\n")}
        `.trim();

        navigator.clipboard.writeText(textToCopy)
            .then(() => alert("Analysis report summary copied to clipboard!"))
            .catch(err => alert("Failed to copy text: " + err));
    });

    // Download PDF handler
    btnDownloadPdf.addEventListener("click", async () => {
        if (!currentReportData) return;
        
        btnDownloadPdf.disabled = true;
        const origContent = btnDownloadPdf.innerHTML;
        btnDownloadPdf.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> Generating PDF...`;

        try {
            const response = await fetch("/api/report", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(currentReportData)
            });

            if (!response.ok) throw new Error("Failed to generate report PDF.");

            const blob = await response.blob();
            const downloadUrl = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = downloadUrl;
            a.download = `ATS_Report_${currentReportData.contact_info.name.replace(/\s+/g, "_")}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(downloadUrl);
        } catch (error) {
            console.error(error);
            alert("Error downloading report: " + error.message);
        } finally {
            btnDownloadPdf.disabled = false;
            btnDownloadPdf.innerHTML = origContent;
        }
    });
});

// ==========================================================================
// FILE UPLOAD & PROCESSING PIPELINE
// ==========================================================================
async function handleFileUpload(file) {
    // 1. Validation
    if (!file.name.toLowerCase().endsWith(".pdf")) {
        alert("Invalid file format. Please upload a PDF resume.");
        return;
    }
    if (file.size > 10 * 1024 * 1024) {
        alert("File is too large. Maximum supported file size is 10MB.");
        return;
    }

    // Toggle View to Processing State
    const dropzone = document.getElementById("dropzone");
    const processingBox = document.getElementById("processing-box");
    const fill = document.getElementById("progress-bar-fill");
    const percentageText = document.getElementById("processing-percentage");
    const statusText = document.getElementById("processing-status-text");

    dropzone.classList.add("hidden");
    processingBox.classList.remove("hidden");
    
    // Reset steps styling
    resetSteps();

    // Trigger step 1: Extracting text
    updateStep(1, "active");
    
    // Smooth progress simulation helper
    let progress = 0;
    const progressInterval = setInterval(() => {
        if (progress < 90) {
            progress += Math.floor(Math.random() * 5) + 1;
            if (progress > 90) progress = 90;
            fill.style.width = `${progress}%`;
            percentageText.textContent = `${progress}%`;
        }
    }, 150);

    const formData = new FormData();
    formData.append("file", file);

    try {
        // Step 1 & 2: Send PDF to backend for text extraction & syntactic parsing
        statusText.textContent = "Uploading & extracting resume text...";
        const uploadResponse = await fetch("/api/upload", {
            method: "POST",
            body: formData
        });

        if (!uploadResponse.ok) {
            const errData = await uploadResponse.json();
            throw new Error(errData.detail || "PDF Text extraction failed.");
        }

        const parseResult = await uploadResponse.json();
        updateStep(1, "completed");
        updateStep(2, "active");
        
        statusText.textContent = "Analyzing metadata structure...";
        await sleep(600); // Small UI buffer so user sees state changes
        updateStep(2, "completed");
        updateStep(3, "active");

        // Step 3: Send parsed details to Grok AI for ATS semantic analysis
        statusText.textContent = "Consulting Grok AI for deep ATS analysis...";
        const analyzeResponse = await fetch("/api/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                text: parseResult.text,
                contact_info: parseResult.contact_info
            })
        });

        if (!analyzeResponse.ok) {
            const errData = await analyzeResponse.json();
            throw new Error(errData.detail || "Grok AI analysis failed.");
        }

        const auditReport = await analyzeResponse.json();
        updateStep(3, "completed");
        updateStep(4, "active");

        statusText.textContent = "Assembling your analytics dashboard...";
        await sleep(500);

        // Completion
        clearInterval(progressInterval);
        fill.style.width = "100%";
        percentageText.textContent = "100%";
        updateStep(4, "completed");
        await sleep(300);

        // Show dashboard with data
        loadDashboard(auditReport);
        saveToHistory(auditReport);

    } catch (error) {
        clearInterval(progressInterval);
        console.error(error);
        alert("Processing Error: " + error.message);
        
        // Return to upload landing view
        dropzone.classList.remove("hidden");
        processingBox.classList.add("hidden");
    }
}

// ==========================================================================
// VIEW CONTROLLER & DASHBOARD LOADER
// ==========================================================================
function switchView(viewId) {
    const landing = document.getElementById("section-landing");
    const dashboard = document.getElementById("section-dashboard");
    const dropzone = document.getElementById("dropzone");
    const processingBox = document.getElementById("processing-box");

    if (viewId === "section-landing") {
        landing.classList.add("active-section");
        landing.classList.remove("hidden-section");
        dashboard.classList.add("hidden-section");
        dashboard.classList.remove("active-section");
        
        // Reset upload box states
        dropzone.classList.remove("hidden");
        processingBox.classList.add("hidden");
        document.getElementById("file-input").value = "";
    } else {
        dashboard.classList.add("active-section");
        dashboard.classList.remove("hidden-section");
        landing.classList.add("hidden-section");
        landing.classList.remove("active-section");
    }
}

function loadDashboard(report) {
    currentReportData = report;
    switchView("section-dashboard");

    // Display fallback banner notice if GROK failed or skipped
    const banner = document.getElementById("notice-banner");
    if (report.is_fallback) {
        banner.classList.remove("hidden");
    } else {
        banner.classList.add("hidden");
    }

    // Populate contact fields
    const contact = report.contact_info || {};
    document.getElementById("cand-name").textContent = contact.name || "Candidate Name";
    document.getElementById("cand-email").textContent = contact.email || "N/A";
    document.getElementById("cand-phone").textContent = contact.phone || "N/A";
    document.getElementById("cand-linkedin").textContent = cleanLinkText(contact.linkedin) || "N/A";
    document.getElementById("cand-github").textContent = cleanLinkText(contact.github) || "N/A";

    // Dynamic Circular Progress for ATS Match Score
    animateCircularScore(report.ats_score || 0);

    // Other linear metric bars
    animateLinearMetric("readability-score-text", "readability-bar-fill", report.readability_score || 0);
    animateLinearMetric("interview-prob-text", "interview-prob-fill", report.interview_probability || 0);

    // Summary text
    document.getElementById("ats-summary-text").textContent = report.summary || "No description provided.";
    document.getElementById("interview-readiness-text").textContent = report.interview_readiness || "No details provided.";

    // Strengths & Weaknesses lists
    populateList("strengths-list", report.strengths || []);
    populateList("weaknesses-list", report.weaknesses || []);

    // Missing keywords tags
    const missingContainer = document.getElementById("missing-keywords-list");
    missingContainer.innerHTML = "";
    if (report.missing_keywords && report.missing_keywords.length > 0) {
        report.missing_keywords.forEach(kw => {
            const tag = document.createElement("span");
            tag.className = "keyword-missing-tag";
            tag.textContent = kw;
            missingContainer.appendChild(tag);
        });
    } else {
        missingContainer.innerHTML = "<p class='summary-text'>No missing keywords identified! Excellent match.</p>";
    }

    // Keyword heatmap tags
    const heatmapContainer = document.getElementById("keyword-heatmap");
    heatmapContainer.innerHTML = "";
    if (report.skills_heatmap && report.skills_heatmap.length > 0) {
        report.skills_heatmap.forEach(item => {
            const tag = document.createElement("div");
            const impClass = item.importance.toLowerCase() === "high" ? "tag-high" : 
                             (item.importance.toLowerCase() === "medium" ? "tag-medium" : "tag-low");
            
            tag.className = `heatmap-tag ${impClass}`;
            tag.innerHTML = `
                <span>${item.keyword}</span>
                <span class="tag-freq">${item.frequency}x</span>
            `;
            heatmapContainer.appendChild(tag);
        });
    } else {
        heatmapContainer.innerHTML = "<p class='summary-text'>Add technical and soft skills to map keyword densities.</p>";
    }

    // Interactive Checklist
    const checklistContainer = document.getElementById("improvement-checklist");
    checklistContainer.innerHTML = "";
    if (report.improvement_checklist && report.improvement_checklist.length > 0) {
        report.improvement_checklist.forEach((item, index) => {
            const div = document.createElement("div");
            const isCompleted = item.status.toLowerCase() === "completed";
            div.className = `checklist-item ${isCompleted ? 'checked' : ''}`;
            
            div.innerHTML = `
                <input type="checkbox" id="chk-${index}" ${isCompleted ? 'checked' : ''}>
                <label for="chk-${index}" class="checklist-text">${item.item}</label>
            `;
            
            // Toggle checklist click
            div.querySelector("input").addEventListener("change", (e) => {
                if (e.target.checked) {
                    div.classList.add("checked");
                    report.improvement_checklist[index].status = "completed";
                } else {
                    div.classList.remove("checked");
                    report.improvement_checklist[index].status = "pending";
                }
                // Save state back to history
                updateActiveReportInHistory(report);
            });
            
            checklistContainer.appendChild(div);
        });
    } else {
        checklistContainer.innerHTML = "<p class='summary-text'>Checklist is empty.</p>";
    }

    // Populating sub suggestions tab panes
    populateList("formatting-tips-list", report.formatting_suggestions || []);
    populateList("grammar-tips-list", report.grammar || []);
    populateList("career-tips-list", report.career_suggestions || []);

    // Render Skills Charts
    renderCharts(report.skills_heatmap || []);
}

// ==========================================================================
// CHART GENERATORS (Chart.js)
// ==========================================================================
function renderCharts(skillsData) {
    // Destroy existing instances if present
    if (currentCharts.radar) currentCharts.radar.destroy();
    if (currentCharts.bar) currentCharts.bar.destroy();
    if (currentCharts.pie) currentCharts.pie.destroy();

    const isDark = document.documentElement.getAttribute("data-theme") === "dark";
    const textThemeColor = isDark ? "#E2E8F0" : "#0F172A";
    const gridThemeColor = isDark ? "rgba(255,255,255,0.06)" : "rgba(15,23,42,0.06)";

    // Prepare chart labels and values based on heatmap
    let labels = [];
    let frequencies = [];
    let radarPoints = []; // Represents weights: High=10, Medium=6, Low=3
    let pieCounts = { high: 0, medium: 0, low: 0 };

    if (skillsData && skillsData.length > 0) {
        // Take top 8 skills for clean display on radar & bar charts
        skillsData.slice(0, 8).forEach(item => {
            labels.push(item.keyword);
            frequencies.push(item.frequency);
            
            const imp = item.importance.toLowerCase();
            if (imp === "high") {
                radarPoints.push(10);
            } else if (imp === "medium") {
                radarPoints.push(6);
            } else {
                radarPoints.push(3);
            }
        });

        // Compute categories for Pie chart
        skillsData.forEach(item => {
            const imp = item.importance.toLowerCase();
            if (imp === "high") pieCounts.high++;
            else if (imp === "medium") pieCounts.medium++;
            else pieCounts.low++;
        });
    } else {
        // Hardcode mock data for visual charts validation if empty
        labels = ["Python", "Algorithms", "Database", "Design", "Testing", "FastAPI"];
        frequencies = [4, 2, 3, 1, 2, 3];
        radarPoints = [10, 6, 10, 3, 6, 10];
        pieCounts = { high: 3, medium: 2, low: 1 };
    }

    // 1. Radar Chart Setup
    const ctxRadar = document.getElementById("skillsRadarChart").getContext("2d");
    currentCharts.radar = new Chart(ctxRadar, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Keyword Weight / Priority',
                data: radarPoints,
                backgroundColor: 'rgba(59, 130, 246, 0.2)',
                borderColor: '#3B82F6',
                borderWidth: 2,
                pointBackgroundColor: '#8B5CF6',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#8B5CF6'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                r: {
                    angleLines: { color: gridThemeColor },
                    grid: { color: gridThemeColor },
                    pointLabels: { color: textThemeColor, font: { family: 'Plus Jakarta Sans', size: 10 } },
                    ticks: { display: false },
                    suggestedMin: 0,
                    suggestedMax: 10
                }
            }
        }
    });

    // 2. Bar Chart Setup
    const ctxBar = document.getElementById("skillsBarChart").getContext("2d");
    currentCharts.bar = new Chart(ctxBar, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Mentions in Resume',
                data: frequencies,
                backgroundColor: 'rgba(139, 92, 246, 0.55)',
                borderColor: '#8B5CF6',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: textThemeColor, font: { family: 'Plus Jakarta Sans', size: 9 } }
                },
                y: {
                    grid: { color: gridThemeColor },
                    ticks: { color: textThemeColor, stepSize: 1, font: { family: 'Plus Jakarta Sans', size: 9 } }
                }
            }
        }
    });

    // 3. Pie Chart Setup
    const ctxPie = document.getElementById("skillsPieChart").getContext("2d");
    currentCharts.pie = new Chart(ctxPie, {
        type: 'doughnut',
        data: {
            labels: ['High Priority', 'Medium Priority', 'Low Priority'],
            datasets: [{
                data: [pieCounts.high, pieCounts.medium, pieCounts.low],
                backgroundColor: [
                    'rgba(16, 185, 129, 0.65)',
                    'rgba(59, 130, 246, 0.65)',
                    'rgba(100, 116, 139, 0.55)'
                ],
                borderColor: isDark ? '#161E31' : '#fff',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: textThemeColor, font: { family: 'Plus Jakarta Sans', size: 9 } }
                }
            },
            cutout: '60%'
        }
    });
}

// ==========================================================================
// HISTORY CONTROLLER (LocalStorage)
// ==========================================================================
function saveToHistory(report) {
    let history = [];
    try {
        history = JSON.parse(localStorage.getItem("cvgrok_history")) || [];
    } catch(e) {
        history = [];
    }

    // Prevent duplicate entries for the same analysis session
    const existingIndex = history.findIndex(item => 
        item.file_name === report.file_name && 
        item.contact_info.name === report.contact_info.name
    );
    
    const entry = {
        id: report.id || uuidv4(),
        file_name: report.file_name,
        ats_score: report.ats_score,
        date: new Date().toLocaleString(),
        report: report
    };

    if (existingIndex !== -1) {
        history[existingIndex] = entry; // overwrite
    } else {
        history.unshift(entry); // add to top
    }

    localStorage.setItem("cvgrok_history", JSON.stringify(history.slice(0, 10))); // keep top 10
    renderHistory();
}

function updateActiveReportInHistory(report) {
    let history = [];
    try {
        history = JSON.parse(localStorage.getItem("cvgrok_history")) || [];
        const index = history.findIndex(item => item.report.file_name === report.file_name);
        if (index !== -1) {
            history[index].report = report;
            localStorage.setItem("cvgrok_history", JSON.stringify(history));
        }
    } catch(e) {
        console.error("Error updating history checklist state:", e);
    }
}

function renderHistory() {
    const list = document.getElementById("history-list");
    list.innerHTML = "";
    
    let history = [];
    try {
        history = JSON.parse(localStorage.getItem("cvgrok_history")) || [];
    } catch(e) {
        history = [];
    }

    if (history.length === 0) {
        list.innerHTML = `<p class="empty-history-text">No previous analyses found.</p>`;
        return;
    }

    history.forEach(item => {
        const card = document.createElement("div");
        card.className = "history-card";
        card.innerHTML = `
            <div class="history-meta">
                <span class="history-name">${item.report.contact_info.name || item.file_name}</span>
                <span class="history-date">${item.date}</span>
            </div>
            <div class="history-score">${item.ats_score}%</div>
        `;
        
        // Clicking load history item
        card.addEventListener("click", () => {
            loadDashboard(item.report);
            // close sidebar history
            document.getElementById("sidebar-history").classList.remove("active");
            document.getElementById("sidebar-overlay").classList.remove("active");
        });
        
        list.appendChild(card);
    });
}

// ==========================================================================
// UTILITY FUNCTIONS
// ==========================================================================
function animateCircularScore(targetScore) {
    const fill = document.getElementById("score-ring-fill");
    const valText = document.getElementById("ats-score-text");
    
    // Circumference of r=85 is 534
    const circumference = 534;
    
    // Animate stroke ring dashoffset
    const offsetValue = circumference - (circumference * targetScore) / 100;
    fill.style.strokeDashoffset = offsetValue;
    
    // Set circle stroke color depending on score
    if (targetScore >= 80) fill.style.stroke = "var(--success)";
    else if (targetScore >= 50) fill.style.stroke = "var(--warning)";
    else fill.style.stroke = "var(--danger)";

    // Text count animation
    let current = 0;
    if (targetScore === 0) {
        valText.textContent = "0%";
        return;
    }
    const timer = setInterval(() => {
        current += 1;
        valText.textContent = `${current}%`;
        if (current >= targetScore) {
            clearInterval(timer);
            valText.textContent = `${targetScore}%`;
        }
    }, Math.floor(1500 / targetScore));
}

function animateLinearMetric(labelId, barId, targetValue) {
    const label = document.getElementById(labelId);
    const bar = document.getElementById(barId);
    
    // set bar width
    bar.style.width = `${targetValue}%`;
    
    // animate text percentage
    let current = 0;
    if (targetValue === 0) {
        label.textContent = "0%";
        return;
    }
    const timer = setInterval(() => {
        current += 1;
        label.textContent = `${current}%`;
        if (current >= targetValue) {
            clearInterval(timer);
            label.textContent = `${targetValue}%`;
        }
    }, Math.floor(1200 / targetValue));
}

function populateList(elementId, items) {
    const ul = document.getElementById(elementId);
    ul.innerHTML = "";
    if (items && items.length > 0) {
        items.forEach(text => {
            const li = document.createElement("li");
            li.textContent = text;
            ul.appendChild(li);
        });
    } else {
        ul.innerHTML = "<li>No specific points identified.</li>";
    }
}

function resetSteps() {
    const steps = document.querySelectorAll(".step");
    steps.forEach(step => {
        step.className = "step";
        const icon = step.querySelector(".step-icon");
        icon.className = "fa-solid fa-circle-notch step-icon";
    });
}

function updateStep(stepNum, status) {
    const step = document.getElementById(`step-${stepNum}`);
    if (!step) return;
    
    const icon = step.querySelector(".step-icon");
    if (status === "active") {
        step.className = "step active";
        icon.className = "fa-solid fa-circle-notch fa-spin step-icon";
    } else if (status === "completed") {
        step.className = "step completed";
        icon.className = "fa-solid fa-circle-check step-icon";
    }
}

function cleanLinkText(link) {
    if (!link || link === "N/A") return "";
    return link.replace(/https?:\/\/(www\.)?/, "");
}

function capitalize(str) {
    if (!str) return "";
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function uuidv4() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

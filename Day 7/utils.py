import os
import re
import fitz  # PyMuPDF
import pdfplumber
from datetime import datetime
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfgen import canvas

# ==========================================================================
# 1. PDF TEXT EXTRACTION & METADATA PARSING
# ==========================================================================
def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts raw text from a PDF file using PyMuPDF with a fallback to pdfplumber."""
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception as e:
        print(f"PyMuPDF extraction failed: {e}")
        text = ""

    if not text.strip():
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"pdfplumber extraction failed: {e}")

    return text.strip()

def parse_contact_info(text: str) -> Dict[str, str]:
    """Uses regex and heuristics to extract Name, Email, Phone, LinkedIn, and GitHub."""
    info = {
        "name": "",
        "email": "",
        "phone": "",
        "linkedin": "",
        "github": ""
    }
    
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if email_match:
        info["email"] = email_match.group(0)

    phone_match = re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    if phone_match:
        info["phone"] = phone_match.group(0)

    linkedin_match = re.search(r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-]+/?', text, re.IGNORECASE)
    if linkedin_match:
        info["linkedin"] = linkedin_match.group(0)

    github_match = re.search(r'(?:https?://)?(?:www\.)?github\.com/[\w\-]+/?', text, re.IGNORECASE)
    if github_match:
        info["github"] = github_match.group(0)

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if lines:
        for line in lines[:3]:
            lower_line = line.lower()
            if (info["email"] and info["email"] in line) or (info["phone"] and info["phone"] in line):
                continue
            if "github.com" in lower_line or "linkedin.com" in lower_line or "resume" in lower_line or "curriculum" in lower_line:
                continue
            words = line.split()
            if 1 < len(words) <= 5 and any(w[0].isupper() for w in words if w.isalpha()):
                info["name"] = line
                break
        
        if not info["name"]:
            if len(lines[0]) < 30 and not any(k in lines[0].lower() for k in ["email", "phone", "@"]):
                info["name"] = lines[0]
            else:
                info["name"] = "Candidate Name"

    return info

def parse_resume_sections(text: str) -> Dict[str, List[str]]:
    """Partitions the resume into potential sections based on common headings."""
    sections = {
        "education": [],
        "skills": [],
        "experience": [],
        "projects": [],
        "certificates": [],
        "languages": [],
        "achievements": []
    }
    
    patterns = {
        "education": [r'\beducation\b', r'\bacademics\b', r'\bacacademic background\b', r'\bstudy history\b'],
        "skills": [r'\bskills\b', r'\btechnical skills\b', r'\btechnologies\b', r'\bcore competencies\b', r'\bexpertise\b'],
        "experience": [r'\bexperience\b', r'\bwork experience\b', r'\bemployment history\b', r'\bprofessional experience\b', r'\bwork history\b'],
        "projects": [r'\bprojects\b', r'\bpersonal projects\b', r'\bacademics projects\b', r'\bkey projects\b'],
        "certificates": [r'\bcertificates\b', r'\bcertifications\b', r'\blicenses\b', r'\bcoursework\b'],
        "languages": [r'\blanguages\b', r'\blanguage proficiency\b'],
        "achievements": [r'\bachievements\b', r'\bhonors\b', r'\bawards\b', r'\baccolades\b', r'\bpublications\b']
    }

    lines = text.split('\n')
    current_section = None
    
    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line:
            continue

        header_found = False
        for sec_name, sec_patterns in patterns.items():
            for pat in sec_patterns:
                if re.search(pat, cleaned_line.lower()):
                    if len(cleaned_line) < 30:
                        current_section = sec_name
                        header_found = True
                        break
            if header_found:
                break
        
        if header_found:
            continue
            
        if current_section:
            sections[current_section].append(cleaned_line)

    return sections

def parse_resume(pdf_path: str) -> Dict[str, Any]:
    """Full parser function combining text extraction and data structure parsing."""
    text = extract_text_from_pdf(pdf_path)
    contact_info = parse_contact_info(text)
    sections = parse_resume_sections(text)
    
    return {
        "text": text,
        "contact_info": contact_info,
        "sections": {k: "\n".join(v) for k, v in sections.items()}
    }


# ==========================================================================
# 2. REPORTLAB PDF REPORT GENERATOR
# ==========================================================================
class NumberedCanvas(canvas.Canvas):
    """Canvas implementation for adding page numbers dynamically."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#A0AEC0"))
        
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 40, letter[0] - 54, 40)
        
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 54, 25, footer_text)
        self.drawString(54, 25, f"AI Resume Analyzer - Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.restoreState()

def generate_pdf_report(report: Dict[str, Any], output_path: str) -> None:
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=60
    )

    styles = getSampleStyleSheet()
    
    c_primary = colors.HexColor("#1A202C")
    c_accent = colors.HexColor("#3182CE")
    c_success = colors.HexColor("#38A169")
    c_warning = colors.HexColor("#DD6B20")
    c_text = colors.HexColor("#2D3748")
    c_light = colors.HexColor("#F7FAFC")
    
    style_normal = ParagraphStyle(
        'ReportNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=c_text
    )
    
    style_title = ParagraphStyle(
        'ReportTitle',
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=c_primary,
        spaceAfter=15
    )

    style_subtitle = ParagraphStyle(
        'ReportSubtitle',
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#718096"),
        spaceAfter=25
    )
    
    style_h1 = ParagraphStyle(
        'ReportH1',
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=c_primary,
        spaceBefore=15,
        spaceAfter=8,
        keepWithNext=True
    )

    style_h2 = ParagraphStyle(
        'ReportH2',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=c_accent,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )
    
    style_bullet = ParagraphStyle(
        'ReportBullet',
        parent=style_normal,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=5
    )

    story = []

    story.append(Paragraph("AI Resume Analyzer", style_title))
    story.append(Paragraph(f"Comprehensive ATS Audit & Optimization Report • {datetime.now().strftime('%B %d, %Y')}", style_subtitle))
    
    contact = report.get("contact_info", {})
    name = contact.get("name", "Candidate")
    email = contact.get("email", "N/A")
    phone = contact.get("phone", "N/A")
    linkedin = contact.get("linkedin", "N/A")
    github = contact.get("github", "N/A")
    
    info_html = f"<b>Candidate:</b> {name} | <b>Email:</b> {email} | <b>Phone:</b> {phone}<br/>"
    socials = []
    if linkedin and linkedin != "N/A":
        socials.append(f"<b>LinkedIn:</b> {linkedin}")
    if github and github != "N/A":
        socials.append(f"<b>GitHub:</b> {github}")
    if socials:
        info_html += " | ".join(socials)
        
    info_p = Paragraph(info_html, ParagraphStyle('InfoStyle', parent=style_normal, fontSize=9, leading=12))
    info_table = Table([[info_p]], colWidths=[letter[0] - 108])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_light),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 15))

    ats_score = report.get("ats_score", 0)
    readability = report.get("readability_score", 0)
    interview_prob = report.get("interview_probability", 0)
    
    score_color = c_success if ats_score >= 80 else (c_warning if ats_score >= 50 else colors.HexColor("#E53E3E"))
    
    score_p = Paragraph(f"<font size=32 color='{score_color}'><b>{ats_score}%</b></font><br/><font size=9 color='#718096'>ATS MATCH SCORE</font>", ParagraphStyle('ScoreP', alignment=TA_CENTER, leading=20))
    read_p = Paragraph(f"<font size=20 color='#3182CE'><b>{readability}%</b></font><br/><font size=9 color='#718096'>READABILITY SCORE</font>", ParagraphStyle('ReadP', alignment=TA_CENTER, leading=16))
    prob_p = Paragraph(f"<font size=20 color='#3182CE'><b>{interview_prob}%</b></font><br/><font size=9 color='#718096'>INTERVIEW PROBABILITY</font>", ParagraphStyle('ProbP', alignment=TA_CENTER, leading=16))
    
    metrics_table = Table([[score_p, read_p, prob_p]], colWidths=[(letter[0] - 108)/3]*3)
    metrics_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('BACKGROUND', (0,0), (-1,-1), c_light),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 15))

    story.append(Paragraph("Professional Summary", style_h1))
    summary_p = Paragraph(report.get("summary", "No summary provided."), style_normal)
    story.append(summary_p)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Lexical Strengths & Weaknesses", style_h1))
    
    strengths_html = "<br/>".join([f"• {s}" for s in report.get("strengths", [])])
    weaknesses_html = "<br/>".join([f"• {w}" for w in report.get("weaknesses", [])])
    
    strengths_p = Paragraph(f"<b>Key Strengths:</b><br/>{strengths_html}", style_normal)
    weaknesses_p = Paragraph(f"<b>Areas for Improvement:</b><br/>{weaknesses_html}", style_normal)
    
    sw_table = Table([[strengths_p, weaknesses_p]], colWidths=[(letter[0]-118)/2, (letter[0]-118)/2])
    sw_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (0,0), colors.HexColor("#F0FFF4")),
        ('BACKGROUND', (1,0), (1,0), colors.HexColor("#FFF5F5")),
        ('BOX', (0,0), (0,0), 0.5, colors.HexColor("#C6F6D5")),
        ('BOX', (1,0), (1,0), 0.5, colors.HexColor("#FED7D7")),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(sw_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("ATS Keyword & Grammar Optimization", style_h1))
    
    keywords_list = report.get("missing_keywords", [])
    keywords_html = ", ".join(keywords_list) if keywords_list else "None identified (Excellent keyword coverage!)."
    keywords_p = Paragraph(f"<b>Missing/Recommended Keywords:</b><br/>{keywords_html}", style_normal)
    
    grammar_list = report.get("grammar", [])
    grammar_html = "<br/>".join([f"• {g}" for g in grammar_list]) if grammar_list else "No spelling or grammatical issues detected."
    grammar_p = Paragraph(f"<b>Grammar, Style & Action Verb Suggestions:</b><br/>{grammar_html}", style_normal)
    
    opt_table = Table([[keywords_p], [grammar_p]], colWidths=[letter[0] - 108])
    opt_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), c_light),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(opt_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Actionable Recommendations", style_h1))
    for rec in report.get("recommendations", []):
        story.append(Paragraph(f"• {rec}", style_bullet))
        
    story.append(Spacer(1, 10))
    story.append(Paragraph("Formatting & Structural Guidelines", style_h2))
    for fmt in report.get("formatting_suggestions", []):
        story.append(Paragraph(f"• {fmt}", style_bullet))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Career Development & Progression Plan", style_h2))
    for car in report.get("career_suggestions", []):
        story.append(Paragraph(f"• {car}", style_bullet))

    story.append(Spacer(1, 15))
    story.append(Paragraph("Interview Readiness & Target Strategy", style_h1))
    story.append(Paragraph(report.get("interview_readiness", "No interview preparation info available."), style_normal))

    doc.build(story, canvasmaker=NumberedCanvas)

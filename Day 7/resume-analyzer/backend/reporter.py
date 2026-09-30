import os
from datetime import datetime
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas


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
        
        # Draw header rule and text on all pages except the first if desired, or all
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 40, letter[0] - 54, 40)
        
        # Footer text
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 54, 25, footer_text)
        self.drawString(54, 25, f"AI Resume Analyzer - Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.restoreState()

def generate_pdf_report(report: Dict[str, Any], output_path: str) -> None:
    # Setup document
    # Left, right margins: 54pt (0.75in), top, bottom: 54pt
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=60
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_primary = colors.HexColor("#1A202C")   # Slate Black
    c_accent = colors.HexColor("#3182CE")    # Blue
    c_success = colors.HexColor("#38A169")   # Green
    c_warning = colors.HexColor("#DD6B20")   # Orange
    c_text = colors.HexColor("#2D3748")      # Dark Grey
    c_light = colors.HexColor("#F7FAFC")     # Light Grey
    
    # Modify existing styles or define unique custom ones
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

    # Title & Subtitle Header
    story.append(Paragraph("AI Resume Analyzer", style_title))
    story.append(Paragraph(f"Comprehensive ATS Audit & Optimization Report • {datetime.now().strftime('%B %d, %Y')}", style_subtitle))
    
    # Candidate Info Banner
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

    # Score Metrics Table
    ats_score = report.get("ats_score", 0)
    readability = report.get("readability_score", 0)
    interview_prob = report.get("interview_probability", 0)
    
    # Define score colors
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

    # Professional Summary
    story.append(Paragraph("Professional Summary", style_h1))
    summary_p = Paragraph(report.get("summary", "No summary provided."), style_normal)
    story.append(summary_p)
    story.append(Spacer(1, 12))

    # Strengths and Weaknesses (Side-by-Side)
    story.append(Paragraph("Lexical Strengths & Weaknesses", style_h1))
    
    strengths_html = "<br/>".join([f"• {s}" for s in report.get("strengths", [])])
    weaknesses_html = "<br/>".join([f"• {w}" for w in report.get("weaknesses", [])])
    
    strengths_p = Paragraph(f"<b>Key Strengths:</b><br/>{strengths_html}", style_normal)
    weaknesses_p = Paragraph(f"<b>Areas for Improvement:</b><br/>{weaknesses_html}", style_normal)
    
    sw_table = Table([[strengths_p, weaknesses_p]], colWidths=[(letter[0]-118)/2, (letter[0]-118)/2])
    sw_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (0,0), colors.HexColor("#F0FFF4")), # Light green
        ('BACKGROUND', (1,0), (1,0), colors.HexColor("#FFF5F5")), # Light red
        ('BOX', (0,0), (0,0), 0.5, colors.HexColor("#C6F6D5")),
        ('BOX', (1,0), (1,0), 0.5, colors.HexColor("#FED7D7")),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(sw_table)
    story.append(Spacer(1, 12))

    # Missing Keywords & Grammar (Force PageBreak if needed, reportlab handles flow automatically,
    # but we can let it pagebreak naturally. We'll add a clean header)
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

    # Recommendations & Suggestions
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

    # Build the document
    from reportlab.pdfgen import canvas
    doc.build(story, canvasmaker=NumberedCanvas)

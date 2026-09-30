import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def create_resume():
    pdf_path = os.path.join(os.path.dirname(__file__), "test_resume.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, leftMargin=72, rightMargin=72, topMargin=72, bottomMargin=72)
    story = []
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'NameStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        spaceAfter=12
    )

    story.append(Paragraph("John Doe", title_style))
    story.append(Paragraph("Email: john.doe@email.com | Phone: +1-555-0199 | GitHub: github.com/johndoe | LinkedIn: linkedin.com/in/johndoe", body_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("<b>Professional Summary</b>", styles['Heading2']))
    story.append(Paragraph("Experienced Software Engineer with a solid background in designing, developing, and deploying scalable web services. Passionate about automated testing and system optimization.", body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Experience</b>", styles['Heading2']))
    story.append(Paragraph("<b>Senior Python Engineer</b> at TechSolutions Inc (2022 - Present)<br/>"
                           "- Built backend web services using FastAPI and PostgreSQL, improving API latency by 25%.<br/>"
                           "- Mentored junior devs and orchestrated migration from legacy systems to containerized microservices.<br/>"
                           "- Maintained CI/CD pipelines using GitHub Actions.", body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Skills</b>", styles['Heading2']))
    story.append(Paragraph("Python, FastAPI, Docker, PostgreSQL, JavaScript, React, CI/CD, Git, System Design", body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Education</b>", styles['Heading2']))
    story.append(Paragraph("<b>B.S. in Computer Science</b> - State University (2018 - 2022)", body_style))
    
    doc.build(story)
    print(f"Generated test resume at: {pdf_path}")

if __name__ == "__main__":
    create_resume()

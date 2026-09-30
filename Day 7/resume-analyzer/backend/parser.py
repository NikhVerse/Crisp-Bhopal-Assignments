import re
import os
import fitz  # PyMuPDF
import pdfplumber
from typing import Dict, Any, List

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts raw text from a PDF file using PyMuPDF with a fallback to pdfplumber."""
    text = ""
    # Try PyMuPDF
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception as e:
        print(f"PyMuPDF extraction failed: {e}")
        text = ""

    # Fallback to pdfplumber if text is empty or too short
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
    
    # 1. Email Extraction
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if email_match:
        info["email"] = email_match.group(0)

    # 2. Phone Extraction
    # Matches +1-123-456-7890, (123) 456-7890, 123-456-7890, 1234567890, etc.
    phone_match = re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    if phone_match:
        info["phone"] = phone_match.group(0)

    # 3. LinkedIn Extraction
    linkedin_match = re.search(r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-]+/?', text, re.IGNORECASE)
    if linkedin_match:
        info["linkedin"] = linkedin_match.group(0)

    # 4. GitHub Extraction
    github_match = re.search(r'(?:https?://)?(?:www\.)?github\.com/[\w\-]+/?', text, re.IGNORECASE)
    if github_match:
        info["github"] = github_match.group(0)

    # 5. Name Heuristics
    # Typically, the name is on the first line or first 3 lines of the document,
    # before any emails, phones, or links. Let's filter out common noise.
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if lines:
        for line in lines[:3]:
            # Clean up the line
            # If line doesn't contain email, phone, github, linkedin, or generic keywords
            lower_line = line.lower()
            if (info["email"] and info["email"] in line) or (info["phone"] and info["phone"] in line):
                continue
            if "github.com" in lower_line or "linkedin.com" in lower_line or "resume" in lower_line or "curriculum" in lower_line:
                continue
            # Basic validation: length check and typical capitalized format
            words = line.split()
            if 1 < len(words) <= 5 and any(w[0].isupper() for w in words if w.isalpha()):
                info["name"] = line
                break
        
        # Fallback if no name found
        if not info["name"]:
            # Check the very first line if it's reasonable length
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
    
    # Define common header patterns for each section
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

        # Check if line matches any section headers
        header_found = False
        for sec_name, sec_patterns in patterns.items():
            for pat in sec_patterns:
                if re.search(pat, cleaned_line.lower()):
                    # To prevent matching longer sentences containing the word, check header length
                    if len(cleaned_line) < 30:
                        current_section = sec_name
                        header_found = True
                        break
            if header_found:
                break
        
        if header_found:
            continue
            
        # Add line to current section
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

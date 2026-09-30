import os
import json
from typing import Dict, Any
from backend.parser import parse_resume
from backend.grok import analyze_resume_text_with_grok

class ResumeAnalyzer:
    @staticmethod
    def get_fallback_analysis(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a comprehensive fallback mock report if Grok API is unavailable
        or if the API key is missing. This allows local visual testing of the UI.
        """
        contact = parsed_data.get("contact_info", {})
        candidate_name = contact.get("name", "Candidate")
        
        # Simple local analysis of sections
        sections = parsed_data.get("sections", {})
        skills_text = sections.get("skills", "")
        exp_text = sections.get("experience", "")
        
        skills_found = [s.strip() for s in skills_text.split(',') if s.strip()]
        if not skills_found:
            skills_found = [s.strip() for s in skills_text.split('\n') if s.strip()]
        if not skills_found:
            skills_found = ["General Professional Skills", "Communication", "Problem Solving"]
            
        skills_heatmap = []
        for i, skill in enumerate(skills_found[:10]):
            freq = 1 + (i % 3)
            importance = "High" if i % 2 == 0 else "Medium"
            skills_heatmap.append({
                "keyword": skill[:30],
                "frequency": freq,
                "importance": importance
            })
            
        return {
            "ats_score": 65,
            "summary": (
                f"NOTICE: This is a fallback local analysis because GROK_API_KEY is not configured or failed to connect. "
                f"Extracted resume for {candidate_name}. Heuristics suggest base formatting is present, but AI analysis is required "
                f"to perform full optimization check."
            ),
            "strengths": [
                "Extracted contact details successfully: Name, Email, and Social links.",
                "Sections identified: " + ", ".join([k.capitalize() for k, v in sections.items() if v]),
                "Skills found in resume text: " + ", ".join(skills_found[:5])
            ],
            "weaknesses": [
                "Grok API not connected: Deep lexical and ATS grammar analysis could not run.",
                "Job-readiness and keywords optimization could not be evaluated by AI.",
                "Quantitative achievements could not be validated."
            ],
            "missing_keywords": ["ATS Optimization", "Action Verbs", "Quantified Achievements"],
            "grammar": ["Ensure all work descriptions start with strong action verbs.", "Use standard bullet format."],
            "recommendations": [
                "Set the GROK_API_KEY environment variable in your backend to enable high-accuracy AI analyses.",
                "Ensure your work experiences list specific metrics and outcomes (e.g., 'increased efficiency by 20%')."
            ],
            "formatting_suggestions": [
                "Use standard margins (1 inch) and system fonts (Calibri, Arial, Helvetica).",
                "Ensure no contact details or important skills are in PDF page headers or footers, as ATS parsers sometimes ignore them."
            ],
            "career_suggestions": [
                "Add certification timelines to validate relevant professional courses.",
                "Tailor resume keywords directly to your target job descriptions."
            ],
            "interview_readiness": "Limited local analysis. Standard formatting indicates typical entry-level readiness.",
            "skills_heatmap": skills_heatmap[:8],
            "readability_score": 75,
            "interview_probability": 45,
            "improvement_checklist": [
                {"item": "Configure GROK_API_KEY environment variable", "status": "pending"},
                {"item": "Ensure Name and Email are parsed correctly", "status": "completed"},
                {"item": "Identify work experiences and date formats", "status": "completed"},
                {"item": "Add missing key technical keywords", "status": "pending"}
            ]
        }

    async def analyze(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extracts text from PDF, parses structure, and executes AI analysis using Grok API.
        If Grok is not configured or errors out, falls back to a descriptive local report.
        """
        # 1. Parse the PDF
        parsed_data = parse_resume(pdf_path)
        
        # 2. Get AI Analysis
        try:
            # Check if key is available
            api_key = os.getenv("GROK_API_KEY", "")
            if not api_key:
                print("Warning: GROK_API_KEY not found. Using fallback local analysis.")
                report = self.get_fallback_analysis(parsed_data)
                report["is_fallback"] = True
            else:
                report = await analyze_resume_text_with_grok(parsed_data["text"], parsed_data["contact_info"])
                report["is_fallback"] = False
        except Exception as e:
            print(f"Error during Grok Analysis: {e}. Falling back to local analysis.")
            report = self.get_fallback_analysis(parsed_data)
            report["is_fallback"] = True
            report["error_detail"] = str(e)
            
        # Combine parsed contact details and sections with the report
        report["contact_info"] = parsed_data["contact_info"]
        
        # Add basic metadata
        report["file_name"] = os.path.basename(pdf_path)
        
        return report

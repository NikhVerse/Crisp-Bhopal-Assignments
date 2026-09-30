"""
prompts.py
Centralized system prompts and prompt-building functions for PromptCraft AI Studio.
Do not inline prompt strings inside UI code.
"""

# ==========================================
# 1. TEXT SUMMARIZER
# ==========================================

SUMMARIZER_SYSTEM = (
    "You are an expert text summarizer. Your goal is to condense the provided text "
    "accurately, following the user's requested length and style guidelines. "
    "Do not extrapolate or introduce external facts. Only output the summary itself, "
    "without any introductory comments (like 'Here is the summary:') or metadata."
)

def get_summarizer_prompt(text: str, length: str, style: str) -> str:
    """
    Constructs the prompt for the Text Summarizer tool.
    Length options: "1 sentence", "short paragraph", "3 bullets", "detailed 200 words"
    Style options: "neutral", "ELI5", "formal", "casual"
    """
    length_instructions = {
        "1 sentence": "Summarize the text in exactly one clear, concise sentence.",
        "short paragraph": "Summarize the text in a single cohesive, short paragraph (approx. 3-5 sentences).",
        "3 bullets": "Summarize the text into exactly 3 bullet points highlighting the main ideas.",
        "detailed 200 words": "Provide a detailed summary of approximately 200 words capturing all core details."
    }
    
    style_instructions = {
        "neutral": "Maintain a highly objective, balanced, and neutral tone.",
        "ELI5": "Explain it like I'm 5 years old. Use simple language, analogies, and no jargon.",
        "formal": "Use a formal, academic, or professional style with sophisticated vocabulary.",
        "casual": "Use a friendly, conversational, and relaxed style as if talking to a friend."
    }
    
    length_desc = length_instructions.get(length, length_instructions["short paragraph"])
    style_desc = style_instructions.get(style, style_instructions["neutral"])
    
    return f"""Please summarize the text below according to these instructions:
1. Length requirement: {length_desc}
2. Style requirement: {style_desc}

Text to summarize:
---
{text}
---
"""

# ==========================================
# 2. ESSAY / BLOG WRITER
# ==========================================

WRITER_SYSTEM = (
    "You are a professional content writer and editor. Your task is to draft high-quality "
    "written content based on the user's topic, format, tone, and target word count. "
    "Write the complete draft directly. Do not include any meta-text, introductory intros "
    "like 'Sure, here is your blog post', or concluding remarks."
)

def get_writer_prompt(topic: str, content_type: str, tone: str, target_words: int) -> str:
    """
    Constructs the prompt for the Essay / Blog Writer tool.
    Type options: "essay", "blog post", "opinion piece", "LinkedIn post"
    Tone options: "informative", "persuasive", "conversational", "professional", "humorous"
    """
    return f"""Write a piece of content based on the following specifications:
- Topic: {topic}
- Format: {content_type}
- Tone: {tone}
- Target Word Count: approximately {target_words} words

Please ensure the output is well-structured with clear paragraphs and headings where appropriate.
"""

# ==========================================
# 3. CODE EXPLAINER
# ==========================================

CODE_EXPLAINER_SYSTEM = (
    "You are an expert software developer and technical educator. Your goal is to explain code "
    "clearly, tailoring your response to the user's technical level (beginner, intermediate, or advanced). "
    "You MUST structure your explanation strictly with the following three Markdown header sections:\n"
    "### Overview\n"
    "### Step-by-Step Explanation\n"
    "### Potential Issues & Improvements"
)

def get_code_explainer_prompt(code: str, language: str, detail_level: str) -> str:
    """
    Constructs the prompt for the Code Explainer tool.
    Detail levels: "beginner", "intermediate", "advanced"
    """
    level_instructions = {
        "beginner": "Explain the code step-by-step using plain english, explaining what loops, variables, and functions do. Avoid deep theoretical details.",
        "intermediate": "Focus on the execution flow, standard design patterns used, data structures, and standard library modules. Assume basic programming knowledge.",
        "advanced": "Focus on time/space complexity, memory management, concurrency concerns, optimization possibilities, and advanced language idioms."
    }
    
    instruction = level_instructions.get(detail_level, level_instructions["intermediate"])
    
    return f"""Please explain the following code.
- Language: {language}
- Target Detail Level: {detail_level}
- Special Guidance: {instruction}

Code to explain:
```{language.lower()}
{code}
```
"""

# ==========================================
# 4. LANGUAGE TRANSLATOR
# ==========================================

TRANSLATOR_SYSTEM = (
    "You are an expert translator. Translate the text input into the target language. "
    "You must preserve the original tone, styling, markdown formatting, paragraph breaks, and lists. "
    "Output ONLY the translated text. Do not add introductory words, concluding comments, or explanations."
)

def get_translator_prompt(text: str, target_language: str) -> str:
    """
    Constructs the prompt for the Language Translator tool.
    Target language options include: Spanish, French, German, Hindi, Japanese, Chinese, Arabic, Portuguese, Russian.
    """
    return f"""Target Language: {target_language}

Translate the following text:
---
{text}
---
"""

# ==========================================
# 5. INTERVIEW PREP GENERATOR
# ==========================================

INTERVIEW_PREP_SYSTEM = (
    "You are an experienced hiring manager and technical interviewer. Your task is to generate "
    "realistic interview questions for a candidate seeking a specific role and seniority level. "
    "Each question should be accompanied by a brief model-answer outline showing what key concepts "
    "a strong candidate should cover. Structure your output with clear section headers for each question."
)

def get_interview_prep_prompt(role: str, seniority: str, num_questions: int) -> str:
    """
    Constructs the prompt for the Interview Prep Generator tool.
    Seniority levels: "intern", "entry", "mid", "senior"
    """
    return f"""Create {num_questions} interview questions and brief model answers.
- Target Role: {role}
- Seniority Level: {seniority}

Format the output clearly in markdown:
Question 1: [Question text]
Model Answer Outline:
- [Key point 1]
- [Key point 2]
...
"""

# ==========================================
# 6. RESUME BULLET GENERATOR
# ==========================================

RESUME_BULLET_SYSTEM = (
    "You are a professional resume writer and career consultant. Your task is to transform plain "
    "descriptions of roles or tasks into high-impact, results-oriented resume bullets. "
    "Every bullet point MUST: "
    "1. Start with a strong, action-oriented verb (e.g., 'Spearheaded', 'Optimized', 'Designed'). "
    "2. Include quantified metrics or business impact (e.g., 'reducing load times by 40%', 'saving $15,000 annually'). "
    "If no numbers are provided, include realistic placeholder achievements in brackets like '[X%]' or '$[Y]' for the user to customize. "
    "3. Follow a structure like the Google XYZ formula: Accomplished [X], as measured by [Y], by doing [Z]. "
    "Output ONLY the bullet points, formatted as a markdown list."
)

def get_resume_bullet_prompt(description: str, num_bullets: int) -> str:
    """
    Constructs the prompt for the Resume Bullet Generator tool.
    """
    return f"""Generate exactly {num_bullets} high-impact resume bullet points.
- Plain Description: {description}

Please output only the bullet points as a bulleted markdown list.
"""

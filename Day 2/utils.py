"""
utils.py
Unified LLM calling logic for Groq and OpenAI APIs using the OpenAI SDK.
Includes latency tracking and mock response generation for local testing.
"""

import os
import time
from typing import Tuple
from dotenv import load_dotenv
from openai import OpenAI

# Load local environment variables if present
load_dotenv()

def get_default_api_key(provider: str) -> str:
    """Gets default API key from environment variables if set."""
    # Force reload environment variables from .env in case user updated it
    load_dotenv(override=True)
    if provider.lower() == "groq":
        return os.environ.get("GROQ_API_KEY", "")
    elif provider.lower() == "openai":
        return os.environ.get("OPENAI_API_KEY", "")
    return ""

def generate_mock_response(system_prompt: str, user_prompt: str) -> str:
    """Generates realistic responses for each tool when Mock Mode is active."""
    # Check Text Summarizer
    if "summarize" in system_prompt.lower() or "summarize" in user_prompt.lower():
        if "1 sentence" in user_prompt.lower():
            return "This text outlines the primary features of the target application, emphasizing its minimal design, multi-tool composition, and unified API capabilities."
        elif "3 bullets" in user_prompt.lower():
            return (
                "- **PromptCraft AI Studio** is a minimal, whitespace-driven multi-tool LLM wrapper application.\n"
                "- It includes six functional tabs for text, code, translation, writing, and professional content creation.\n"
                "- The architecture separates prompts, utility logic, and interface styling for robust design control."
            )
        elif "200 words" in user_prompt.lower():
            return (
                "The document details PromptCraft AI Studio, an elegant and restrained design-oriented Streamlit application. "
                "The application houses six key AI-driven utilities: a text summarizer, an essay/blog writer, a code explainer, "
                "a language translator, an interview preparation generator, and a resume bullet generator. Centralizing all "
                "prompts in a distinct prompts module, it prevents prompt contamination of the UI layer. Furthermore, "
                "the application relies on standard OpenAI client integrations for both Groq and OpenAI providers, supporting "
                "session-only API key parameters, response latency display, and query history storage. "
                "The interface layout enforces strict minimalist design parameters: using deep charcoal accents, clean hairline "
                "borders, and generous white space. By rejecting complex shadows and loud colored card grids, it achieves an "
                "editorial, Notion-like user experience that is visually quiet yet highly functional."
            )
        else:
            return (
                "PromptCraft AI Studio is a clean, multi-tool platform built with Streamlit. "
                "It serves six utility tools powered by Groq and OpenAI LLMs using structured prompts. "
                "The tool has a quiet, minimal design aesthetic focusing on typography and generous whitespace."
            )

    # Check Essay / Blog Writer
    elif "content writer" in system_prompt.lower() or "write a piece" in user_prompt.lower():
        topic = "the topic"
        for line in user_prompt.split("\n"):
            if "topic:" in line.lower():
                topic = line.split(":", 1)[1].strip()
        
        return (
            f"# Reflections on {topic}\n\n"
            f"Writing about {topic} reveals how rapidly modern systems are evolving. "
            "In today's landscape, clarity and structure represent the thin boundary between success and complexity. "
            "When we break down complex architectures, we discover that simple, modular parts form the strongest foundations.\n\n"
            "## Key Perspectives\n"
            "First, aesthetics and usability must go hand-in-hand. An interface that is cluttered or visually loud "
            "detracts from the user's focus, while an editorial-style design promotes calm concentration. "
            "Second, performance metrics like request latency should be treated as core attributes rather than afterthought diagnostics.\n\n"
            "Ultimately, whether we look at clean code paradigms or minimalist interfaces, the message remains clear: "
            "simplicity is the ultimate sophistication."
        )

    # Check Code Explainer
    elif "explain code" in system_prompt.lower() or "explain this code" in user_prompt.lower():
        return (
            "### Overview\n"
            "This script is a modular utility designed to process data collections. It uses a decorator-based helper "
            "to measure function execution time and records performance metrics for subsequent audit runs.\n\n"
            "### Step-by-Step Explanation\n"
            "1. **Decorator Definition (`@measure_time`)**: Wraps target functions to record the start time, executes the logic, "
            "calculates total latency, and prints the result to standard output.\n"
            "2. **Data Streaming Loop**: The core function uses a generator expression to yield transformed chunks of data, "
            "minimizing memory footprint when loading large sequences.\n"
            "3. **Exception Handler**: Encloses all network read calls inside a try-except block to gracefully catch timeout limits "
            "and retry operations up to three times.\n\n"
            "### Potential Issues & Improvements\n"
            "- **Issue**: Hardcoded retry count (3) in the read operation.\n"
            "  *Improvement*: Expose this parameter as a function default argument to improve testability.\n"
            "- **Issue**: Standard print output might get lost in containerized log aggregators.\n"
            "  *Improvement*: Replace `print()` statements with standard Python logging modules (`logging.info`)."
        )

    # Check Language Translator
    elif "translator" in system_prompt.lower() or "translate" in user_prompt.lower():
        target_lang = "Spanish"
        for line in user_prompt.split("\n"):
            if "language:" in line.lower():
                target_lang = line.split(":", 1)[1].strip()
        
        translations = {
            "spanish": "Esta es una traducción simulada. El sistema está funcionando de forma correcta y visualizando el texto traducido con elegancia.",
            "french": "Ceci est une traduction simulée. Le système fonctionne correctement et affiche le texte traduit avec élégance.",
            "german": "Dies ist eine simulierte Übersetzung. Das System funktioniert einwandfrei und zeigt den übersetzten Text elegant an.",
            "hindi": "यह एक सिम्युलेटेड अनुवाद है। सिस्टम सही ढंग से काम कर रहा है और अनुवादित पाठ को सुरुचिपूर्ण ढंग से प्रदर्शित कर रहा है।",
            "japanese": "これはシミュレートされた翻訳です。システムは正常に動作しており、翻訳されたテキストをエレガントに表示しています。",
            "chinese": "这是模拟翻译。系统工作正常，正在优雅地显示翻译后的文本。",
            "arabic": "هذه ترجمة محاكاة. يعمل النظام بشكل صحيح ويعرض النص المترجم بأناقة.",
            "portuguese": "Esta é uma tradução simulada. O sistema está funcionando corretamente e exibindo o texto traduzido com elegância.",
            "russian": "Это симулированный перевод. Система работает корректно и элегантно отображает переведенный текст."
        }
        return translations.get(target_lang.lower(), f"[Mock Translation to {target_lang}]: This is a simulated translation of the input text.")

    # Check Interview Prep Generator
    elif "interview questions" in system_prompt.lower() or "interview prep" in user_prompt.lower():
        role = "Software Engineer"
        for line in user_prompt.split("\n"):
            if "role:" in line.lower():
                role = line.split(":", 1)[1].strip()
                
        return (
            f"### Interview Preparation for {role}\n\n"
            "Question 1: Explain the difference between optimistic and pessimistic locking patterns, and when you would use each.\n"
            "Model Answer Outline:\n"
            "- Definition: Optimistic locking assumes collision is rare and checks on write; pessimistic locking blocks other threads proactively.\n"
            "- Use Case: Optimistic is preferred for high-read, low-write volume to avoid deadlocks; pessimistic is for highly contentions transactions.\n\n"
            "Question 2: How do you handle error states and transient API failures in distributed applications?\n"
            "Model Answer Outline:\n"
            "- Implement exponential backoff retry policies with randomized jitter.\n"
            "- Introduce circuit breakers to stop cascading failures to dependent services."
        )

    # Check Resume Bullet Generator
    elif "resume writer" in system_prompt.lower() or "resume bullet" in user_prompt.lower():
        return (
            "- Spearheaded database migration for legacy analytics dashboards, **reducing query latency by 45%** and saving $[12,000] in yearly server overhead.\n"
            "- Designed and integrated a unified logging decorator system across [8] key microservices, **improving error diagnosis time by 30%**.\n"
            "- Collaborated with cross-functional teams to prototype a real-time reporting console, **increasing user session retention by [18%]**."
        )
        
    return "This is a simulated model output from Mock Mode. Please enter a valid API key to test live completions."

def call_llm(
    provider: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    api_key: str = "",
    temperature: float = 0.7,
    max_tokens: int = 1024
) -> Tuple[str, float]:
    """
    Calls the specified LLM provider (Groq or OpenAI) using the OpenAI SDK.
    Returns a tuple of (response_text, response_latency_seconds).
    
    If api_key == "mock", runs in simulated mode with realistic response content.
    """
    start_time = time.time()
    
    # Check if API Key is empty and try to fetch from env
    resolved_key = api_key.strip() if api_key else ""
    if not resolved_key:
        resolved_key = get_default_api_key(provider)
        
    # Check if we should use mock mode
    is_mock = resolved_key.lower() == "mock" or not resolved_key
    
    if is_mock:
        time.sleep(0.65)  # Simulate API latency
        mock_response = generate_mock_response(system_prompt, user_prompt)
        latency = time.time() - start_time
        return mock_response, latency
        
    try:
        if provider.lower() == "groq":
            client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=resolved_key
            )
        else:  # openai
            client = OpenAI(
                api_key=resolved_key
            )
            
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        content = chat_completion.choices[0].message.content
        latency = time.time() - start_time
        return content or "", latency
        
    except Exception as e:
        latency = time.time() - start_time
        error_msg = f"API Error ({provider.upper()}): {str(e)}"
        return error_msg, latency

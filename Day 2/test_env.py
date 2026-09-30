import os
from dotenv import load_dotenv

print("--- Initial Load ---")
load_dotenv()
print("GROQ_API_KEY from env:", os.environ.get("GROQ_API_KEY"))
print("OPENAI_API_KEY from env:", os.environ.get("OPENAI_API_KEY"))

print("\n--- Override Load ---")
load_dotenv(override=True)
print("GROQ_API_KEY from env (override):", os.environ.get("GROQ_API_KEY"))
print("OPENAI_API_KEY from env (override):", os.environ.get("OPENAI_API_KEY"))

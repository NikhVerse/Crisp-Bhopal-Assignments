import os
import json
import asyncio
import httpx
from dotenv import load_dotenv

# Load local environment variables
load_dotenv()

async def test_connection():
    api_key = os.getenv("GROK_API_KEY", "").strip()
    
    print("=" * 60)
    print("CVGROK ENVIRONMENT VARIABLES VALIDATION")
    print("=" * 60)
    
    if not api_key:
        print("[ERROR] GROK_API_KEY not found in environment variables.")
        print("Please check your .env file in the workspace directory.")
        return
        
    # Mask key for log security
    prefix = api_key[:4]
    suffix = api_key[-4:] if len(api_key) > 8 else ""
    masked_key = f"{prefix}...{suffix} (Length: {len(api_key)})"
    print(f"[OK] Found GROK_API_KEY: {masked_key}")
    
    # Provider detection
    if api_key.startswith("gsk_"):
        api_url = "https://api.groq.com/openai/v1/chat/completions"
        model = os.getenv("GROK_MODEL", "llama-3.3-70b-versatile")
        provider = "Groq"
    else:
        api_url = "https://api.x.ai/v1/chat/completions"
        model = os.getenv("GROK_MODEL", "grok-2-1212")
        provider = "xAI Grok"
        
    print(f"Detected Provider: {provider}")
    print(f"Configured Model: {model}")
    print(f"Target Endpoint: {api_url}")
    print("-" * 60)
    print("Initiating test query...")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Respond with the word 'ACKNOWLEDGE'"}
        ],
        "temperature": 0.1
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(api_url, headers=headers, json=payload)
            response_json = response.json()
            
            if response.status_code == 200:
                answer = response_json["choices"][0]["message"]["content"].strip()
                print(f"[SUCCESS] Connection verified.")
                print(f"Model Response: '{answer}'")
            else:
                print(f"[FAILED] Connection Failed (HTTP {response.status_code})")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"[ERROR] Request Error: {str(e)}")
            
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_connection())

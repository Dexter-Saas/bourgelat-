from dotenv import load_dotenv
load_dotenv()
import base64
import httpx
import os
import json

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "google/gemma-4-31b-it:free")
API_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """You are Bourgelat, an expert veterinary AI assistant specializing in cattle health.
Analyze the provided image and return a JSON response with exactly these fields:
{
  "bcs_score": float between 1-5,
  "conditions": [list of observed conditions],
  "severity_score": float between 0-1 (1=healthy, 0=critical),
  "confidence": float between 0-1,
  "observations": "detailed clinical observations",
  "disclaimer": "This is decision support only. Always consult a licensed veterinarian."
}
Return only valid JSON. No preamble or explanation outside the JSON."""

async def analyze_frames(frames: list) -> dict:
    if not frames:
        return {
            "bcs_score": 3.0,
            "conditions": ["No frames extracted"],
            "severity_score": 0.5,
            "confidence": 0.0,
            "observations": "Could not extract frames from video.",
            "disclaimer": "This is decision support only. Always consult a licensed veterinarian."
        }

    encoded = []
    for f in frames[:3]:
        encoded.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64.b64encode(f).decode()}"
            }
        })

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Analyze these cattle frames and return your assessment as JSON."},
                *encoded
            ]
        }
    ]

    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://bourgelat.app",
                "X-Title": "Bourgelat"
            },
            json={
                "model": MODEL_NAME,
                "messages": messages,
                "max_tokens": 1000
            }
        )
        result = response.json()

        # Debug: print full response
        print("OpenRouter response:", json.dumps(result, indent=2))

        if "error" in result:
            raise Exception(f"OpenRouter error: {result['error']}")

        if "choices" not in result:
            raise Exception(f"Unexpected response: {result}")

        text = result["choices"][0]["message"]["content"]
        clean = text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)

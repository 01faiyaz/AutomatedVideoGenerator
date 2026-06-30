import os
import json
import re
import requests
from dotenv import load_dotenv

load_dotenv()


def generate_script(topic: str) -> dict:
    use_ollama = os.getenv("USE_OLLAMA", "true").lower() == "true"

    if use_ollama:
        return _generate_with_ollama(topic)
    else:
        return _generate_with_openai(topic)


def _build_prompt(topic: str) -> str:
    return f"""You are a JSON API. Respond with ONLY a JSON object, no explanation, no markdown, no code fences.

Generate a 60-second educational video script about: {topic}

The JSON must have exactly these keys:
- title: string
- script: string (120-150 words, full narration)
- description: string (2-3 sentences)
- thumbnail_text: string (3-5 words)
- scenes: array of exactly 5 objects, each with scene_number (int), text (string), visual_keywords (array of 2 strings)

Example of the exact format:
{{"title":"Example Title","script":"Full script here...","description":"Description here.","thumbnail_text":"Short Text Here","scenes":[{{"scene_number":1,"text":"Scene one text.","visual_keywords":["keyword1","keyword2"]}},{{"scene_number":2,"text":"Scene two text.","visual_keywords":["keyword1","keyword2"]}},{{"scene_number":3,"text":"Scene three text.","visual_keywords":["keyword1","keyword2"]}},{{"scene_number":4,"text":"Scene four text.","visual_keywords":["keyword1","keyword2"]}},{{"scene_number":5,"text":"Scene five text.","visual_keywords":["keyword1","keyword2"]}}]}}

Now generate for topic: {topic}"""


def _generate_with_ollama(topic: str) -> dict:
    url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
    model = os.getenv("OLLAMA_MODEL", "llama3.1")

    try:
        response = requests.post(
            url,
            json={
                "model": model,
                "prompt": _build_prompt(topic),
                "stream": False,
                "format": "json",   # forces JSON output mode
                "options": {
                    "temperature": 0.3,
                    "num_predict": 1200
                }
            },
            timeout=180
        )
        response.raise_for_status()
        text = response.json()["response"]
        data = _parse_json_response(text)
        return _ensure_scenes(data, topic)
    except requests.exceptions.ConnectionError:
        raise Exception(
            "Could not connect to Ollama. Make sure Ollama is running "
            "and OLLAMA_URL is set to http://localhost:11434/api/generate"
        )


def _generate_with_openai(topic: str) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_key_here":
        raise Exception("OPENAI_API_KEY not set in .env and USE_OLLAMA is false.")

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": "You are a video script writer. Return only valid JSON."},
                {"role": "user", "content": _build_prompt(topic)}
            ],
            "temperature": 0.5
        },
        timeout=60
    )
    response.raise_for_status()
    text = response.json()["choices"][0]["message"]["content"]
    data = _parse_json_response(text)
    return _ensure_scenes(data, topic)


def _parse_json_response(text: str) -> dict:
    # Strip markdown code fences
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    text = text.strip()

    # Extract first JSON object if there's surrounding text
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse AI response as JSON: {e}\n\nRaw:\n{text[:500]}")


def _ensure_scenes(data: dict, topic: str) -> dict:
    """Fill in any missing fields so the pipeline never crashes."""

    if "title" not in data:
        data["title"] = f"All About {topic.title()}"
    if "script" not in data:
        data["script"] = f"Let's explore {topic}. " * 10
    if "description" not in data:
        data["description"] = f"An educational video about {topic}."
    if "thumbnail_text" not in data:
        data["thumbnail_text"] = topic[:30].title()

    # If scenes missing or empty, auto-generate from script
    if not data.get("scenes"):
        script = data["script"]
        sentences = re.split(r"(?<=[.!?])\s+", script.strip())
        sentences = [s for s in sentences if s.strip()]

        # Split into 5 chunks
        chunk_size = max(1, len(sentences) // 5)
        scenes = []
        for i in range(5):
            chunk = sentences[i * chunk_size: (i + 1) * chunk_size]
            text = " ".join(chunk) if chunk else f"Part {i+1} about {topic}"
            # Generate keywords from topic words
            words = [w.lower() for w in topic.split() if len(w) > 3]
            keywords = words[:2] if len(words) >= 2 else [topic.split()[0], "nature"]
            scenes.append({
                "scene_number": i + 1,
                "text": text,
                "visual_keywords": keywords
            })
        data["scenes"] = scenes

    return data

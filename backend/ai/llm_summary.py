import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

MISSING_TELEMETRY_RESPONSE = "That information is not available in the current session."

UNAVAILABLE_TELEMETRY_KEYWORDS = [
    "fuel",
    "fuel level",
    "fuel load",
    "lap time",
    "sector",
    "sector time",
    "gap",
    "tyre temperature",
    "tire temperature",
    "tyre temp",
    "tire temp",
    "brake temperature",
    "brake temp",
    "engine temperature",
    "engine temp",
    "oil temperature",
    "oil temp",
    "tyre pressure",
    "tire pressure",
    "compound",
    "softs",
    "mediums",
    "hards",
    "intermediates",
    "wets",
    "telemetry value",
    "telemetry reading",
]


def risk_level(urgency):
    if urgency >= 90:
        return "CRITICAL"
    if urgency >= 70:
        return "HIGH"
    if urgency >= 40:
        return "MODERATE"
    return "LOW"


def is_missing_telemetry_question(question):
    q = (question or "").lower()
    return any(keyword in q for keyword in UNAVAILABLE_TELEMETRY_KEYWORDS)


def build_session_context(transcript, emotion, driver, ai_summary="", telemetry_context="", engineer_decision=None):
    emotion = emotion or {}
    driver = driver or {}
    stress = driver.get("stress", emotion.get("stress", 0))
    urgency = driver.get("urgency", emotion.get("urgency", 0))

    ctx = {
        "transcript": transcript or "",
        "emotion": emotion.get("emotion", "neutral"),
        "confidence": emotion.get("confidence", 0),
        "stress": stress,
        "urgency": urgency,
        "driver_state": driver.get("driver_state", emotion.get("driver_state", "Calm")),
        "issues": driver.get("issues", []),
        "recommendations": driver.get("recommendations", []),
        "risk": risk_level(urgency),
        "ai_summary": ai_summary or "",
    }
    if telemetry_context:
        ctx["telemetry"] = telemetry_context
    if engineer_decision:
        ctx["engineer_decision"] = engineer_decision
    return ctx



def _get_api_key():
    key = os.getenv("GEMINI_API_KEY")
    if key:
        return key.strip()

    backend_dir = Path(__file__).resolve().parents[1]
    repo_dir = backend_dir.parent
    for env_path in [backend_dir / ".env", repo_dir / ".env"]:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            name, _, value = line.partition("=")
            if name.strip() == "GEMINI_API_KEY":
                return value.strip().strip('"').strip("'")

    return ""


def _call_gemini(prompt, max_tokens=420):
    api_key = _get_api_key()
    if not api_key:
        return ""

    model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip() or "gemini-3.6-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "topP": 0.8,
            "maxOutputTokens": max_tokens,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError):
        return ""

    try:
        parts = body["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, TypeError):
        return ""

    return "".join(part.get("text", "") for part in parts).strip()


def _extract_json(text):
    if not text:
        return {}

    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.removeprefix("json").strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}

    try:
        return json.loads(cleaned[start:end + 1])
    except json.JSONDecodeError:
        return {}


def contains_unsupported_telemetry_claim(text):
    lowered = (text or "").lower()
    suspicious_terms = [
        "fuel level",
        "fuel load",
        "lap time",
        "sector time",
        "tyre temperature",
        "tire temperature",
        "brake temperature",
        "engine temperature",
        "tyre pressure",
        "tire pressure",
    ]
    return any(term in lowered for term in suspicious_terms)


def generate_gemini_brief(context):
    prompt = f"""
You are PitSense's race engineer wording layer.

Use only this JSON session context:
{json.dumps(context, ensure_ascii=True)}

Rules:
- Do not calculate or change emotion, confidence, stress, urgency, driver_state, risk, issues, or recommendations.
- Do not invent telemetry, lap times, tyre temperatures, brake temperatures, fuel levels, tyre pressure, sector gaps, or compounds.
- If a value is not in the JSON, do not mention it.
- Keep the response concise and operational.
- Return JSON only with keys "summary" and "radio_response".

The "summary" must be 4 to 6 short lines covering situation, driver condition, concerns, risk, and action.
The "radio_response" must be one short driver-radio message.
"""
    response = _call_gemini(prompt, max_tokens=360)
    data = _extract_json(response)

    summary = str(data.get("summary", "")).strip()
    radio_response = str(data.get("radio_response", "")).strip()
    if not summary or not radio_response:
        return None
    if contains_unsupported_telemetry_claim(summary) or contains_unsupported_telemetry_claim(radio_response):
        return None

    return {
        "summary": summary,
        "radio_response": radio_response,
    }


def auto_close_json(s):
    stack = []
    in_string = False
    escaped = False
    repaired_chars = []
    
    for i, char in enumerate(s):
        repaired_chars.append(char)
        if escaped:
            escaped = False
            continue
        if char == '\\':
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if not in_string:
            if char == '{':
                stack.append('}')
            elif char == '[':
                stack.append(']')
            elif char == '}':
                if stack and stack[-1] == '}':
                    stack.pop()
            elif char == ']':
                if stack and stack[-1] == ']':
                    stack.pop()
                    
    if in_string:
        repaired_chars.append('"')
        
    while stack:
        repaired_chars.append(stack.pop())
        
    return "".join(repaired_chars)


def repair_and_load_json(text):
    cleaned = text.strip()
    if not cleaned:
        return None
    
    start = cleaned.find("{")
    if start == -1:
        return None
    
    substring = cleaned[start:]
    
    # Try directly
    try:
        return json.loads(substring)
    except json.JSONDecodeError:
        pass
    
    # Try suffixes
    suffixes = ["", "\"", "}", "\"} ", "\"]}", "\"}", "}", "]}", "\"]}}", "\"}}", "}}"]
    for suffix in suffixes:
        try:
            return json.loads(substring + suffix)
        except json.JSONDecodeError:
            pass
            
    # Try auto-close
    try:
        repaired = auto_close_json(substring)
        return json.loads(repaired)
    except Exception:
        pass
        
    return None


def is_context_dict(data):
    if not isinstance(data, dict):
        return False
    context_keys = {"driver_state", "stress", "urgency", "issues", "recommendations", "risk", "transcript", "emotion", "confidence", "ai_summary"}
    keys = set(data.keys())
    preferred_keys = {"answer", "response", "summary", "radio_response"}
    if keys & context_keys and not (keys & preferred_keys):
        return True
    return False


def is_context_or_fragment(text):
    lowered = text.lower()
    context_indicators = ["driver_state", "stress", "urgency", "recommendations", "issues", "transcript", "emotion", "confidence"]
    has_context_field = any(indicator in lowered for indicator in context_indicators)
    
    preferred_fields = ["answer", "response", "summary", "radio_response"]
    has_preferred_field = any(pref in lowered for pref in preferred_fields)
    
    if has_context_field and not has_preferred_field and ":" in lowered:
        return True
    return False


def extract_answer_from_dict(data):
    if not isinstance(data, dict):
        return None
    
    for key in ["answer", "response", "summary", "radio_response"]:
        if key in data:
            val = data[key]
            if isinstance(val, str) and val.strip():
                return val.strip()
            if isinstance(val, dict):
                res = extract_answer_from_dict(val)
                if res:
                    return res
                    
    for key, val in data.items():
        if isinstance(val, str):
            val_clean = val.strip()
            if " " in val_clean and not (val_clean.startswith("{") or val_clean.startswith("[")):
                return val_clean
        elif isinstance(val, dict):
            res = extract_answer_from_dict(val)
            if res:
                return res
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, dict):
                    res = extract_answer_from_dict(item)
                    if res:
                        return res
                elif isinstance(item, str):
                    item_clean = item.strip()
                    if " " in item_clean:
                        return item_clean
    return None


def clean_markdown_fences(text):
    cleaned = text.strip()
    if cleaned.startswith("```"):
        first_newline = cleaned.find("\n")
        if first_newline != -1:
            content = cleaned[first_newline:].strip()
            if content.endswith("```"):
                content = content[:-3].strip()
            return content
        else:
            cleaned = cleaned.strip("`")
            cleaned = cleaned.removeprefix("json").strip()
            return cleaned
    return cleaned


def extract_via_regex(text):
    patterns = [
        r'"(?:answer|response|summary|radio_response)"\s*:\s*"([^"]+)"',
        r"'(?:answer|response|summary|radio_response)'\s*:\s*'([^']+)'",
        r'"(?:answer|response|summary|radio_response)"\s*:\s*\'([^\']+)\'',
        r"'(?:answer|response|summary|radio_response)'\s*:\s*\"([^\"]+)\"",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            return matches[0].strip()
            
    patterns_no_quotes_key = [
        r'(?:answer|response|summary|radio_response)\s*:\s*"([^"]+)"',
        r"(?:answer|response|summary|radio_response)\s*:\s*'([^']+)'",
    ]
    for pattern in patterns_no_quotes_key:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            return matches[0].strip()

    patterns_cutoff = [
        r'"(?:answer|response|summary|radio_response)"\s*:\s*"([^"]*)$',
        r"'(?:answer|response|summary|radio_response)'\s*:\s*'([^']*)$",
        r'(?:answer|response|summary|radio_response)\s*:\s*"([^"]*)$',
        r"(?:answer|response|summary|radio_response)\s*:\s*'([^']*)$",
    ]
    for pattern in patterns_cutoff:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            return matches[0].strip()
            
    return None


def clean_and_parse_gemini_response(text):
    if not text:
        return ""
        
    cleaned = clean_markdown_fences(text)
    
    if is_context_or_fragment(cleaned):
        return ""
        
    data = repair_and_load_json(cleaned)
    if data and isinstance(data, dict):
        if is_context_dict(data):
            return ""
        ans = extract_answer_from_dict(data)
        if ans:
            return ans

    for prefix in ["{", "{\"", "{ \""]:
        try_text = prefix + cleaned
        data = repair_and_load_json(try_text)
        if data and isinstance(data, dict):
            if is_context_dict(data):
                return ""
            ans = extract_answer_from_dict(data)
            if ans:
                return ans
                
    ans = extract_via_regex(cleaned)
    if ans:
        return ans
        
    if cleaned.startswith('"') and cleaned.endswith('"'):
        try:
            unescaped = json.loads(cleaned)
            ans = clean_and_parse_gemini_response(unescaped)
            if ans:
                return ans
        except Exception:
            pass

    if "{" not in cleaned and "}" not in cleaned and "[" not in cleaned and "]" not in cleaned:
        if cleaned.count(":") >= 2:
            return ""
        if cleaned.lower() in ["high stress", "concerned", "calm", "emergency", "neutral", "anxious", "low", "moderate", "high", "critical"]:
            return ""
        return cleaned
        
    return ""


def generate_gemini_chat_answer(context, question):
    if is_missing_telemetry_question(question):
        return MISSING_TELEMETRY_RESPONSE

    prompt = f"""
You are PitSense's AI Race Engineer.

Answer the user's question using only this JSON session context:
{json.dumps(context, ensure_ascii=True)}

User question:
{question}

Rules:
- Be concise, professional, and operational.
- Do not calculate or change the supplied analysis values.
- Do not invent telemetry, lap times, tyre temperatures, brake temperatures, fuel levels, tyre pressure, sector gaps, or compounds.
- If the answer is not available in the JSON session context, return exactly:
{MISSING_TELEMETRY_RESPONSE}
"""
    raw_answer = _call_gemini(prompt, max_tokens=1024)
    if not raw_answer:
        return ""
    
    answer = clean_and_parse_gemini_response(raw_answer)
    if not answer:
        return ""
        
    if contains_unsupported_telemetry_claim(answer):
        return ""
        
    return answer.strip()

from __future__ import annotations

import requests
import json
import os


def get_config():
    from config import (
        AI_FEEDBACK_ENABLED,
        AI_PROVIDER,
        OLLAMA_BASE_URL,
        OLLAMA_MODEL,
        ANTHROPIC_API_KEY,
        CLAUDE_MODEL,
    )

    return (
        AI_FEEDBACK_ENABLED,
        AI_PROVIDER,
        OLLAMA_BASE_URL,
        OLLAMA_MODEL,
        ANTHROPIC_API_KEY,
        CLAUDE_MODEL,
    )


def check_provider_connection() -> bool:
    (
        AI_FEEDBACK_ENABLED,
        AI_PROVIDER,
        OLLAMA_BASE_URL,
        _,
        ANTHROPIC_API_KEY,
        _,
    ) = get_config()
    if not AI_FEEDBACK_ENABLED:
        return False
    if AI_PROVIDER == "ollama":
        try:
            r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
            return r.status_code == 200
        except Exception:
            return False
    elif AI_PROVIDER == "claude":
        return len(ANTHROPIC_API_KEY) > 10
    return False


def is_ai_available() -> dict:
    AI_FEEDBACK_ENABLED, AI_PROVIDER, _, _, _, _ = get_config()
    return {
        "enabled": AI_FEEDBACK_ENABLED,
        "provider": AI_PROVIDER if AI_FEEDBACK_ENABLED else "disabled",
        "ready": True if AI_FEEDBACK_ENABLED else False,
    }


SYSTEM_PROMPT = """You are an expert embroidery digitizing assistant for StitchAI.
Respond ONLY in this exact JSON format with no other text:
{
  "understood_problem": "one sentence description",
  "affected_regions": "all",
  "parameter_changes": {
    "stitch_type": null,
    "density": null,
    "angle": null,
    "length_mm": null
  },
  "user_message": "friendly 1-2 sentence explanation",
  "training_label": "short_label"
}"""


def call_ollama(user_prompt: str) -> str:
    _, _, OLLAMA_BASE_URL, OLLAMA_MODEL, _, _ = get_config()
    print(f"Calling Ollama model: {OLLAMA_MODEL} at {OLLAMA_BASE_URL}")
    full_prompt = f"""Embroidery expert. User feedback: "{user_prompt}"

Reply ONLY with JSON:
{{"understood_problem": "brief issue description", "affected_regions": "all", "parameter_changes": {{"stitch_type": null, "density": null, "angle": null, "length_mm": null}}, "user_message": "one sentence fix explanation", "training_label": "label"}}

Rules: density issue→set density 2-8, rough text→stitch_type satin_stitch density 6, thick border→density 3"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 150,
            "num_ctx": 512,
        },
    }
    r = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json=payload,
        timeout=(10, 60),
    )
    r.raise_for_status()
    response = r.json().get("response", "")
    print(f"Ollama response: {response[:300]}")
    return response


def call_claude(user_prompt: str) -> str:
    _, _, _, _, ANTHROPIC_API_KEY, CLAUDE_MODEL = get_config()
    import anthropic

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    msg = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return msg.content[0].text


def parse_ai_response(text: str) -> dict:
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        return json.loads(text[start:end])
    except Exception:
        return {
            "understood_problem": "Could not parse response",
            "parameter_changes": {},
            "user_message": "I understood your feedback but could not apply changes automatically. Please try rephrasing.",
            "training_label": "parse_error",
        }


def apply_changes(regions: list, changes: dict, affected: str) -> list:
    for region in regions:
        if affected == "all" or region.get("stitch_type") in affected:
            if changes.get("stitch_type"):
                region["stitch_type"] = changes["stitch_type"]
            if changes.get("density"):
                region["density"] = changes["density"]
            if changes.get("angle") is not None:
                region["angle"] = changes["angle"]
            if changes.get("length_mm"):
                region["length_mm"] = changes["length_mm"]
    return regions


def process_feedback(job_id: str, user_message: str) -> dict:
    AI_FEEDBACK_ENABLED, AI_PROVIDER, _, _, _, _ = get_config()
    if not AI_FEEDBACK_ENABLED:
        return {
            "success": False,
            "reason": "disabled",
            "user_message": "AI feedback is currently disabled.",
        }

    regions_path = f"uploads/{job_id}/final_regions.json"
    if not os.path.exists(regions_path):
        return {
            "success": False,
            "reason": "no_design",
            "user_message": "Design not found. Please process an image first.",
        }

    with open(regions_path) as f:
        regions = json.load(f)

    region_summary = f"{len(regions)} regions, types: {list(set(r.get('stitch_type', 'unknown') for r in regions))}"
    user_prompt = f"Design info: {region_summary}\nUser feedback: {user_message}"

    try:
        if AI_PROVIDER == "ollama":
            raw = call_ollama(user_prompt)
        elif AI_PROVIDER == "claude":
            raw = call_claude(user_prompt)
        else:
            raise Exception(f"Unknown provider: {AI_PROVIDER}")

        parsed = parse_ai_response(raw)
        changes = parsed.get("parameter_changes", {})
        affected = parsed.get("affected_regions", "all")
        updated = apply_changes(regions, changes, affected)

        with open(regions_path, "w") as f:
            json.dump(updated, f)

        for fmt in ["dst", "pes"]:
            p = f"outputs/{job_id}/design.{fmt}"
            if os.path.exists(p):
                os.remove(p)

        save_training_data(job_id, user_message, parsed)

        return {
            "success": True,
            "user_message": parsed.get("user_message", "Changes applied successfully."),
            "changes": changes,
        }
    except Exception as e:
        return {
            "success": False,
            "reason": "ai_error",
            "user_message": f"AI error: {str(e)}",
        }


def save_training_data(job_id: str, original_message: str, parsed: dict):
    os.makedirs("ml/training", exist_ok=True)
    entry = {
        "job_id": job_id,
        "feedback": original_message,
        "understood": parsed.get("understood_problem"),
        "changes": parsed.get("parameter_changes", {}),
        "label": parsed.get("training_label"),
    }
    with open("ml/training/feedback_data.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")

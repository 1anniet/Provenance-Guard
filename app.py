import os
import re
import json
import uuid
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from groq import Groq

# Load environment configuration variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev_fallback_key')

# Setup Rate Limiting with Memory Storage (Mandated by Milestone 5)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day"],
    storage_uri="memory://"
)

# Initialize the Groq SDK client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Audit Log File Path
LOG_PATH = "audit_log.jsonl"


# =====================================================================
# AUDIT STORAGE UTILITIES (Structured JSON Lines)
# =====================================================================
def log_event(entry):
    """Appends a single structured transaction entry to the JSONL log file."""
    entry["timestamp"] = datetime.now(timezone.utc).isoformat() + "Z"
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def read_log():
    """Reads and parses all historical records from the log."""
    try:
        with open(LOG_PATH, "r") as f:
            lines = f.readlines()
        return [json.loads(line.strip()) for line in lines if line.strip()]
    except FileNotFoundError:
        return []


def rewrite_all_logs(entries):
    """Overwrites the log database with updated mutated records."""
    with open(LOG_PATH, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


# =====================================================================
# MULTI-SIGNAL PIPELINE LOGIC
# =====================================================================
def evaluate_llm_signal(text: str) -> float:
    """Signal 1: Holistic Semantic Analysis via Groq."""
    system_instruction = (
        "You are an authenticity classifier inside an automated safety pipeline. "
        "Analyze the provided text holistically for signatures of language-model generation. "
        "Output exactly one valid JSON object containing a single key named 'ai_score', "
        "where the value is a float between 0.0 and 1.0. Do not provide markdown formatting."
    )
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": text}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        response_payload = json.loads(completion.choices[0].message.content)
        ai_score = float(response_payload.get("ai_score", 0.50))
        return max(0.0, min(1.0, ai_score))
    except Exception as e:
        app.logger.error(f"Signal 1 API Failure: {str(e)}")
        return 0.50


def evaluate_stylometric_heuristics(text: str) -> float:
    """Signal 2: Calibrated Structural Text Heuristics."""
    words = re.findall(r'\b\w+\b', text.lower())
    total_words = len(words)
    if total_words == 0:
        return 0.50

    unique_words = len(set(words))
    ttr = unique_words / total_words
    ttr_ai_score = max(0.0, min(1.0, 1.2 - (ttr * 1.5)))

    raw_sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in raw_sentences if s.strip()]

    if len(sentences) <= 1:
        variance_ai_score = 0.50
    else:
        sentence_lengths = [len(re.findall(r'\b\w+\b', s)) for s in sentences if re.findall(r'\b\w+\b', s)]
        if not sentence_lengths:
            variance_ai_score = 0.50
        else:
            mean_length = sum(sentence_lengths) / len(sentence_lengths)
            variance = sum((l - mean_length) ** 2 for l in sentence_lengths) / len(sentence_lengths)
            variance_ai_score = max(0.0, min(1.0, 1.0 - (variance / 35.0)))

    return (ttr_ai_score * 0.5) + (variance_ai_score * 0.5)


# =====================================================================
# API ROUTER GATEWAYS
# =====================================================================
@app.route("/submit", methods=["POST"])
@limiter.limit("10 per minute; 100 per day")
def submit():
    """Processes text inputs, fuses pipeline signals, and issues transparency labels."""
    request_data = request.get_json()
    if not request_data or "text" not in request_data or "creator_id" not in request_data:
        return jsonify({"error": "Bad Request. Missing parameters."}), 400

    raw_text = request_data["text"]
    creator_id = request_data["creator_id"]
    content_id = str(uuid.uuid4())

    llm_score = evaluate_llm_signal(raw_text)
    heuristic_score = evaluate_stylometric_heuristics(raw_text)

    # Divergence Safety Guard Logic to protect human academic variations
    score_gap = abs(llm_score - heuristic_score)
    if score_gap > 0.65:
        final_confidence = 0.50
        attribution_verdict = "uncertain"
    else:
        final_confidence = (llm_score * 0.7) + (heuristic_score * 0.3)
        if final_confidence >= 0.70:
            attribution_verdict = "likely_ai"
        elif final_confidence >= 0.35:
            attribution_verdict = "uncertain"
        else:
            attribution_verdict = "likely_human"

    # Verbatim explicit label strings
    if attribution_verdict == "likely_human":
        transparency_label = "🟢 Verified Authentic: This piece exhibits the structural variation and natural voice characteristic of human creation."
    elif attribution_verdict == "uncertain":
        transparency_label = "🟡 System Note: Unable to verify origin. The text displays a mix of structured patterns and organic language choices."
    else:
        transparency_label = "🔴 AI Generated: Automated signatures detected. Content closely matches the structural profiles of language model generations."

    # Commit structured framework metrics directly to persistent log
    audit_frame = {
        "content_id": content_id,
        "creator_id": creator_id,
        "attribution": attribution_verdict,
        "confidence": round(final_confidence, 4),
        "llm_score": round(llm_score, 4),
        "heuristic_score": round(heuristic_score, 4),
        "status": "classified",
        "appeal_filed": False
    }
    log_event(audit_frame)

    return jsonify({
        "content_id": content_id,
        "attribution": attribution_verdict,
        "confidence": round(final_confidence, 4),
        "label": transparency_label
    }), 200


@app.route("/appeal", methods=["POST"])
def appeal():
    """
    Appeals Gateway Module.
    Locates an active classification event, maps reasoning, and flips status to 'under_review'.
    """
    request_data = request.get_json()
    if not request_data or "content_id" not in request_data or "creator_reasoning" not in request_data:
        return jsonify({"error": "Bad Request. Missing 'content_id' or 'creator_reasoning'."}), 400

    target_id = request_data["content_id"]
    reasoning_text = request_data["creator_reasoning"]

    all_entries = read_log()
    record_found = False

    for entry in all_entries:
        if entry.get("content_id") == target_id:
            entry["status"] = "under_review"
            entry["appeal_filed"] = True
            entry["creator_reasoning"] = reasoning_text
            entry["appeal_timestamp"] = datetime.now(timezone.utc).isoformat() + "Z"
            record_found = True
            break

    if not record_found:
        return jsonify({"error": f"Content ID {target_id} not found in log history."}), 404

    # Save tracking modifications back down to persistence layout
    rewrite_all_logs(all_entries)

    return jsonify({
        "status": "success",
        "message": "Appeal logged successfully. Content status updated to under_review."
    }), 200


@app.route("/log", methods=["GET"])
def view_log():
    """Exposes structured tracking history matrix lines for verification."""
    return jsonify({"entries": read_log()[::-1]}), 200


if __name__ == "__main__":
    app.run(port=5000, debug=True)
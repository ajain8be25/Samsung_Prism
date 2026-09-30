"""Small offline troubleshooter using only Python's standard library."""
from __future__ import annotations

import json
import math
import os
import re
import threading
import webbrowser
from collections import Counter
from difflib import SequenceMatcher
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
WEB = ROOT / "web"
STOP = set("a an the and or but if then than to of in on at by for from with into after before when while as is are was were be been being do does did can could should would may might will has have had it its this that these those my me i we you your our they them their phone device smartphone tablet screen display issue problem problem's please help not no can't dont doesn't wont isn't very really just only about what how why".split())
TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?", re.I)
HEADING_RE = re.compile(r"^\s*(?:#{1,6}\s*(.*?)\s*#*|((?:step\s+)?\d+[.)]\s+.+))\s*$", re.I)
MODEL_RE = re.compile(r"\b(?:Galaxy\s+[SAZMF]\s?\d{1,2}(?:\s*(?:Ultra|Plus|FE|5G|Fold|Flip))?|Nexa(?:\s+Fold)?\s+X\d(?:\s+Ultra)?|TechCorp\s+[A-Z0-9-]+)\b", re.I)
HINGLISH = [
    (r"battery\s+jaldi\s+khatam\s+ho\s+jaati\s+hai", "battery drains quickly"),
    (r"battery\s+jaldi\s+khatam", "battery drains quickly"),
    (r"charge\s+jaldi\s+khatam", "battery drains quickly"),
    (r"phone\s+on\s+nahi\s+ho\s+raha", "phone will not turn on"),
    (r"touch\s+kaam\s+nahi\s+kar\s+raha", "touch is not working"),
    (r"screen\s+(?:kaali|kala|black)\s+ho\s+gayi", "screen became black"),
    (r"display\s+(?:kaali|kala)\s+ho\s+gayi", "display became black"),
    (r"phone\s+bahut\s+slow\s+ho\s+gaya\s+hai", "phone is very slow"),
    (r"mera\s+phone", "my phone"),
    (r"bahut\s+garam", "very hot overheating"),
]


def load_json(name: str):
    with (DATA / name).open("r", encoding="utf-8-sig") as f:
        return json.load(f)


SIIS = load_json("siis_responses.json")["responses"]
LINKS = load_json("deeplinks.json")["deeplinks"]


def tokens(text: str) -> list[str]:
    result = []
    for token in TOKEN_RE.findall((text or "").lower()):
        if token in STOP or len(token) < 2:
            continue
        # A few simple suffix reductions help match singular/plural forms.
        if len(token) > 5 and token.endswith("ies"):
            token = token[:-3] + "y"
        elif len(token) > 5 and token.endswith("s") and not token.endswith("ss"):
            token = token[:-1]
        result.append(token)
    return result


def build_index(rows: list[dict], field) -> list[Counter]:
    return [Counter(tokens(field(row))) for row in rows]


def similarity(query: str, query_terms: Counter, doc: str, doc_terms: Counter, idf: dict[str, float]) -> float:
    shared = set(query_terms) & set(doc_terms)
    dot = sum(query_terms[t] * doc_terms[t] * idf.get(t, 1.0) ** 2 for t in shared)
    qnorm = math.sqrt(sum((n * idf.get(t, 1.0)) ** 2 for t, n in query_terms.items()))
    dnorm = math.sqrt(sum((n * idf.get(t, 1.0)) ** 2 for t, n in doc_terms.items()))
    cosine = dot / (qnorm * dnorm) if qnorm and dnorm else 0.0
    seq = SequenceMatcher(None, " ".join(tokens(query)), " ".join(tokens(doc))).ratio()
    return 0.82 * cosine + 0.18 * seq


DOC_TEXTS = [str(r.get("original_query", "")) for r in SIIS]
DOC_TERMS = build_index(SIIS, lambda r: r.get("original_query", ""))
DF = Counter(t for doc in DOC_TERMS for t in doc)
IDF = {t: math.log((len(SIIS) + 1) / (n + 1)) + 1 for t, n in DF.items()}


def split_sections(content: str) -> list[dict[str, str]]:
    lines = (content or "").replace("\r\n", "\n").split("\n")
    first = next((i for i, line in enumerate(lines) if HEADING_RE.match(line)), None)
    if first is None:
        text = "\n".join(lines).strip()
        return [{"title": "Guide", "text": text}] if text else []

    # SIIS prepends product taxonomy before the actual article. Drop that prefix.
    lines = lines[first:]
    sections: list[dict[str, str]] = []
    title = "Guide"
    body: list[str] = []
    for line in lines:
        match = HEADING_RE.match(line)
        if match:
            text = "\n".join(body).strip()
            if text:
                sections.append({"title": title, "text": text})
            title = (match.group(1) or match.group(2) or "Guide").strip().strip("#")
            body = []
        else:
            body.append(line)
    text = "\n".join(body).strip()
    if text:
        sections.append({"title": title, "text": text})
    return sections


# Build a searchable index over every titled section, not just the 20 sample prompts.
SECTION_INDEX: list[tuple[int, int, dict[str, str]]] = []
for row_index, row in enumerate(SIIS):
    article = row.get("siis_response") or {}
    for section_index, section in enumerate(split_sections(article.get("content", ""))):
        SECTION_INDEX.append((row_index, section_index, section))


def best_link(query: str) -> dict | None:
    qterms = Counter(tokens(query))
    best = None
    best_score = 0.0
    for entry in LINKS:
        desc = " ".join(str(entry.get(k) or "") for k in ("message", "description", "qna_description"))
        terms = Counter(tokens(desc))
        shared = set(qterms) & set(terms)
        dot = sum(qterms[t] * terms[t] * IDF.get(t, 1.0) ** 2 for t in shared)
        qnorm = math.sqrt(sum((n * IDF.get(t, 1.0)) ** 2 for t, n in qterms.items()))
        dnorm = math.sqrt(sum((n * IDF.get(t, 1.0)) ** 2 for t, n in terms.items()))
        score = dot / (qnorm * dnorm) if qnorm and dnorm else 0.0
        if score > best_score:
            best, best_score = entry, score
    if best and best_score >= 0.20:
        return {"message": best.get("message") or best.get("description") or "Related setting", "description": best.get("description", "")}
    return None


def normalize_hinglish(query: str) -> tuple[str, bool]:
    normalized = query
    for pattern, replacement in HINGLISH:
        normalized = re.sub(pattern, replacement, normalized, flags=re.I)
    normalized = re.sub(r"\b(bahut|bohot)\b", "very", normalized, flags=re.I)
    normalized = re.sub(r"\b(mera|meri|mere)\b", "my", normalized, flags=re.I)
    return " ".join(normalized.split()), normalized.casefold() != query.casefold()


def extract_model(text: str) -> str | None:
    match = MODEL_RE.search(text or "")
    return " ".join(match.group(0).split()) if match else None


def assess_severity(text: str) -> str:
    text = (text or "").lower()
    if re.search(r"smoke|swelling|swollen|burning smell|burning odor|very hot|overheat|liquid damage|completely dead|won't turn on|will not turn on|doesn't turn on|not turning on|unusable", text):
        return "high"
    if re.search(r"slightly|a little|minor|occasionally|sometimes|intermittent|mild", text):
        return "low"
    return "medium"


def search(query: str, context: str = "") -> dict:
    query = " ".join((query or "").split())[:1200]
    normalized, hinglish_used = normalize_hinglish(query)
    qterms = Counter(tokens(normalized))
    device_model = extract_model(context + " " + query)
    if not qterms:
        return {"match": None, "message": "Describe the phone problem in a few words so I can search the guide.", "severity": assess_severity(query), "device_model": device_model, "understood_as": normalized if hinglish_used else None}
    severity = assess_severity(query)
    battery_query = bool(re.search(r"\bbattery\b|\bcharge\s+jaldi\b", normalized, re.I))
    battery_articles = any(
        re.search(r"battery.{0,35}(?:drain|life|health|usage|replace|optimi)|(?:drain|life|health).{0,35}battery", (str((r.get("siis_response") or {}).get("title", "")) + " " + str(r.get("original_query", ""))), re.I)
        for r in SIIS
    )
    if battery_query and not battery_articles:
        message = "I understood the battery problem, but the supplied dataset has no battery-drain or battery-health guide yet. Add verified battery guidance to cover it."
        return {"match": None, "message": message, "severity": severity, "device_model": device_model, "understood_as": normalized if hinglish_used else None}
    # Blend issue-example similarity with article heading/body similarity so
    # users can find topics mentioned inside the larger SIIS documents too.
    ranked_sections = []
    for row_index, section_index, section in SECTION_INDEX:
        row = SIIS[row_index]
        article = row.get("siis_response") or {}
        example_score = similarity(query, qterms, str(row.get("original_query", "")), DOC_TERMS[row_index], IDF)
        section_text = f"{article.get('title', '')} {section['title']} {section['text'][:1200]}"
        section_score = similarity(query, qterms, section_text, Counter(tokens(section_text)), IDF)
        model_in_record = bool(device_model and re.search(re.escape(device_model), str(row.get("original_query", "")) + " " + str(article.get("title", "")) + " " + str(article.get("content", "")), re.I))
        model_adjustment = 0.12 if model_in_record else -0.08 if device_model else 0.0
        combined = max(0.0, 0.52 * example_score + 0.48 * section_score + model_adjustment)
        ranked_sections.append((combined, row_index, section_index, section_score, example_score))
    score, index, matched_section_index, section_score, example_score = max(ranked_sections)
    if score < 0.14:
        message = "I couldn’t find a close issue in the supplied guide. Add the phone model, what you see, and when it started."
        return {"match": None, "message": message, "severity": severity, "device_model": device_model, "understood_as": normalized if hinglish_used else None}

    row = SIIS[index]
    guide = row.get("siis_response") or {}
    matched_section = next(
        (section["title"] for row_id, section_id, section in SECTION_INDEX
         if row_id == index and section_id == matched_section_index),
        "Guide",
    )
    sections = split_sections(guide.get("content", ""))
    # Keep the article order, while focusing longer articles on sections most related to the report.
    if len(sections) > 7:
        ranked_sections = []
        for i, section in enumerate(sections):
            text = f"{section['title']} {section['text'][:1200]}"
            score_s = similarity(query, qterms, text, Counter(tokens(text)), IDF)
            ranked_sections.append((score_s, i, section))
        picked = sorted(ranked_sections, reverse=True)[:6]
        sections = [item[2] for item in sorted(picked, key=lambda item: item[1])]

    for section in sections:
        section["link_preview"] = best_link(section["title"] + " " + section["text"][:800])

    confidence = "Strongest dataset match" if score >= 0.42 else "Possible dataset match" if score >= 0.25 else "Weak match — check that this guide fits"
    model_in_match = bool(device_model and re.search(re.escape(device_model), str(row.get("original_query", "")) + " " + str(guide.get("title", "")) + " " + str(guide.get("content", "")), re.I))
    if severity == "high":
        service = [s for s in sections if re.search(r"service|repair|support|contact", s["title"], re.I)]
        others = [s for s in sections if s not in service]
        sections = service + others
    return {
        "match": {
            "title": guide.get("title") or "Troubleshooting guide",
            "matched_query": row.get("original_query", ""),
            "matched_section": matched_section,
            "confidence": confidence,
            "score": round(score, 3),
            "sections": sections,
            "model_match": model_in_match if device_model else None,
        },
        "message": "I found the closest guide in the supplied dataset. Check that it describes your exact problem before following its steps.",
        "severity": severity,
        "device_model": device_model,
        "understood_as": normalized if hinglish_used else None,
    }


def load_examples() -> list[str]:
    path = DATA / "input.txt"
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    examples = []
    for line in lines:
        line = line.strip()
        if len(line) <= 70 or not any(word in line.lower() for word in ("phone", "screen", "tablet")):
            continue
        line = re.sub(r'^(?:\d+\.\s*)+', '', line).strip().strip('"')
        if line:
            examples.append(line)
    return examples[:20]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))

    def send_json(self, payload: dict, status: int = 200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/examples":
            return self.send_json({"examples": load_examples(), "records": len(SIIS), "links": len(LINKS)})
        if path == "/api/health":
            return self.send_json({"status": "ok"})
        target = WEB / ("index.html" if path == "/" else path.lstrip("/"))
        if not target.resolve().is_relative_to(WEB.resolve()) or not target.is_file():
            self.send_error(404)
            return
        body = target.read_bytes()
        mime = "text/html; charset=utf-8" if target.suffix == ".html" else "text/css; charset=utf-8" if target.suffix == ".css" else "text/javascript; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if urlparse(self.path).path != "/api/troubleshoot":
            return self.send_json({"error": "not_found"}, 404)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 5000:
                return self.send_json({"error": "Please keep the description under 1,200 characters."}, 413)
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            messages = payload.get("messages")
            if isinstance(messages, list):
                user_messages = [str(m.get("content", "")) for m in messages if isinstance(m, dict) and m.get("role") == "user"]
                query = user_messages[-1] if user_messages else ""
                context = " ".join(user_messages[:-1][-8:])
            else:
                query = str(payload.get("query", ""))
                context = ""
            if not query.strip():
                return self.send_json({"error": "Enter a phone problem first."}, 400)
            return self.send_json(search(query, context))
        except (ValueError, json.JSONDecodeError):
            return self.send_json({"error": "I couldn’t read that request. Please try again."}, 400)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    host = "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1"
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Phone Troubleshooter is ready on {host}:{port}")
    if host == "127.0.0.1":
        print("Open http://127.0.0.1:8000 in your browser.")
    print(f"Loaded {len(SIIS)} troubleshooting records and {len(LINKS)} masked demo links. Press Ctrl+C to stop.")
    if host == "127.0.0.1":
        threading.Timer(0.8, lambda: webbrowser.open("http://127.0.0.1:8000")).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()

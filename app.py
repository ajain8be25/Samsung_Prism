"""Vercel FastAPI adapter for the existing Python troubleshooting engine."""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request

from server import LINKS, SIIS, load_examples, search

app = FastAPI(title="Phone Troubleshooter")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/examples")
def examples() -> dict[str, Any]:
    return {"examples": load_examples(), "records": len(SIIS), "links": len(LINKS)}


@app.post("/api/troubleshoot")
async def troubleshoot(request: Request) -> dict[str, Any]:
    raw = await request.body()
    if len(raw) > 5000:
        raise HTTPException(status_code=413, detail="Please keep the description under 1,200 characters.")
    try:
        payload = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="I couldn’t read that request. Please try again.") from exc

    messages = payload.get("messages")
    if isinstance(messages, list):
        user_messages = [str(m.get("content", "")) for m in messages if isinstance(m, dict) and m.get("role") == "user"]
        query = user_messages[-1] if user_messages else ""
        context = " ".join(user_messages[:-1][-8:])
    else:
        query = str(payload.get("query", ""))
        context = ""
    if not query.strip():
        raise HTTPException(status_code=400, detail="Enter a phone problem first.")
    return search(query, context)

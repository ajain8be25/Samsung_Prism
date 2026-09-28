# 📱 Samsung SIIS Settings & Diagnostic Engine

> An ultra-fast, deterministic troubleshooting and deep-link navigation engine for device settings. Built with **FastAPI**, **React (Vite)**, **Hybrid BM25 + Dense Search**, and a **3-Tier SQLite Semantic Cache**.

![Pytest Suite](https://img.shields.io/badge/tests-37%2F37%20passing-brightgreen)
![Backend](https://img.shields.io/badge/backend-FastAPI-009688)
![Frontend](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61DAFB)
![Docker](https://img.shields.io/badge/docker-ready-2496ED)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

---

## 📌 Overview

Traditional LLM-based troubleshooting tools are often slow, expensive to run, and prone to hallucinating non-existent settings menus or broken deep links. 

The **Samsung SIIS Settings & Diagnostic Engine** solves this by providing a lightweight, zero-hallucination solution. It normalizes colloquial user queries (e.g., *"wifi wont connect"*), retrieves grounded troubleshooting steps directly from official SIIS documentation using a hybrid search strategy, and routes users to the exact setting screen via deep links—all with sub-millisecond response times for cached queries.

---

## ✨ Key Features

- **🎯 Zero-Hallucination Pipeline**: Uses template-based grounded extraction directly from structured SIIS docs. Every step and deep link is strictly verified.
- **🔍 Hybrid Retrieval Engine**: Merges **BM25 lexical search** with **Feature-Hashed Dense Embeddings** to handle both exact keyword matches and conversational phrasing/typos without requiring external API keys.
- **⚡ 3-Tier SQLite Semantic Cache**:
  - **Tier 1 (Exact Match)**: Instant 0 ms lookup for previously seen queries.
  - **Tier 2 (Semantic Similarity)**: Reuses validated results for semantically equivalent queries using cosine similarity.
  - **Tier 3 (Per-Screen Domain Guard)**: Prevents cross-domain cache leaks (e.g., Bluetooth queries will never receive cached Wi-Fi fixes).
- **🔗 Direct Deep-Linking**: Maps resolutions to 40+ specific Android/One UI setting sub-screens (`settings://...`).
- **🛡️ Strict Pydantic Schema Validation**: Enforces programmatically validated data contracts on every response.
- **🧪 100% Test Coverage**: Fully verified pipeline with **37 passing unit & integration tests**.

---

## 🛠️ Architecture & Tech Stack

### System Workflow

```text
[ User Input ] 
      │
      ▼
[ Typo & Colloquial Normalization ]
      │
      ▼
[ 3-Tier Semantic Cache (SQLite) ] ── (Hit <5ms) ──► [ Return Cached Result ]
      │ (Miss)
      ▼
[ Hybrid Search: BM25 + Hashing Embeddings ]
      │
      ▼
[ Leaf-Screen Weighting & Parent-Menu Guard ]
      │
      ▼
[ Grounded Template Extraction & Pydantic Validation ]
      │
      ▼
[ React Diagnostic UI ]

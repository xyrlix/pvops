# Backend Agent Guidelines

## Environment

- Python 3.10+
- No `pytest` / `httpx` / `langchain` / `reportlab` in the current dev environment.
- Prefer `requests` for LLM HTTP calls and `asyncio.to_thread` to avoid blocking.
- Vector store uses PGVector in Docker/Prod; falls back to local SQLite keyword search when dependencies or config are missing.
- Run backend with:
  ```bash
  PYTHONPATH=backend:.:backend/.apt-libs/usr/lib/python3/dist-packages \
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  ```

## Coding Style

- Use `from __future__ import annotations` where forward references help.
- Prefer Pydantic v1 patterns (current project uses `pydantic==1.10`).
- Add Optional type hints for nullable fields.
- Keep providers configurable through environment variables.

## Testing

- Unit tests live under `backend/tests/`.
- When `pytest` is unavailable, run `python3 -m scripts.sanity_check` for a quick smoke test of the LLM factory and vector store.

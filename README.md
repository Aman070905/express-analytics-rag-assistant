# Testing notes

Before submission, run the application locally and test all endpoints through `http://127.0.0.1:8000/docs`.

Recommended smoke-test sequence:
1. `GET /health`
2. Run `python -m scripts.ingest_sample_docs`
3. `GET /documents` — expect four sample sources.
4. `POST /query` with: "What is a StateGraph in LangGraph?"
5. `POST /query` with an unrelated question — expect `insufficient_context` if no corpus passage is relevant.
6. `POST /feedback` with rating `up` or `down`.
7. Upload a small PDF/TXT/MD file using `POST /ingest`.
8. Ingest a publicly accessible HTML documentation URL.

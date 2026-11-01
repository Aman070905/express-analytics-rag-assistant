from pathlib import Path
from tempfile import NamedTemporaryFile
import json
from datetime import datetime, timezone
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings, PROJECT_ROOT
from app.schemas import QueryRequest, QueryResponse, IngestURLRequest, FeedbackRequest
from app.graph import answer_question
from app.ingestion import ingest_file, ingest_url, list_documents

app = FastAPI(
    title="Technical Documentation Assistant",
    description="A self-corrective RAG assistant powered by LangGraph, ChromaDB and FastAPI.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Technical Documentation Assistant is running.", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/query", response_model=QueryResponse)
def query_endpoint(payload: QueryRequest):
    try:
        result = answer_question(payload.question)
        return result
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Query failed: {exc}")

@app.post("/ingest")
async def ingest_endpoint(
    files: list[UploadFile] | None = File(default=None),
    urls: list[str] | None = None,
):
    if not files and not urls:
        raise HTTPException(status_code=400, detail="Provide at least one file or URL.")
    results = []
    if files:
        for upload in files:
            suffix = Path(upload.filename or "").suffix.lower()
            if suffix not in {".pdf", ".txt", ".md", ".markdown"}:
                results.append({"source": upload.filename, "status": "error",
                                "error": "Unsupported file type."})
                continue
            content = await upload.read()
            if len(content) > settings.max_upload_mb * 1024 * 1024:
                results.append({"source": upload.filename, "status": "error",
                                "error": f"File exceeds {settings.max_upload_mb} MB."})
                continue
            temp_path = None
            try:
                with NamedTemporaryFile(delete=False, suffix=suffix) as temp:
                    temp.write(content)
                    temp_path = Path(temp.name)
                results.append(ingest_file(temp_path, upload.filename or temp_path.name))
            except Exception as exc:
                results.append({"source": upload.filename, "status": "error", "error": str(exc)})
            finally:
                if temp_path and temp_path.exists():
                    temp_path.unlink()
    if urls:
        for url in urls:
            try:
                results.append(ingest_url(url))
            except Exception as exc:
                results.append({"source": url, "status": "error", "error": str(exc)})
    return {"results": results}

@app.get("/documents")
def documents_endpoint():
    try:
        return {"documents": list_documents()}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not list documents: {exc}")

@app.post("/feedback")
def feedback_endpoint(payload: FeedbackRequest):
    feedback_path = PROJECT_ROOT / "data" / "feedback.jsonl"
    feedback_path.parent.mkdir(parents=True, exist_ok=True)
    record = payload.model_dump()
    record["created_at"] = datetime.now(timezone.utc).isoformat()
    with feedback_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {"status": "received", "message": "Thank you for your feedback."}

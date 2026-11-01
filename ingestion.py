from pathlib import Path
from urllib.parse import urlparse
import hashlib
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import settings
from app.vectorstore import get_vectorstore

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown"}

def _read_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return path.read_text(encoding="utf-8", errors="replace")

def _fetch_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Only valid HTTP/HTTPS URLs are supported: {url}")
    response = requests.get(
        url, timeout=20, headers={"User-Agent": "ExpressAnalyticsRAG/1.0"}
    )
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").lower()
    if "html" not in content_type and not url.lower().endswith((".html", ".htm")):
        raise ValueError(f"URL does not appear to return HTML: {url}")
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    title = soup.title.get_text(" ", strip=True) if soup.title else url
    text = soup.get_text("\n", strip=True)
    return f"Title: {title}\nSource URL: {url}\n\n{text}"

def _split_and_store(text: str, source: str, source_type: str) -> int:
    cleaned = text.strip()
    if not cleaned:
        raise ValueError(f"No extractable text found in {source}")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""],
        add_start_index=True,
    )
    doc = Document(
        page_content=cleaned,
        metadata={"source": source, "source_type": source_type},
    )
    chunks = splitter.split_documents([doc])
    # Stable IDs make repeated ingestion of the same source less noisy.
    ids = [
        hashlib.sha256(f"{source}:{i}:{chunk.page_content}".encode()).hexdigest()
        for i, chunk in enumerate(chunks)
    ]
    get_vectorstore().add_documents(chunks, ids=ids)
    return len(chunks)

def ingest_file(path: Path, original_name: str | None = None) -> dict:
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("Supported file types: PDF, TXT, MD, MARKDOWN.")
    text = _read_file(path)
    source = original_name or path.name
    count = _split_and_store(text, source, "file")
    return {"source": source, "chunks_added": count, "status": "indexed"}

def ingest_url(url: str) -> dict:
    text = _fetch_url(url)
    count = _split_and_store(text, url, "url")
    return {"source": url, "chunks_added": count, "status": "indexed"}

def list_documents() -> list[dict]:
    store = get_vectorstore()
    result = store.get(include=["metadatas"])
    seen = {}
    for metadata in result.get("metadatas") or []:
        if not metadata:
            continue
        source = metadata.get("source", "unknown")
        item = seen.setdefault(source, {
            "source": source,
            "source_type": metadata.get("source_type", "unknown"),
            "chunks": 0,
        })
        item["chunks"] += 1
    return sorted(seen.values(), key=lambda x: x["source"])

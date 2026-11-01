from pathlib import Path
from app.ingestion import ingest_file

DOCS_DIR = Path(__file__).resolve().parents[1] / "data" / "sample_docs"

def main():
    paths = sorted(p for p in DOCS_DIR.iterdir() if p.is_file())
    if not paths:
        print("No sample documents found.")
        return
    for path in paths:
        try:
            print(ingest_file(path))
        except Exception as exc:
            print(f"Failed to ingest {path.name}: {exc}")

if __name__ == "__main__":
    main()

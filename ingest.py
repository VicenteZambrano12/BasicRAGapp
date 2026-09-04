import argparse
import os
from pathlib import Path

from vector_db.create_vector_db import create_vector_db


def sync_collections(content_dir: str) -> None:
    """Ingest every PDF below content_dir into its Qdrant collection."""
    root = Path(content_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"Content directory does not exist: {root}")

    pdf_files = sorted(root.rglob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in: {root}")

    for pdf_file in pdf_files:
        print(f"Ingesting {pdf_file}")
        create_vector_db(str(pdf_file))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest PDF content into Qdrant")
    parser.add_argument(
        "content_dir",
        nargs="?",
        default=os.getenv("CONTENT_DIRECTORY", "./content"),
        help="Directory containing PDF files",
    )
    args = parser.parse_args()

    content_dir = args.content_dir
    sync_collections(content_dir)
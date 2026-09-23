from dataclasses import dataclass
import hashlib
from pathlib import Path
import re

import chromadb


POLICY_DIR = Path(__file__).resolve().parent / "Policy_Docs"
CHROMA_DIR = Path(__file__).resolve().parent / "DB" / "chroma_policy"
COLLECTION_NAME = "risk_policies"


@dataclass
class PolicyChunk:
    chunk_id: str
    source: str
    section: str
    text: str


def split_oversized_text(text: str, max_characters: int, overlap: int) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip()
        if current and len(candidate) > max_characters:
            chunks.append(current)
            overlap_text = current[-overlap:].strip() if overlap else ""
            current = f"{overlap_text}\n\n{paragraph}".strip()
        else:
            current = candidate

    if current:
        chunks.append(current)

    return chunks


def chunk_policy_document(
    document_path: Path,
    max_characters: int = 1000,
    overlap: int = 200,
) -> list[PolicyChunk]:
    text = document_path.read_text(encoding="utf-8").strip()
    sections = re.split(r"(?=^##? )", text, flags=re.MULTILINE)
    chunks: list[PolicyChunk] = []

    for section_number, section in enumerate(sections):
        section = section.strip()
        if not section:
            continue

        heading_match = re.match(r"^##? (.+)", section)
        section_name = heading_match.group(1).strip() if heading_match else "Document introduction"
        section_parts = split_oversized_text(section, max_characters, overlap)

        for part_number, section_part in enumerate(section_parts):
            chunk_id = (
                f"{document_path.stem}:section-{section_number:02d}:"
                f"chunk-{part_number:02d}"
            )
            chunks.append(
                PolicyChunk(
                    chunk_id=chunk_id,
                    source=document_path.name,
                    section=section_name,
                    text=section_part,
                )
            )

    return chunks


def chunk_policy_directory(policy_dir: Path = POLICY_DIR) -> list[PolicyChunk]:
    chunks: list[PolicyChunk] = []
    for document_path in sorted(policy_dir.glob("*.md")):
        chunks.extend(chunk_policy_document(document_path))
    return chunks


def policy_checksum(document_path: Path) -> str:
    return hashlib.sha256(document_path.read_bytes()).hexdigest()


def index_policy_directory(
    policy_dir: Path = POLICY_DIR,
    chroma_dir: Path = CHROMA_DIR,
) -> None:
    client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    current_sources: set[str] = set()

    for document_path in sorted(policy_dir.glob("*.md")):
        source = document_path.name
        checksum = policy_checksum(document_path)
        current_sources.add(source)
        existing = collection.get(
            where={"source": source},
            include=["metadatas"],
        )
        existing_metadata = existing.get("metadatas") or []
        is_unchanged = bool(existing_metadata) and all(
            metadata.get("document_checksum") == checksum
            for metadata in existing_metadata
        )

        if is_unchanged:
            print(f"Unchanged: {source}")
            continue

        if existing.get("ids"):
            collection.delete(ids=existing["ids"])

        chunks = chunk_policy_document(document_path)
        collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            metadatas=[
                {
                    "source": chunk.source,
                    "section": chunk.section,
                    "chunk_index": index,
                    "document_checksum": checksum,
                }
                for index, chunk in enumerate(chunks)
            ],
        )
        print(f"Indexed: {source} ({len(chunks)} chunks)")

    stored_sources = collection.get(include=["metadatas"]).get("metadatas") or []
    stale_sources = {
        metadata["source"]
        for metadata in stored_sources
        if metadata.get("source") not in current_sources
    }
    for source in stale_sources:
        collection.delete(where={"source": source})
        print(f"Removed: {source}")


if __name__ == "__main__":
    index_policy_directory()

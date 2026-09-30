import chromadb
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
CHROMA_DIR = PROJECT_DIR / "DB" / "chroma_policy"
COLLECTION_NAME = "risk_policies"

def retrieve_policy_context(query: str, n_results: int = 3) -> str:
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = chroma_client.get_collection(name=COLLECTION_NAME)
    policy_results = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["metadatas", "documents"],
    )
    policy_chunks = []
    for document, metadata in zip(
        policy_results.get("documents", [[]])[0],
        policy_results.get("metadatas", [[]])[0],
    ):
        policy_chunks.append(
            f"Source: {metadata.get('source')}\n"
            f"Section: {metadata.get('section')}\n"
            f"{document}"
        )
    return "\n\n---\n\n".join(policy_chunks)

def policy_fetcher(query: str) -> str:
    return retrieve_policy_context(query)
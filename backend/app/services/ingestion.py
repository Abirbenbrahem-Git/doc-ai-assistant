"""
Service responsable du découpage et de l'indexation des documents.
Stratégie de chunking : RecursiveCharacterTextSplitter avec chevauchement
pour éviter de couper des phrases importantes à mi-parcours.
"""
import hashlib
import logging
from pathlib import Path
from typing import Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def get_chroma_client() -> chromadb.ClientAPI:
    """Retourne un client ChromaDB persistant."""
    return chromadb.PersistentClient(
        path=settings.chroma_persist_dir,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def get_embeddings() -> HuggingFaceEmbeddings:
    """Modèle d'embedding local — aucune API key nécessaire."""
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def generate_doc_id(filename: str) -> str:
    """Génère un ID stable basé sur le nom du fichier."""
    return hashlib.md5(filename.encode()).hexdigest()[:12]


def ingest_document(file_path: str, filename: str) -> dict:
    """
    Charge, découpe, embed et stocke un document dans ChromaDB.
    Retourne des métadonnées sur l'ingestion.
    """
    path = Path(file_path)
    doc_id = generate_doc_id(filename)

    # Chargement selon le type de fichier
    if path.suffix.lower() == ".pdf":
        loader = PyPDFLoader(file_path)
    else:
        loader = TextLoader(file_path, encoding="utf-8")

    documents = loader.load()

    # Ajout de métadonnées source sur chaque page
    for doc in documents:
        doc.metadata["source"] = filename
        doc.metadata["doc_id"] = doc_id

    # Découpage en chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    logger.info(f"Document '{filename}' → {len(chunks)} chunks")

    # Stockage dans ChromaDB
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name="documents",
        metadata={"hnsw:space": "cosine"},
    )

    embeddings_model = get_embeddings()
    texts = [chunk.page_content for chunk in chunks]
    metadatas = [chunk.metadata for chunk in chunks]
    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]

    # Générer les embeddings par batch
    embeddings = embeddings_model.embed_documents(texts)

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    return {
        "doc_id": doc_id,
        "filename": filename,
        "chunks": len(chunks),
        "pages": len(documents),
    }


def list_documents() -> list[dict]:
    """Liste tous les documents indexés dans ChromaDB."""
    client = get_chroma_client()
    try:
        collection = client.get_collection("documents")
        results = collection.get(include=["metadatas"])
        seen = {}
        for meta in results["metadatas"]:
            doc_id = meta.get("doc_id")
            if doc_id and doc_id not in seen:
                seen[doc_id] = {
                    "doc_id": doc_id,
                    "filename": meta.get("source", "unknown"),
                }
        return list(seen.values())
    except Exception:
        return []
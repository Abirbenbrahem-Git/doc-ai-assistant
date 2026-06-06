"""
Routes FastAPI exposées :
- POST /api/upload    → ingérer un document
- POST /api/chat      → poser une question à l'agent
- GET  /api/documents → lister les documents indexés
- GET  /api/health    → vérifier que l'API fonctionne
"""
import os
import tempfile
import logging
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.services.ingestion import ingest_document, list_documents
from app.services.agent import run_agent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

ALLOWED_TYPES = {"application/pdf", "text/plain"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


class ChatRequest(BaseModel):
    question: str
    chat_history: list[dict] = []


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict] = []


@router.get("/health")
def health():
    return {"status": "ok", "service": "doc-ai-assistant"}


@router.get("/documents")
def get_documents():
    """Liste tous les documents indexés."""
    docs = list_documents()
    return {"documents": docs, "count": len(docs)}


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Reçoit un fichier (PDF ou TXT), le sauvegarde temporairement,
    l'ingère dans ChromaDB, puis supprime le fichier temporaire.
    """
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Type non supporté : {file.content_type}. Acceptés : PDF, TXT",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Fichier trop grand (max 10 MB)")

    suffix = ".pdf" if file.content_type == "application/pdf" else ".txt"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = ingest_document(tmp_path, file.filename)
        return {
            "message": f"Document '{file.filename}' ingéré avec succès",
            "doc_id": result["doc_id"],
            "chunks": result["chunks"],
            "pages": result["pages"],
        }
    except Exception as e:
        logger.error(f"Erreur ingestion : {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'ingestion : {str(e)}")
    finally:
        os.unlink(tmp_path)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Envoie une question à l'agent LangChain.
    L'agent décide quels outils utiliser et retourne
    une réponse avec les sources.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="La question ne peut pas être vide")

    try:
        result = run_agent(
            question=request.question,
            chat_history=request.chat_history,
        )
        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
        )
    except Exception as e:
        logger.error(f"Erreur agent : {e}")
        raise HTTPException(status_code=500, detail=f"Erreur de l'agent : {str(e)}")
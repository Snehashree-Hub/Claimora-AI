from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from backend.rag.rag_service import (
    rag_chat,
    rag_health
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/rag",
    tags=["RAG Assistant"]
)


# ============================================================
# REQUEST MODEL
# ============================================================

class RAGChatRequest(BaseModel):

    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="User's insurance-related question"
    )

    user_email: Optional[str] = Field(
        default=None,
        description="Optional user email"
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Number of knowledge-base chunks to retrieve"
    )


# ============================================================
# CHAT ENDPOINT
# ============================================================

@router.post("/chat")
def chat(request: RAGChatRequest):

    try:

        # Clean user message
        message = request.message.strip()


        if not message:

            raise HTTPException(
                status_code=400,
                detail="Message cannot be empty."
            )


        # ----------------------------------------------------
        # Call RAG service
        # ----------------------------------------------------

        result = rag_chat(

            question=message,

            top_k=request.top_k
        )


        # ----------------------------------------------------
        # Return frontend-friendly response
        # ----------------------------------------------------

        return {

            "success": True,

            "answer": result.get(
                "answer",
                "Unable to generate an answer."
            ),

            "sources": result.get(
                "sources",
                []
            ),

            "user_email": request.user_email,

            "disclaimer": (
                "This AI assistant provides informational "
                "guidance based on the available ClaimCare Health "
                "Insurance knowledge base. It does not make "
                "final insurance approval or rejection "
                "decisions. Final decisions are made by the "
                "applicable insurer or authorized reviewer."
            )

        }


    except HTTPException:

        raise


    except Exception as exc:

        print(
            f"[RAG API ERROR] {exc}"
        )

        raise HTTPException(

            status_code=500,

            detail=(
                "RAG processing failed. "
                "Please try again later."
            )

        )


# ============================================================
# HEALTH ENDPOINT
# ============================================================

@router.get("/health")
def health():

    try:

        return rag_health()

    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=(
                f"RAG health check failed: {str(exc)}"
            )

        )

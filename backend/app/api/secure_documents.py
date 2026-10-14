from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from backend.security.document_security import (
    save_secure_document,
    verify_secure_document,
    MAX_FILE_SIZE,
    validate_document,
)
from backend.security.audit_service import log_security_event


router = APIRouter(
    prefix="/api/security/documents",
    tags=["Secure Document Security"]
)


@router.post("/upload")
async def secure_document_upload(
    claim_id: str = Form(...),
    user: str = Form("system"),
    document: UploadFile = File(...)
):
    try:
        # Reject unsupported extensions before reading the upload.
        valid, validation_message = validate_document(
            document.filename or "",
            1,
        )

        if not valid:
            log_security_event(
                claim_id=claim_id,
                action="DOCUMENT_UPLOAD",
                status="REJECTED",
                user=user,
                details={
                    "filename": document.filename,
                    "reason": validation_message,
                },
            )
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "message": validation_message,
                },
            )

        # Read in bounded chunks; never load an unlimited upload into memory.
        content_buffer = bytearray()

        while len(content_buffer) <= MAX_FILE_SIZE:
            remaining = MAX_FILE_SIZE + 1 - len(content_buffer)
            chunk = await document.read(min(1024 * 1024, remaining))

            if not chunk:
                break

            content_buffer.extend(chunk)

        if len(content_buffer) > MAX_FILE_SIZE:
            log_security_event(
                claim_id=claim_id,
                action="DOCUMENT_UPLOAD",
                status="REJECTED",
                user=user,
                details={
                    "filename": document.filename,
                    "reason": "Document exceeds the 10 MB size limit.",
                },
            )
            raise HTTPException(
                status_code=413,
                detail={
                    "success": False,
                    "message": "Document exceeds the 10 MB size limit.",
                },
            )

        content = bytes(content_buffer)

        result = save_secure_document(
            original_name=document.filename or "",
            content=content,
            claim_id=claim_id
        )

        if not result["success"]:
            log_security_event(
                claim_id=claim_id,
                action="DOCUMENT_UPLOAD",
                status="REJECTED",
                user=user,
                details={
                    "filename": document.filename,
                    "reason": result.get("message", result.get("reason", "Upload rejected"))
                }
            )
            raise HTTPException(status_code=400, detail=result)

        log_security_event(
            claim_id=claim_id,
            action="DOCUMENT_UPLOAD",
            status="ACCEPTED",
            user=user,
            details={
                "filename": result["original_filename"],
                "stored_filename": result["stored_filename"],
                "file_size": result["file_size"]
            }
        )

        log_security_event(
            claim_id=claim_id,
            action="DOCUMENT_INTEGRITY_FINGERPRINT_RECORDED",
            status="RECORDED",
            user="security_analyzer",
            details={
                "algorithm": "SHA-256",
                "hash": result["sha256"],
                "stored_filename": result["stored_filename"]
            }
        )

        return {
            "success": True,
            "security": {
                "status": "RECORDED",
                "claim_id": claim_id,
                "filename": result["original_filename"],
                "stored_filename": result["stored_filename"],
                "file_size": result["file_size"],
                "algorithm": "SHA-256",
                "sha256": result["sha256"],
                "message": (
                    "Document stored and its fingerprint recorded. "
                    "Run the integrity endpoint to verify it later."
                )
            }
        }

    except HTTPException:
        raise
    except Exception as exc:
        try:
            log_security_event(
                claim_id=claim_id,
                action="DOCUMENT_UPLOAD",
                status="FAILED",
                user=user,
                details={"error": str(exc)}
            )
        except Exception:
            pass

        raise HTTPException(
            status_code=500,
            detail="Secure document upload failed."
        )


@router.get("/verify/{claim_id}/{stored_filename}")
def verify_uploaded_document(claim_id: str, stored_filename: str):
    result = verify_secure_document(claim_id, stored_filename)

    log_security_event(
        claim_id=claim_id,
        action="DOCUMENT_INTEGRITY_RECHECK",
        status=result.get("status", "FAILED"),
        user="security_analyzer",
        details={
            "stored_filename": stored_filename,
            "message": result.get("message", "")
        }
    )

    if result.get("status") == "FAILED":
        raise HTTPException(status_code=400, detail=result)

    return result


@router.get("/health")
def secure_document_health():
    return {
        "status": "healthy",
        "module": "Secure Document Upload",
        "features": [
            "File type validation",
            "10 MB size validation",
            "Safe claim ID validation",
            "Random stored filenames",
            "Recorded SHA-256 document fingerprints",
            "HMAC-SHA256 signed manifest verification",
            "Manifest tampering detection",
            "Document integrity comparison",
            "Upload and verification audit logging"
        ]
    }




from backend.app.security import ClaimoraSecurityMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.auth import router as auth_router
from backend.app.api.claims import router as claims_router
from backend.app.api.documents import router as documents_router
from backend.app.api.eligibility import router as eligibility_router
from backend.app.api.fraud_detection import router as fraud_router
from backend.app.api.orchestrator import router as orchestrator_router
from backend.app.api.datasets import router as datasets_router
from backend.app.api.excel import router as excel_router
from backend.app.api.demo_claims import router as demo_claims_router
from backend.app.api.mail import router as mail_router
from backend.app.api.rag import router as rag_router
from backend.app.api.recommendations import router as recommendations_router
from backend.app.api.security import router as security_router
from backend.app.api.security_audit import router as security_audit_router
from backend.app.api.secure_documents import router as secure_documents_router
from backend.app.api.claim_readiness import router as claim_readiness_router

app = FastAPI(title="ClaimCare API", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(auth_router)
app.include_router(claims_router)
app.include_router(documents_router)
app.include_router(eligibility_router)
app.include_router(fraud_router)
app.include_router(orchestrator_router)
app.include_router(datasets_router)
app.include_router(excel_router)
app.include_router(demo_claims_router)
app.include_router(mail_router)
app.include_router(rag_router)
app.include_router(recommendations_router)
app.include_router(security_router)
app.include_router(security_audit_router)
app.include_router(secure_documents_router)
app.include_router(claim_readiness_router)

app.add_api_route("/", lambda: {"success": True, "message": "ClaimCare API is running"}, methods=["GET"])
app.add_api_route("/health", lambda: {"status": "healthy"}, methods=["GET"])
app.add_api_route("/status", lambda: {"status": "running", "service": "ClaimCare"}, methods=["GET"])





app.add_middleware(ClaimoraSecurityMiddleware)


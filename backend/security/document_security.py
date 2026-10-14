import os
import re
import json
import hashlib
import uuid
import hmac
from datetime import datetime, timezone

from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

load_dotenv(
    dotenv_path=os.path.join(PROJECT_ROOT, ".env"),
    override=False,
)

UPLOAD_DIR = os.path.join(
    PROJECT_ROOT, "backend", "security", "uploads"
)
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".docx", ".txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024

CLAIM_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,99}$")
STORED_NAME_PATTERN = re.compile(
    r"^[a-f0-9]{32}\.(pdf|png|jpg|jpeg|docx|txt)$"
)


def valid_claim_id(claim_id):
    return bool(
        isinstance(claim_id, str)
        and CLAIM_ID_PATTERN.fullmatch(claim_id)
    )


def calculate_sha256(file_path):
    digest = hashlib.sha256()

    with open(file_path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def validate_document(filename, file_size):
    extension = os.path.splitext(str(filename))[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        return False, "Unsupported document type."

    if not isinstance(file_size, int) or file_size <= 0:
        return False, "Document is empty or has an invalid size."

    if file_size > MAX_FILE_SIZE:
        return False, "Document exceeds the 10 MB size limit."

    return True, "Document validation passed."


def _manifest_path(claim_folder):
    return os.path.join(claim_folder, "manifest.json")


def _hmac_key_bytes():
    key = os.getenv("DOCUMENT_MANIFEST_HMAC_KEY")

    if not key:
        raise RuntimeError(
            "DOCUMENT_MANIFEST_HMAC_KEY is missing. "
            "Manifest verification is disabled until configuration is restored."
        )

    try:
        key_bytes = bytes.fromhex(key.strip())
    except ValueError as exc:
        raise RuntimeError(
            "DOCUMENT_MANIFEST_HMAC_KEY is not valid hexadecimal."
        ) from exc

    if len(key_bytes) < 32:
        raise RuntimeError(
            "DOCUMENT_MANIFEST_HMAC_KEY must contain at least 32 bytes."
        )

    return key_bytes


def _load_manifest(claim_folder):
    path = _manifest_path(claim_folder)

    if not os.path.isfile(path):
        return {"documents": {}}

    try:
        with open(path, "r", encoding="utf-8") as stream:
            manifest = json.load(stream)

        if not isinstance(manifest, dict):
            raise ValueError("Manifest root must be an object.")

        if not isinstance(manifest.get("documents"), dict):
            raise ValueError("Manifest documents must be an object.")

        return manifest

    except (OSError, ValueError, TypeError) as exc:
        raise RuntimeError(
            "Document manifest is unreadable; manual recovery is required."
        ) from exc


def _manifest_payload(manifest):
    payload = dict(manifest)
    payload.pop("manifest_hmac_sha256", None)

    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _sign_manifest(manifest):
    key_bytes = _hmac_key_bytes()
    signature = hmac.new(
        key_bytes,
        _manifest_payload(manifest),
        hashlib.sha256,
    ).hexdigest()

    manifest["manifest_hmac_sha256"] = signature
    return manifest


def _verify_manifest_signature(manifest):
    try:
        key_bytes = _hmac_key_bytes()
    except RuntimeError as exc:
        return False, str(exc)

    signature = manifest.get("manifest_hmac_sha256")

    if not isinstance(signature, str) or not re.fullmatch(
        r"[a-f0-9]{64}", signature
    ):
        return False, "Manifest is unsigned; explicit migration is required."

    expected = hmac.new(
        key_bytes,
        _manifest_payload(manifest),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):
        return False, "Manifest HMAC verification failed; possible tampering."

    return True, "Manifest HMAC verified."


def _save_manifest(claim_folder, manifest):
    os.makedirs(claim_folder, exist_ok=True)

    path = _manifest_path(claim_folder)
    temp_path = path + "." + uuid.uuid4().hex + ".tmp"

    try:
        with open(temp_path, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(
                manifest,
                stream,
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())

        os.replace(temp_path, path)

    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def save_secure_document(claim_id, original_name, content):
    if not valid_claim_id(claim_id):
        return {
            "success": False,
            "status": "FAILED",
            "message": "Invalid claim ID.",
        }

    if not isinstance(content, bytes):
        return {
            "success": False,
            "status": "FAILED",
            "message": "Document content must be bytes.",
        }

    safe_original = os.path.basename(str(original_name or ""))
    valid, message = validate_document(safe_original, len(content))

    if not valid:
        return {
            "success": False,
            "status": "FAILED",
            "message": message,
        }

    extension = os.path.splitext(safe_original)[1].lower()
    stored_name = uuid.uuid4().hex + extension

    claim_folder = os.path.abspath(os.path.join(UPLOAD_DIR, claim_id))
    target_path = os.path.abspath(os.path.join(claim_folder, stored_name))

    if os.path.commonpath([UPLOAD_DIR, claim_folder]) != os.path.abspath(UPLOAD_DIR):
        return {
            "success": False,
            "status": "FAILED",
            "message": "Invalid storage path.",
        }

    if os.path.commonpath([claim_folder, target_path]) != claim_folder:
        return {
            "success": False,
            "status": "FAILED",
            "message": "Invalid document path.",
        }

    manifest_path = _manifest_path(claim_folder)
    file_created = False

    try:
        # An existing manifest must already be signed and valid.
        if os.path.exists(manifest_path):
            manifest = _load_manifest(claim_folder)
            verified, reason = _verify_manifest_signature(manifest)

            if not verified:
                return {
                    "success": False,
                    "status": "FAILED",
                    "message": reason,
                }
        else:
            manifest = {"documents": {}}

        os.makedirs(claim_folder, exist_ok=True)

        with open(target_path, "xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())

        file_created = True
        sha256_hash = calculate_sha256(target_path)

        manifest["documents"][stored_name] = {
            "claim_id": claim_id,
            "original_filename": safe_original,
            "stored_filename": stored_name,
            "file_size": len(content),
            "algorithm": "SHA-256",
            "sha256": sha256_hash,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }

        _sign_manifest(manifest)
        _save_manifest(claim_folder, manifest)

        return {
            "success": True,
            "status": "VERIFIED",
            "claim_id": claim_id,
            "original_filename": safe_original,
            "stored_filename": stored_name,
            "sha256": sha256_hash,
            "file_size": len(content),
            "message": "Document stored and manifest signed successfully.",
        }

    except Exception as exc:
        if file_created and os.path.isfile(target_path):
            try:
                os.remove(target_path)
            except OSError:
                pass

        return {
            "success": False,
            "status": "FAILED",
            "message": "Secure storage failed: " + str(exc),
        }


def verify_secure_document(claim_id, stored_filename):
    if not valid_claim_id(claim_id):
        return {
            "success": False,
            "status": "FAILED",
            "message": "Invalid claim ID.",
        }

    if not isinstance(stored_filename, str) or not STORED_NAME_PATTERN.fullmatch(
        stored_filename
    ):
        return {
            "success": False,
            "status": "FAILED",
            "message": "Invalid stored filename.",
        }

    claim_folder = os.path.abspath(os.path.join(UPLOAD_DIR, claim_id))
    file_path = os.path.abspath(os.path.join(claim_folder, stored_filename))

    if os.path.commonpath([UPLOAD_DIR, claim_folder]) != os.path.abspath(UPLOAD_DIR):
        return {
            "success": False,
            "status": "FAILED",
            "message": "Invalid storage path.",
        }

    if os.path.commonpath([claim_folder, file_path]) != claim_folder:
        return {
            "success": False,
            "status": "FAILED",
            "message": "Invalid document path.",
        }

    try:
        manifest_path = _manifest_path(claim_folder)

        if not os.path.isfile(manifest_path):
            return {
                "success": False,
                "status": "FAILED",
                "message": "Manifest is missing; document cannot be trusted.",
            }

        manifest = _load_manifest(claim_folder)
        verified, reason = _verify_manifest_signature(manifest)

        # Never trust manifest entries until the HMAC passes.
        if not verified:
            return {
                "success": False,
                "status": "FAILED",
                "message": reason,
            }

        record = manifest["documents"].get(stored_filename)

        if not isinstance(record, dict) or record.get("claim_id") != claim_id:
            return {
                "success": False,
                "status": "NOT_REGISTERED",
                "claim_id": claim_id,
                "stored_filename": stored_filename,
                "message": "Document is not registered to this claim.",
            }

        if not os.path.isfile(file_path):
            return {
                "success": False,
                "status": "MISSING",
                "claim_id": claim_id,
                "stored_filename": stored_filename,
                "message": "Registered document file is missing.",
            }

        expected_hash = record.get("sha256")
        current_hash = calculate_sha256(file_path)

        if not isinstance(expected_hash, str) or not re.fullmatch(
            r"[a-fA-F0-9]{64}", expected_hash
        ):
            return {
                "success": False,
                "status": "FAILED",
                "claim_id": claim_id,
                "stored_filename": stored_filename,
                "message": "Manifest contains an invalid SHA-256 value.",
            }

        matches = hmac.compare_digest(
            expected_hash.lower(),
            current_hash.lower(),
        )

        return {
            "success": matches,
            "status": "VERIFIED" if matches else "MODIFIED",
            "claim_id": claim_id,
            "stored_filename": stored_filename,
            "expected_sha256": expected_hash,
            "current_sha256": current_hash,
            "file_size": os.path.getsize(file_path),
            "message": (
                "Manifest signature and document integrity verified."
                if matches
                else "Document hash mismatch; possible document tampering."
            ),
        }

    except Exception as exc:
        return {
            "success": False,
            "status": "FAILED",
            "message": "Document verification failed: " + str(exc),
        }

import os
import sys
import hmac
import shutil
from datetime import datetime, timezone

from document_security import (
    UPLOAD_DIR,
    STORED_NAME_PATTERN,
    calculate_sha256,
    _load_manifest,
    _sign_manifest,
    _verify_manifest_signature,
    _hmac_key_bytes,
    _save_manifest,
)


def inspect_legacy_manifest(manifest_path):
    claim_folder = os.path.dirname(os.path.abspath(manifest_path))
    claim_id = os.path.basename(claim_folder)
    manifest = _load_manifest(claim_folder)

    if not isinstance(manifest.get("documents"), dict):
        return False, "INVALID_DOCUMENTS_OBJECT", None

    for stored_name, record in manifest["documents"].items():
        if not isinstance(stored_name, str) or not STORED_NAME_PATTERN.fullmatch(
            stored_name
        ):
            return False, "INVALID_STORED_FILENAME", None

        if not isinstance(record, dict):
            return False, "INVALID_RECORD", None

        if record.get("stored_filename") != stored_name:
            return False, "FILENAME_MISMATCH", None

        if record.get("claim_id") != claim_id:
            return False, "CLAIM_ID_MISMATCH", None

        expected = record.get("sha256")
        if not isinstance(expected, str) or len(expected) != 64:
            return False, "INVALID_RECORDED_HASH", None

        file_path = os.path.join(claim_folder, stored_name)
        if not os.path.isfile(file_path):
            return False, "FILE_MISSING", None

        actual = calculate_sha256(file_path)
        if not hmac.compare_digest(expected.lower(), actual.lower()):
            return False, "FILE_HASH_MISMATCH", None

    return True, "LEGACY_FILES_MATCH_RECORDED_HASHES", manifest


def main():
    apply_changes = "--apply" in sys.argv[1:]

    try:
        _hmac_key_bytes()
    except RuntimeError as exc:
        print("ERROR:", str(exc))
        return 2

    if not os.path.isdir(UPLOAD_DIR):
        print("Upload directory does not exist:", UPLOAD_DIR)
        return 1

    manifest_paths = []

    for root, dirs, files in os.walk(UPLOAD_DIR):
        dirs.sort()
        if "manifest.json" in files:
            manifest_paths.append(os.path.join(root, "manifest.json"))

    manifest_paths.sort()

    print("Mode:", "APPLY" if apply_changes else "DRY RUN")
    print("Manifest count:", len(manifest_paths))

    if not apply_changes:
        print("No files will be changed. Re-run with --apply only after reviewing results.")

    errors = 0

    for manifest_path in manifest_paths:
        relative = os.path.relpath(manifest_path, UPLOAD_DIR)

        try:
            manifest = _load_manifest(os.path.dirname(manifest_path))

            if "manifest_hmac_sha256" in manifest:
                valid, reason = _verify_manifest_signature(manifest)

                if valid:
                    print("SKIP - already signed and valid:", relative)
                else:
                    print("ERROR - existing signature invalid:", relative, "-", reason)
                    errors += 1
                continue

            valid, reason, manifest = inspect_legacy_manifest(manifest_path)

            if not valid:
                print("SKIP - legacy validation failed:", relative, "-", reason)
                errors += 1
                continue

            print("READY -", relative, "-", reason)

            if not apply_changes:
                continue

            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup_path = manifest_path + ".backup_pre_hmac_" + stamp

            if os.path.exists(backup_path):
                print("ERROR - backup already exists:", relative)
                errors += 1
                continue

            shutil.copy2(manifest_path, backup_path)

            # Re-check file hashes immediately before signing.
            valid_again, reason_again, latest_manifest = inspect_legacy_manifest(
                manifest_path
            )

            if not valid_again:
                print("ERROR - changed during migration:", relative, "-", reason_again)
                errors += 1
                continue

            _sign_manifest(latest_manifest)
            _save_manifest(os.path.dirname(manifest_path), latest_manifest)

            saved = _load_manifest(os.path.dirname(manifest_path))
            signature_valid, signature_reason = _verify_manifest_signature(saved)

            if signature_valid:
                print("MIGRATED -", relative, "| backup:", os.path.basename(backup_path))
            else:
                print("ERROR - post-write verification failed:", relative, "-", signature_reason)
                errors += 1

        except Exception as exc:
            print("ERROR -", relative, "-", str(exc))
            errors += 1

    print("Migration finished. Errors/skipped manifests:", errors)

    if errors:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

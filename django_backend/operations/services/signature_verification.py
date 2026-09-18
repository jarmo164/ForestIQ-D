"""Verification boundary for trusted electronic-signature provider evidence."""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any


class SignatureVerificationError(ValueError):
    pass


def file_sha256(uploaded) -> str:
    digest = hashlib.sha256()
    for chunk in uploaded.chunks():
        digest.update(chunk)
    uploaded.seek(0)
    return digest.hexdigest()


def canonical_evidence(payload: dict[str, Any]) -> bytes:
    evidence = {key: value for key, value in payload.items() if key != "providerSignature"}
    return json.dumps(evidence, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def verify_provider_evidence(
    payload: dict[str, Any],
    *,
    secret: str,
    expected_sha256: str = "",
    expected_signer_id: str = "",
) -> dict[str, Any]:
    if not secret:
        raise SignatureVerificationError("Signature verification provider secret is not configured.")
    supplied_signature = str(payload.get("providerSignature") or "").strip().lower()
    expected_signature = hmac.new(secret.encode(), canonical_evidence(payload), hashlib.sha256).hexdigest()
    if not supplied_signature or not hmac.compare_digest(supplied_signature, expected_signature):
        raise SignatureVerificationError("Signature provider evidence authentication failed.")
    document_sha256 = str(payload.get("documentSha256") or "").strip().lower()
    if len(document_sha256) != 64 or any(char not in "0123456789abcdef" for char in document_sha256):
        raise SignatureVerificationError("A valid documentSha256 is required.")
    if expected_sha256 and not hmac.compare_digest(document_sha256, expected_sha256.lower()):
        raise SignatureVerificationError("Verified document hash does not match the uploaded document.")
    signer = payload.get("signer")
    certificate = payload.get("certificate")
    reference = str(payload.get("providerReference") or "").strip()
    if not isinstance(signer, dict) or not signer.get("identifier"):
        raise SignatureVerificationError("Verified signer identity is required.")
    if expected_signer_id and str(signer["identifier"]) != str(expected_signer_id):
        raise SignatureVerificationError("Verified signer does not match the contract seller.")
    if not isinstance(certificate, dict) or not certificate.get("serialNumber"):
        raise SignatureVerificationError("Verified certificate metadata is required.")
    if certificate.get("trusted") is not True or certificate.get("validAtSigning") is not True:
        raise SignatureVerificationError("The signing certificate is not trusted or was not valid at signing time.")
    if payload.get("signatureValid") is not True or payload.get("timestampValid") is not True:
        raise SignatureVerificationError("The signature or trusted timestamp is invalid.")
    if not reference:
        raise SignatureVerificationError("providerReference is required.")
    return {
        "documentSha256": document_sha256,
        "signer": signer,
        "certificate": certificate,
        "providerReference": reference,
    }


def stored_file_integrity(field_file, expected_sha256: str) -> bool | None:
    if not field_file or not expected_sha256:
        return None
    try:
        field_file.open("rb")
        return hmac.compare_digest(file_sha256(field_file), expected_sha256.lower())
    except (OSError, ValueError):
        return False
    finally:
        try:
            field_file.close()
        except (OSError, ValueError):
            pass

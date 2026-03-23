"""Verifactu endpoint configuration and environment settings."""

from __future__ import annotations

from enum import Enum


class Environment(str, Enum):
    """AEAT environment selector."""

    PRODUCTION = "production"
    SANDBOX = "sandbox"


class CertificateType(str, Enum):
    """Certificate type determines the host prefix (www1 vs www10)."""

    PERSONAL = "personal"
    ENTITY_SEAL = "entity_seal"


# ---------------------------------------------------------------------------
# SOAP endpoint paths (same across all environments)
# ---------------------------------------------------------------------------
_VERIFACTU_PATH = "/wlpl/TIKE-CONT/ws/SistemaFacturacion/VerifactuSOAP"
_REQUERIMIENTO_PATH = "/wlpl/TIKE-CONT/ws/SistemaFacturacion/RequerimientoSOAP"
_QR_VALIDATE_PATH = "/wlpl/TIKE-CONT/ValidarQR"

# ---------------------------------------------------------------------------
# Host mappings: (environment, certificate_type) -> host
# ---------------------------------------------------------------------------
_HOSTS: dict[tuple[Environment, CertificateType], str] = {
    (Environment.PRODUCTION, CertificateType.PERSONAL): "https://www1.agenciatributaria.gob.es",
    (Environment.PRODUCTION, CertificateType.ENTITY_SEAL): "https://www10.agenciatributaria.gob.es",
    (Environment.SANDBOX, CertificateType.PERSONAL): "https://prewww1.aeat.es",
    (Environment.SANDBOX, CertificateType.ENTITY_SEAL): "https://prewww10.aeat.es",
}

_QR_HOSTS: dict[Environment, str] = {
    Environment.PRODUCTION: "https://www2.agenciatributaria.gob.es",
    Environment.SANDBOX: "https://prewww2.aeat.es",
}


def get_submit_url(
    environment: Environment,
    certificate_type: CertificateType,
    *,
    is_verifactu: bool = True,
) -> str:
    """Build the full SOAP submit endpoint URL.

    Args:
        environment: Production or sandbox.
        certificate_type: Personal certificate or entity seal.
        is_verifactu: ``True`` for VERI*FACTU mode, ``False`` for NO VERI*FACTU (requerimiento).

    Returns:
        Full URL for the submit SOAP service.
    """
    host = _HOSTS[(environment, certificate_type)]
    path = _VERIFACTU_PATH if is_verifactu else _REQUERIMIENTO_PATH
    return f"{host}{path}"


def get_query_url(
    environment: Environment,
    certificate_type: CertificateType,
) -> str:
    """Build the full SOAP query endpoint URL (VERI*FACTU only).

    The query service only exists for VERI*FACTU mode.
    """
    host = _HOSTS[(environment, certificate_type)]
    return f"{host}{_VERIFACTU_PATH}"


def get_qr_validation_url(environment: Environment) -> str:
    """Build the QR code validation base URL.

    Args:
        environment: Production or sandbox.

    Returns:
        Base URL for the QR validation service (without query params).
    """
    host = _QR_HOSTS[environment]
    return f"{host}{_QR_VALIDATE_PATH}"


# ---------------------------------------------------------------------------
# Protocol constants
# ---------------------------------------------------------------------------
MAX_RECORDS_PER_SUBMISSION = 1000
MAX_RECORDS_PER_QUERY_RESPONSE = 10_000
DEFAULT_WAIT_TIME_SECONDS = 60
MAX_GENERATION_TO_SEND_SECONDS = 240
VERIFACTU_VERSION = "1.0"

# SOAP action is empty string per WSDL
SOAP_ACTION = ""
SOAP_CONTENT_TYPE = 'text/xml; charset="UTF-8"'

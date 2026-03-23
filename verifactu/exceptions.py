"""Verifactu SDK exception hierarchy."""

from __future__ import annotations


class VerifactuError(Exception):
    """Base exception for all Verifactu SDK errors."""


class ValidationError(VerifactuError):
    """Model or business rule validation failed."""


class CertificateError(VerifactuError):
    """Certificate loading, parsing, or authentication error."""


class SOAPFaultError(VerifactuError):
    """AEAT returned a SOAP fault (envelope-level rejection).

    Attributes:
        fault_code: ``soapenv:Client`` or ``soapenv:Server``.
        fault_string: Human-readable description from AEAT.
        detail: Optional raw detail text from the fault.
    """

    def __init__(
        self,
        fault_code: str,
        fault_string: str,
        detail: str | None = None,
    ) -> None:
        self.fault_code = fault_code
        self.fault_string = fault_string
        self.detail = detail
        super().__init__(f"SOAP Fault [{fault_code}]: {fault_string}")

    @property
    def is_retryable(self) -> bool:
        """``soapenv:Server`` faults are retryable; ``soapenv:Client`` are not."""
        return "Server" in self.fault_code


class AEATError(VerifactuError):
    """AEAT rejected one or more records (business-level error).

    Attributes:
        code: Numeric AEAT error code (e.g. 4102, 1106, 2000, 3000).
        description: AEAT error description.
    """

    def __init__(self, code: int, description: str) -> None:
        self.code = code
        self.description = description
        super().__init__(f"AEAT Error {code}: {description}")

    @property
    def is_full_rejection(self) -> bool:
        """4xxx errors reject the entire submission."""
        return 4000 <= self.code < 5000

    @property
    def is_record_rejection(self) -> bool:
        """1xxx errors reject an individual record."""
        return 1000 <= self.code < 2000

    @property
    def is_accepted_with_errors(self) -> bool:
        """2xxx errors: record accepted but should be corrected."""
        return 2000 <= self.code < 3000

    @property
    def is_duplicate(self) -> bool:
        """3000 = duplicate record."""
        return self.code == 3000


class ConnectionError(VerifactuError):
    """Network or TLS connection failure to AEAT endpoints."""


class ChainError(VerifactuError):
    """Hash chain integrity or state error."""

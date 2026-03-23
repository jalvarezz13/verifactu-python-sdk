"""SOAP client for AEAT Verifactu web services.

Handles certificate-authenticated HTTPS communication with AEAT endpoints
for submit (alta/anulación) and query operations.
"""

from __future__ import annotations

import ssl
import tempfile
from pathlib import Path
from typing import Union

import requests

from verifactu.config import (
    SOAP_ACTION,
    SOAP_CONTENT_TYPE,
    CertificateType,
    Environment,
    get_query_url,
    get_submit_url,
)
from verifactu.exceptions import CertificateError, ConnectionError, SOAPFaultError
from verifactu.models.cancellation import RegistroAnulacion
from verifactu.models.header import Cabecera
from verifactu.models.invoice import RegistroAlta
from verifactu.models.query import ConsultaFactura, RespuestaConsulta
from verifactu.models.response import RespuestaEnvio
from verifactu.xml.builder import build_query_xml, build_submit_xml
from verifactu.xml.parser import parse_query_response, parse_submit_response


class VeriFactuClient:
    """SOAP client for AEAT Verifactu services.

    Supports both VERI*FACTU (voluntary submission + query) and
    NO VERI*FACTU (submission by requirement) modes.

    Authentication uses client certificates (mTLS). Accepts either:
    - PEM files (cert_path + key_path)
    - PKCS#12 (.p12/.pfx) files (converted to PEM on-the-fly)

    Usage::

        client = VeriFactuClient(
            environment=Environment.SANDBOX,
            certificate_type=CertificateType.PERSONAL,
            cert_path="/path/to/cert.pem",
            key_path="/path/to/key.pem",
        )

        response = client.submit(cabecera, [registro_alta])
        query_result = client.query(consulta)
    """

    def __init__(
        self,
        *,
        environment: Environment = Environment.SANDBOX,
        certificate_type: CertificateType = CertificateType.PERSONAL,
        cert_path: str | Path | None = None,
        key_path: str | Path | None = None,
        pfx_path: str | Path | None = None,
        pfx_password: str | None = None,
        is_verifactu: bool = True,
        timeout: int = 30,
    ) -> None:
        self.environment = environment
        self.certificate_type = certificate_type
        self.is_verifactu = is_verifactu
        self.timeout = timeout
        self._last_wait_time: int = 60

        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": SOAP_CONTENT_TYPE,
            "SOAPAction": SOAP_ACTION,
        })

        self._temp_files: list[tempfile.NamedTemporaryFile] = []
        self._configure_certificate(cert_path, key_path, pfx_path, pfx_password)

    def _configure_certificate(
        self,
        cert_path: str | Path | None,
        key_path: str | Path | None,
        pfx_path: str | Path | None,
        pfx_password: str | None,
    ) -> None:
        if cert_path and key_path:
            self._session.cert = (str(cert_path), str(key_path))
        elif pfx_path:
            cert_pem, key_pem = self._pfx_to_pem(Path(pfx_path), pfx_password)
            self._session.cert = (cert_pem, key_pem)
        self._session.verify = True

    def _pfx_to_pem(self, pfx_path: Path, password: str | None) -> tuple[str, str]:
        try:
            from cryptography.hazmat.primitives.serialization import (
                BestAvailableEncryption,
                Encoding,
                NoEncryption,
                pkcs12,
                PrivateFormat,
            )
        except ImportError:
            msg = "cryptography package required for PFX certificate support"
            raise CertificateError(msg) from None

        try:
            pfx_data = pfx_path.read_bytes()
            pwd = password.encode() if password else None
            private_key, certificate, chain = pkcs12.load_key_and_certificates(pfx_data, pwd)
        except Exception as e:
            msg = f"Failed to load PFX certificate from {pfx_path}: {e}"
            raise CertificateError(msg) from e

        if private_key is None or certificate is None:
            msg = f"PFX file {pfx_path} does not contain both key and certificate"
            raise CertificateError(msg)

        cert_tmp = tempfile.NamedTemporaryFile(suffix=".pem", delete=False)
        key_tmp = tempfile.NamedTemporaryFile(suffix=".pem", delete=False)
        self._temp_files.extend([cert_tmp, key_tmp])

        cert_pem = certificate.public_bytes(Encoding.PEM)
        if chain:
            for ca_cert in chain:
                cert_pem += ca_cert.public_bytes(Encoding.PEM)
        cert_tmp.write(cert_pem)
        cert_tmp.flush()

        key_pem = private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
        key_tmp.write(key_pem)
        key_tmp.flush()

        return cert_tmp.name, key_tmp.name

    @property
    def submit_url(self) -> str:
        return get_submit_url(
            self.environment,
            self.certificate_type,
            is_verifactu=self.is_verifactu,
        )

    @property
    def query_url(self) -> str:
        return get_query_url(self.environment, self.certificate_type)

    @property
    def last_wait_time(self) -> int:
        """Seconds to wait before next submission (from last AEAT response)."""
        return self._last_wait_time

    def submit(
        self,
        cabecera: Cabecera,
        records: list[Union[RegistroAlta, RegistroAnulacion]],
    ) -> RespuestaEnvio:
        """Submit invoice records (alta and/or anulación) to AEAT.

        Args:
            cabecera: Submission header identifying the obligated party.
            records: List of RegistroAlta and/or RegistroAnulacion (max 1000).

        Returns:
            AEAT response with per-record status.

        Raises:
            SOAPFaultError: AEAT rejected the entire envelope.
            ConnectionError: Network or TLS failure.
            ValidationError: Record count exceeds 1000.
        """
        if len(records) > 1000:
            from verifactu.exceptions import ValidationError

            msg = f"Max 1000 records per submission, got {len(records)}"
            raise ValidationError(msg)

        xml_bytes = build_submit_xml(cabecera, records)
        response_bytes = self._send(self.submit_url, xml_bytes)
        result = parse_submit_response(response_bytes)
        self._last_wait_time = result.tiempo_espera_envio
        return result

    def query(self, consulta: ConsultaFactura) -> RespuestaConsulta:
        """Query invoice records from AEAT (VERI*FACTU mode only).

        Args:
            consulta: Query parameters.

        Returns:
            Query results with pagination info.

        Raises:
            SOAPFaultError: AEAT rejected the query.
            ConnectionError: Network or TLS failure.
        """
        xml_bytes = build_query_xml(consulta)
        response_bytes = self._send(self.query_url, xml_bytes)
        return parse_query_response(response_bytes)

    def _send(self, url: str, xml_bytes: bytes) -> bytes:
        try:
            response = self._session.post(
                url,
                data=xml_bytes,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.content
        except requests.exceptions.SSLError as e:
            msg = f"TLS/certificate error communicating with {url}: {e}"
            raise CertificateError(msg) from e
        except requests.exceptions.ConnectionError as e:
            msg = f"Connection failed to {url}: {e}"
            raise ConnectionError(msg) from e
        except requests.exceptions.Timeout as e:
            msg = f"Request to {url} timed out after {self.timeout}s"
            raise ConnectionError(msg) from e
        except requests.exceptions.HTTPError as e:
            return e.response.content if e.response is not None else b""

    def close(self) -> None:
        """Close the HTTP session and clean up temp files."""
        self._session.close()
        for tmp in self._temp_files:
            try:
                Path(tmp.name).unlink(missing_ok=True)
            except OSError:
                pass

    def __enter__(self) -> VeriFactuClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

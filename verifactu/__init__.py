"""Verifactu Python SDK — AEAT electronic invoicing integration.

Usage::

    from verifactu import VeriFactuClient, Environment, ChainManager
    from verifactu.models import (
        Cabecera, RegistroAlta, RegistroAnulacion,
        IDFactura, SistemaInformatico, Desglose, DetalleDesglose,
        PersonaFisicaJuridicaES, PersonaFisicaJuridica,
    )
    from verifactu.models.enums import TipoFactura, CalificacionOperacion, ClaveRegimen

    chain = ChainManager()
    client = VeriFactuClient(
        environment=Environment.SANDBOX,
        cert_path="cert.pem",
        key_path="key.pem",
    )

    alta = RegistroAlta(...)
    chain.link_alta(alta)

    cabecera = Cabecera(obligado_emision=PersonaFisicaJuridicaES(...))
    response = client.submit(cabecera, [alta])
"""

from verifactu.chain import ChainManager
from verifactu.client import VeriFactuClient
from verifactu.config import CertificateType, Environment
from verifactu.hash import calculate_hash_alta, calculate_hash_anulacion
from verifactu.qr import build_qr_url, build_qr_url_from_alta, generate_qr_image

__all__ = [
    "VeriFactuClient",
    "ChainManager",
    "Environment",
    "CertificateType",
    "calculate_hash_alta",
    "calculate_hash_anulacion",
    "build_qr_url",
    "build_qr_url_from_alta",
    "generate_qr_image",
]

__version__ = "0.1.0"

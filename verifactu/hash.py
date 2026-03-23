"""SHA-256 chained hash calculation per AEAT Verifactu specification.

Implements the hash algorithm as defined in:
"Detalle de las especificaciones técnicas para la generación de la huella o hash" v0.1.2

The hash input is a concatenation of key=value pairs separated by '&',
encoded in UTF-8, then hashed with SHA-256. The output is uppercase hex (64 chars).

AEAT official test vector:
    Input:  IDEmisorFactura=89890001K&NumSerieFactura=12345678/G33&...
    Output: 3C464DAF61ACB827C65FDA19F352A4E3BDC2C640E9E9FC4CC058073F38F12F60
"""

from __future__ import annotations

import hashlib


def _strip_spaces(value: str) -> str:
    """Remove all spaces from a value per AEAT spec."""
    return value.replace(" ", "")


def calculate_hash_alta(
    *,
    id_emisor_factura: str,
    num_serie_factura: str,
    fecha_expedicion_factura: str,
    tipo_factura: str,
    cuota_total: str,
    importe_total: str,
    huella_anterior: str,
    fecha_hora_huso_gen_registro: str,
) -> str:
    """Calculate SHA-256 hash for an Alta (registration) record.

    Args:
        id_emisor_factura: NIF of the issuer.
        num_serie_factura: Invoice series + number.
        fecha_expedicion_factura: Issue date in DD-MM-YYYY format.
        tipo_factura: Invoice type code (F1, F2, R1, etc.).
        cuota_total: Total tax amount.
        importe_total: Total invoice amount.
        huella_anterior: Hash of the previous record in the chain.
            Empty string for the first record.
        fecha_hora_huso_gen_registro: Generation timestamp ISO 8601.

    Returns:
        Uppercase hex SHA-256 hash string (64 characters).
    """
    fields = [
        ("IDEmisorFactura", _strip_spaces(id_emisor_factura)),
        ("NumSerieFactura", _strip_spaces(num_serie_factura)),
        ("FechaExpedicionFactura", _strip_spaces(fecha_expedicion_factura)),
        ("TipoFactura", _strip_spaces(tipo_factura)),
        ("CuotaTotal", _strip_spaces(cuota_total)),
        ("ImporteTotal", _strip_spaces(importe_total)),
        ("Huella", _strip_spaces(huella_anterior)),
        ("FechaHoraHusoGenRegistro", _strip_spaces(fecha_hora_huso_gen_registro)),
    ]
    payload = "&".join(f"{k}={v}" for k, v in fields)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()


def calculate_hash_anulacion(
    *,
    id_emisor_factura_anulada: str,
    num_serie_factura_anulada: str,
    fecha_expedicion_factura_anulada: str,
    huella_anterior: str,
    fecha_hora_huso_gen_registro: str,
) -> str:
    """Calculate SHA-256 hash for an Anulación (cancellation) record.

    Args:
        id_emisor_factura_anulada: NIF of the issuer of the cancelled invoice.
        num_serie_factura_anulada: Series + number of the cancelled invoice.
        fecha_expedicion_factura_anulada: Issue date of the cancelled invoice (DD-MM-YYYY).
        huella_anterior: Hash of the previous record in the chain.
            Empty string for the first record.
        fecha_hora_huso_gen_registro: Generation timestamp ISO 8601.

    Returns:
        Uppercase hex SHA-256 hash string (64 characters).
    """
    fields = [
        ("IDEmisorFacturaAnulada", _strip_spaces(id_emisor_factura_anulada)),
        ("NumSerieFacturaAnulada", _strip_spaces(num_serie_factura_anulada)),
        ("FechaExpedicionFacturaAnulada", _strip_spaces(fecha_expedicion_factura_anulada)),
        ("Huella", _strip_spaces(huella_anterior)),
        ("FechaHoraHusoGenRegistro", _strip_spaces(fecha_hora_huso_gen_registro)),
    ]
    payload = "&".join(f"{k}={v}" for k, v in fields)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()

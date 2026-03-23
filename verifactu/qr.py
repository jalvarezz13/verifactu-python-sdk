"""QR code URL builder per AEAT Verifactu QR specification v0.5.0.

Generates the validation URL that should be encoded into the QR code
on the invoice. The QR must be ISO/IEC 18004:2015, 30-40mm, placed
at the top of the invoice (preferably upper-left corner, first page only).

The URL points to AEAT's validation service, which responds with:
- "Factura encontrada" (found)
- "Factura no encontrada" (not found)
- "Factura no verificable" (not verifiable)
"""

from __future__ import annotations

from urllib.parse import quote, urlencode

from verifactu.config import Environment, get_qr_validation_url


def build_qr_url(
    *,
    nif: str,
    num_serie: str,
    fecha: str,
    importe: str,
    environment: Environment = Environment.PRODUCTION,
) -> str:
    """Build the AEAT QR validation URL.

    Args:
        nif: NIF of the invoice issuer.
        num_serie: Invoice series + number (NumSerieFactura).
        fecha: Issue date in DD-MM-YYYY format.
        importe: Total invoice amount (ImporteTotal).
        environment: Production or sandbox.

    Returns:
        Full URL string ready to be encoded into a QR code.
    """
    base_url = get_qr_validation_url(environment)
    params = urlencode(
        {
            "nif": nif,
            "numserie": num_serie,
            "fecha": fecha,
            "importe": importe,
        },
        quote_via=quote,
    )
    return f"{base_url}?{params}"


def build_qr_url_from_alta(
    alta: object,
    environment: Environment = Environment.PRODUCTION,
) -> str:
    """Build the AEAT QR validation URL from a RegistroAlta model.

    Args:
        alta: A ``RegistroAlta`` instance.
        environment: Production or sandbox.

    Returns:
        Full URL string ready to be encoded into a QR code.
    """
    from verifactu.models.invoice import RegistroAlta

    if not isinstance(alta, RegistroAlta):
        msg = f"Expected RegistroAlta, got {type(alta).__name__}"
        raise TypeError(msg)

    return build_qr_url(
        nif=alta.id_factura.id_emisor_factura,
        num_serie=alta.id_factura.num_serie_factura,
        fecha=alta.id_factura.fecha_expedicion_factura,
        importe=alta.importe_total,
        environment=environment,
    )


def generate_qr_image(
    url: str,
    *,
    box_size: int = 10,
    border: int = 4,
) -> bytes:
    """Generate a QR code PNG image from a URL.

    Requires the optional ``qrcode[pil]`` dependency.
    Install with: ``pip install verifactu[qr]``

    Args:
        url: The URL to encode.
        box_size: Size of each QR module in pixels.
        border: Border size in modules.

    Returns:
        PNG image as bytes.

    Raises:
        ImportError: If ``qrcode`` is not installed.
    """
    try:
        import io

        import qrcode
    except ImportError:
        msg = (
            "QR code generation requires the 'qrcode' package. "
            "Install with: pip install verifactu[qr]"
        )
        raise ImportError(msg) from None

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()

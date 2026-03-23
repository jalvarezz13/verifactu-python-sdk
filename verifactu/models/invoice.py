"""Invoice registration (alta) record model.

Maps to XSD ``RegistroFacturacionAltaType`` from SuministroInformacion.xsd.
This is the primary record type for registering new invoices with AEAT.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from verifactu.models.breakdown import Desglose, DesgloseRectificacion
from verifactu.models.enums import (
    SiNo,
    TerceroODestinatario,
    TipoFactura,
    TipoHuella,
    TipoRectificativa,
)
from verifactu.models.identifiers import (
    Encadenamiento,
    IDFactura,
    IDFacturaAR,
    PersonaFisicaJuridica,
)
from verifactu.models.system import SistemaInformatico


class RegistroAlta(BaseModel):
    """Invoice registration record (Alta).

    Maps to XSD ``RegistroFacturacionAltaType``. Contains all fields needed
    to register a new invoice (or corrective/substitute invoice) with AEAT.
    """

    # --- Identification ---
    id_version: str = "1.0"
    """Schema version (IDVersion). Always '1.0'."""

    id_factura: IDFactura
    """Invoice identifier (IDFactura)."""

    ref_externa: str | None = Field(default=None, max_length=60)
    """External reference for correlation (RefExterna). Optional."""

    nombre_razon_emisor: str = Field(max_length=120)
    """Issuer name (NombreRazonEmisor). Required."""

    # --- Correction/subsanation flags ---
    subsanacion: SiNo | None = None
    """Set to 'S' for amendment submissions (Subsanacion)."""

    rechazo_previo: str | None = Field(default=None, pattern=r"^[NSX]$")
    """Previous rejection flag: N=no, S=yes, X=record not in AEAT."""

    # --- Invoice type ---
    tipo_factura: TipoFactura
    """Invoice type code (F1, F2, F3, R1-R5)."""

    tipo_rectificativa: TipoRectificativa | None = None
    """Corrective invoice method (S=substitutive, I=incremental). Only for R1-R5."""

    # --- Rectified/substituted invoices ---
    facturas_rectificadas: list[IDFacturaAR] | None = None
    """Rectified invoices (up to 1000). Only for corrective invoices."""

    facturas_sustituidas: list[IDFacturaAR] | None = None
    """Substituted invoices (up to 1000). Only for substitute invoices."""

    importe_rectificacion: DesgloseRectificacion | None = None
    """Rectification amounts. Only for substitutive corrective invoices."""

    # --- Operation details ---
    fecha_operacion: str | None = Field(default=None, min_length=10, max_length=10)
    """Operation date DD-MM-YYYY (if different from issue date). Optional."""

    descripcion_operacion: str = Field(max_length=500)
    """Operation description (DescripcionOperacion). Required."""

    # --- Special flags ---
    factura_simplificada_art7273: SiNo | None = None
    """Qualified simplified invoice (Art. 7.2/7.3 RD 1619/2012)."""

    factura_sin_identif_destinatario_art61d: SiNo | None = None
    """Invoice without recipient identification (Art. 6.1.d)."""

    macrodato: SiNo | None = None
    """Invoice amount exceeds threshold (Macrodato)."""

    emitida_por_tercero_o_destinatario: TerceroODestinatario | None = None
    """Issued by third party (T) or recipient (D)."""

    tercero: PersonaFisicaJuridica | None = None
    """Third party who issued the invoice. Optional."""

    # --- Recipients ---
    destinatarios: list[PersonaFisicaJuridica] | None = None
    """Invoice recipients (up to 1000). Optional for simplified invoices."""

    cupon: SiNo | None = None
    """Coupon/discount reduction (Cupon)."""

    # --- Tax breakdown ---
    desglose: Desglose
    """Tax breakdown (1-12 detail lines). Required."""

    cuota_total: str = Field(pattern=r"^(\+|-)?\d{1,12}(\.\d{0,2})?$")
    """Total tax amount (CuotaTotal)."""

    importe_total: str = Field(pattern=r"^(\+|-)?\d{1,12}(\.\d{0,2})?$")
    """Total invoice amount (ImporteTotal)."""

    # --- Chain and system info ---
    encadenamiento: Encadenamiento
    """Chain link to previous record."""

    sistema_informatico: SistemaInformatico
    """Invoicing system identification."""

    fecha_hora_huso_gen_registro: str
    """Record generation timestamp ISO 8601: YYYY-MM-DDTHH:MM:SS+HH:00."""

    # --- Hash ---
    num_registro_acuerdo_facturacion: str | None = Field(default=None, max_length=15)
    """Billing agreement registration number. Optional."""

    id_acuerdo_sistema_informatico: str | None = Field(default=None, max_length=16)
    """IT system agreement identifier. Optional."""

    tipo_huella: TipoHuella = TipoHuella.SHA256
    """Hash algorithm type. Always '01' (SHA-256)."""

    huella: str = Field(max_length=64)
    """SHA-256 hash of this record (uppercase hex, 64 chars)."""
